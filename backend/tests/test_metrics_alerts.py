from datetime import datetime, timedelta

from app import models
from app.services import alert_service
from conftest import TEST_AGENT_KEY


def metric_payload(**overrides):
    payload = {
        "hostname": "test-node",
        "ip_address": "192.0.2.10",
        "os": "Test OS",
        "location": "Lab Rack 1",
        "cpu_percent": 20,
        "memory_percent": 30,
        "disk_percent": 40,
        "disk_io_percent": 5,
    }
    payload.update(overrides)
    return payload


def post_metric(client, **overrides):
    return client.post(
        "/api/metrics",
        json=metric_payload(**overrides),
        headers={"X-API-Key": TEST_AGENT_KEY},
    )


def register_and_login(client):
    client.post(
        "/api/auth/register",
        json={"username": "operator", "password": "password123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "password123"},
    )
    assert response.status_code == 200


def test_metric_ingestion_requires_key_and_upserts_one_node(client, db):
    unauthorized = client.post("/api/metrics", json=metric_payload())
    assert unauthorized.status_code == 401

    first = post_metric(client)
    second = post_metric(client, ip_address="192.0.2.11", cpu_percent=25)
    assert first.status_code == 201
    assert second.status_code == 201

    db.expire_all()
    assert db.query(models.Node).count() == 1
    assert db.query(models.Metric).count() == 2
    node = db.query(models.Node).one()
    assert node.ip_address == "192.0.2.11"
    assert node.status == "online"


def test_warning_reasons_follow_live_metrics_not_alert_acknowledgment(client):
    register_and_login(client)

    assert post_metric(client, cpu_percent=80, disk_percent=92).status_code == 201
    node = client.get("/api/nodes").json()[0]
    assert node["status"] == "warning"
    assert node["warning_reasons"] == [
        "CPU usage is high: 80.0% (warning threshold: 75%).",
        "Disk space is almost full: 92.0% used (critical threshold: 90%).",
    ]

    # Human review of the alert must not hide a condition that is still true.
    for alert in client.get("/api/alerts").json():
        assert client.post(f"/api/alerts/{alert['id']}/acknowledge").status_code == 200
    assert client.get("/api/nodes").json()[0]["warning_reasons"] == node["warning_reasons"]

    # The explanation disappears only after the latest metrics recover.
    assert post_metric(client).status_code == 201
    recovered = client.get("/api/nodes").json()[0]
    assert recovered["status"] == "online"
    assert recovered["warning_reasons"] == []


def test_alert_episode_acknowledgment_escalation_recovery_and_reopening(client, db):
    register_and_login(client)

    assert post_metric(client, cpu_percent=80).status_code == 201
    first_alerts = client.get("/api/alerts").json()
    assert len(first_alerts) == 1
    assert first_alerts[0]["severity"] == "warning"

    alert_id = first_alerts[0]["id"]
    acknowledged = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert acknowledged.status_code == 200
    assert acknowledged.json()["acknowledged_by"] is not None

    # Remaining above warning does not create another warning episode.
    assert post_metric(client, cpu_percent=82).status_code == 201
    assert len(client.get("/api/alerts").json()) == 1

    # Escalation creates one critical alert while the warning episode stays open.
    assert post_metric(client, cpu_percent=90).status_code == 201
    escalated = client.get("/api/alerts").json()
    assert len(escalated) == 2
    assert {alert["severity"] for alert in escalated} == {"warning", "critical"}

    # Recovery closes both alerts without changing the human acknowledgment state.
    assert post_metric(client, cpu_percent=20).status_code == 201
    db.expire_all()
    alerts = db.query(models.Alert).all()
    assert all(alert.cleared_at is not None for alert in alerts)
    assert db.query(models.Node).one().status == "online"

    # A later crossing is a new episode and may alert again.
    assert post_metric(client, cpu_percent=80).status_code == 201
    assert len(client.get("/api/alerts").json()) == 3


def test_alert_recovery_margin_prevents_threshold_flapping(client, db):
    assert post_metric(client, memory_percent=80.2).status_code == 201
    assert db.query(models.Alert).count() == 1

    # A small dip below the 80% warning line changes the live node state, but
    # does not end the alert episode until memory reaches the 78% recovery line.
    assert post_metric(client, memory_percent=79.8).status_code == 201
    db.expire_all()
    alert = db.query(models.Alert).one()
    assert alert.cleared_at is None
    assert db.query(models.Node).one().status == "online"

    # Crossing above warning again reuses the still-open episode.
    assert post_metric(client, memory_percent=80.3).status_code == 201
    assert db.query(models.Alert).count() == 1

    assert post_metric(client, memory_percent=78).status_code == 201
    db.expire_all()
    assert db.query(models.Alert).one().cleared_at is not None

    # A crossing after a full recovery is a genuinely new episode.
    assert post_metric(client, memory_percent=80.4).status_code == 201
    assert db.query(models.Alert).count() == 2


def test_offline_alert_is_deduplicated_and_clears_on_check_in(client, db):
    assert post_metric(client).status_code == 201

    db.expire_all()
    node = db.query(models.Node).one()
    node.last_seen = datetime.now() - timedelta(minutes=5)
    node.status = "online"
    db.commit()

    assert alert_service.mark_offline_nodes(db) == 1
    assert alert_service.mark_offline_nodes(db) == 0
    assert db.query(models.Alert).count() == 1
    offline_alert = db.query(models.Alert).one()
    assert offline_alert.severity == "critical"
    assert offline_alert.cleared_at is None

    assert post_metric(client).status_code == 201
    db.expire_all()
    assert db.query(models.Node).one().status == "online"
    assert db.query(models.Alert).one().cleared_at is not None
