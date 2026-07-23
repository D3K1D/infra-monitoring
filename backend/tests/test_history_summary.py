from datetime import datetime, timedelta

from app import models
from app.services import metric_service


def register_and_login(client):
    client.post(
        "/api/auth/register",
        json={"username": "viewer", "password": "password123"},
    )
    response = client.post(
        "/api/auth/login",
        json={"username": "viewer", "password": "password123"},
    )
    assert response.status_code == 200


def add_metric(db, node_id, recorded_at, cpu_percent=20):
    db.add(
        models.Metric(
            node_id=node_id,
            cpu_percent=cpu_percent,
            memory_percent=30,
            disk_percent=40,
            disk_io_percent=5,
            recorded_at=recorded_at,
        )
    )


def test_metric_history_filters_orders_and_returns_404(client, db):
    register_and_login(client)
    now = datetime.now()
    node = models.Node(
        hostname="history-node",
        status="online",
        last_seen=now,
        created_at=now - timedelta(hours=2),
    )
    db.add(node)
    db.flush()
    add_metric(db, node.id, now - timedelta(minutes=70), 10)
    add_metric(db, node.id, now - timedelta(minutes=50), 20)
    add_metric(db, node.id, now - timedelta(minutes=20), 30)
    add_metric(db, node.id, now - timedelta(minutes=5), 40)
    db.commit()

    response = client.get(f"/api/nodes/{node.id}/metrics?minutes=60")
    assert response.status_code == 200
    rows = response.json()
    assert [row["cpu_percent"] for row in rows] == [20, 30, 40]
    assert all(
        datetime.fromisoformat(row["recorded_at"]).utcoffset() is not None
        for row in rows
    )

    node_response = client.get(f"/api/nodes/{node.id}")
    assert node_response.status_code == 200
    last_seen = datetime.fromisoformat(node_response.json()["last_seen"])
    assert last_seen.utcoffset() is not None
    assert client.get("/api/nodes/9999/metrics?minutes=60").status_code == 404


def test_summary_returns_all_node_and_alert_counts(client, db):
    register_and_login(client)
    now = datetime.now()
    nodes = [
        models.Node(hostname="online-node", status="online", created_at=now),
        models.Node(hostname="warning-node", status="warning", created_at=now),
        models.Node(hostname="offline-node", status="offline", created_at=now),
    ]
    db.add_all(nodes)
    db.flush()
    db.add_all(
        [
            models.Alert(
                node_id=nodes[0].id,
                severity="warning",
                trigger_reason="cpu test",
                status="active",
            ),
            models.Alert(
                node_id=nodes[1].id,
                severity="warning",
                trigger_reason="memory test",
                status="active",
                cleared_at=now,
            ),
            models.Alert(
                node_id=nodes[2].id,
                severity="critical",
                trigger_reason="offline test",
                status="acknowledged",
            ),
        ]
    )
    db.commit()

    response = client.get("/api/summary?minutes=60")
    assert response.status_code == 200
    summary = response.json()
    assert summary["total_nodes"] == 3
    assert summary["online"] == 1
    assert summary["warning"] == 1
    assert summary["offline"] == 1
    assert summary["active_alerts"] == 2
    assert summary["ongoing_alerts"] == 1
    assert summary["recovered_unacknowledged"] == 1
    assert summary["window_minutes"] == 60


def test_uptime_is_full_then_half_for_a_full_window(db, monkeypatch):
    fixed_now = datetime(2026, 7, 22, 12, 0, 0)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(metric_service, "datetime", FrozenDatetime)
    node = models.Node(
        hostname="uptime-node",
        status="online",
        created_at=fixed_now - timedelta(seconds=60),
    )
    db.add(node)
    db.flush()
    for seconds_ago in (60, 45, 30, 15):
        add_metric(db, node.id, fixed_now - timedelta(seconds=seconds_ago))
    db.commit()

    assert metric_service.uptime_percent(db, 1) == 100.0

    db.query(models.Metric).delete()
    for seconds_ago in (45, 15):
        add_metric(db, node.id, fixed_now - timedelta(seconds=seconds_ago))
    db.commit()
    assert metric_service.uptime_percent(db, 1) == 50.0


def test_new_node_is_only_expected_to_report_since_creation(db, monkeypatch):
    fixed_now = datetime(2026, 7, 22, 12, 0, 0)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(metric_service, "datetime", FrozenDatetime)
    node = models.Node(
        hostname="new-node",
        status="online",
        created_at=fixed_now - timedelta(seconds=30),
    )
    db.add(node)
    db.flush()
    add_metric(db, node.id, fixed_now - timedelta(seconds=30))
    add_metric(db, node.id, fixed_now - timedelta(seconds=15))
    db.commit()

    assert metric_service.uptime_percent(db, 60) == 100.0
