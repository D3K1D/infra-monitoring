import asyncio
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..database import SessionLocal

# Maps a threshold metric_type to the matching column on a metric reading.
METRIC_FIELDS = {
    "cpu": "cpu_percent",
    "memory": "memory_percent",
    "disk": "disk_percent",
}


def _has_active_alert(db: Session, node_id: int, reason_prefix: str) -> bool:
    """True if this node already has an unacknowledged alert for the same condition.

    Dedup keeps a single hot reading from raising a new alert on every check-in.
    Conditions are identified by the start of trigger_reason (e.g. "cpu ").
    """
    return (
        db.query(models.Alert)
        .filter(
            models.Alert.node_id == node_id,
            models.Alert.status == "active",
            models.Alert.trigger_reason.like(reason_prefix + "%"),
        )
        .first()
        is not None
    )


def _raise_alert(
    db: Session,
    node_id: int,
    metric_type: str,
    severity: str,
    value: float,
    limit: float,
) -> None:
    if _has_active_alert(db, node_id, metric_type + " "):
        return
    reason = f"{metric_type} {value:.1f}% >= {severity} {limit:g}%"
    db.add(models.Alert(node_id=node_id, severity=severity, trigger_reason=reason))


def evaluate_metric(db: Session, node: models.Node, metric: models.Metric) -> None:
    """Check one reading against the thresholds and update node status + alerts.

    Does not commit; the caller (store_metric) owns the transaction.
    """
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
        if not _has_active_alert(db, node.id, "offline"):
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
