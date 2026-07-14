import asyncio
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..database import SessionLocal

# Maps a threshold metric_type to the matching column on a metric reading.
# "disk" is space used; "disk_io" is drive busy time (Task Manager style).
METRIC_FIELDS = {
    "cpu": "cpu_percent",
    "memory": "memory_percent",
    "disk": "disk_percent",
    "disk_io": "disk_io_percent",
}


def _open_alerts(db: Session, node_id: int, reason_prefix: str) -> list:
    """Alerts for this node+condition whose episode has not ended yet.

    An alert row represents one episode of a condition (e.g. one disk-usage
    excursion above the threshold). The episode is open while cleared_at is
    NULL, regardless of whether a user acknowledged it — acknowledging is a
    human "seen it", clearing is the metric actually recovering.
    Conditions are identified by the start of trigger_reason (e.g. "cpu ").
    """
    return (
        db.query(models.Alert)
        .filter(
            models.Alert.node_id == node_id,
            models.Alert.cleared_at.is_(None),
            models.Alert.trigger_reason.like(reason_prefix + "%"),
        )
        .all()
    )


def _raise_alert(
    db: Session,
    node_id: int,
    metric_type: str,
    severity: str,
    value: float,
    limit: float,
) -> None:
    open_alerts = _open_alerts(db, node_id, metric_type + " ")
    # Suppress while the episode is open. The one exception: a warning episode
    # escalating to critical still raises one new critical alert.
    if severity == "warning" and open_alerts:
        return
    if severity == "critical" and any(a.severity == "critical" for a in open_alerts):
        return
    reason = f"{metric_type} {value:.1f}% >= {severity} {limit:g}%"
    db.add(models.Alert(node_id=node_id, severity=severity, trigger_reason=reason))


def _clear_alerts(db: Session, node_id: int, reason_prefix: str) -> None:
    """End the episode: the condition is no longer true, so a future crossing
    is a new event and may alert again."""
    for alert in _open_alerts(db, node_id, reason_prefix):
        alert.cleared_at = datetime.now()


def evaluate_metric(db: Session, node: models.Node, metric: models.Metric) -> None:
    """Check one reading against the thresholds and update node status + alerts.

    Does not commit; the caller (store_metric) owns the transaction.
    """
    # The node just reported, so any offline episode is over.
    _clear_alerts(db, node.id, "offline")

    thresholds = {t.metric_type: t for t in db.query(models.Threshold).all()}
    crossed = False

    for metric_type, field in METRIC_FIELDS.items():
        threshold = thresholds.get(metric_type)
        if threshold is None:
            continue
        value = getattr(metric, field)
        if value >= threshold.critical_value:
            crossed = True
            _raise_alert(db, node.id, metric_type, "critical", value, threshold.critical_value)
        elif value >= threshold.warning_value:
            crossed = True
            _raise_alert(db, node.id, metric_type, "warning", value, threshold.warning_value)
        else:
            # Back under the warning limit: this episode is finished.
            _clear_alerts(db, node.id, metric_type + " ")

    # A node that just reported is online; a crossed threshold downgrades it to
    # warning. Offline is handled separately by the background monitor.
    node.status = "warning" if crossed else "online"


def mark_offline_nodes(db: Session) -> int:
    """Flag nodes that have missed check-ins as offline and raise an alert.

    Runs on a timer so alerts fire even when no one has the dashboard open.
    Returns how many nodes were newly marked offline.
    """
    cutoff = datetime.now() - timedelta(seconds=settings.offline_timeout_seconds)
    stale_nodes = (
        db.query(models.Node)
        .filter(
            models.Node.last_seen.isnot(None),
            models.Node.last_seen < cutoff,
            models.Node.status != "offline",
        )
        .all()
    )

    for node in stale_nodes:
        node.status = "offline"
        if not _open_alerts(db, node.id, "offline"):
            reason = f"offline: no check-in for over {settings.offline_timeout_seconds}s"
            db.add(models.Alert(node_id=node.id, severity="critical", trigger_reason=reason))

    if stale_nodes:
        db.commit()
    return len(stale_nodes)


async def offline_monitor_loop() -> None:
    """Background task started in the app lifespan to run offline checks on a timer."""
    interval = max(settings.offline_timeout_seconds // 2, 5)
    while True:
        await asyncio.sleep(interval)
        db = SessionLocal()
        try:
            count = mark_offline_nodes(db)
            if count:
                print(f"[offline-monitor] marked {count} node(s) offline")
        except Exception as exc:  # keep the loop alive across transient DB errors
            print(f"[offline-monitor] check failed: {exc}")
        finally:
            db.close()
