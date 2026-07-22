from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..services.alert_service import METRIC_FIELDS

router = APIRouter(
    prefix="/api", tags=["nodes"], dependencies=[Depends(get_current_user)]
)

METRIC_DESCRIPTIONS = {
    "cpu": ("CPU usage", "high", ""),
    "memory": ("Memory usage", "high", ""),
    "disk": ("Disk space", "almost full", " used"),
    "disk_io": ("Disk activity", "high", ""),
}


def _warning_reasons(metric, thresholds: dict) -> list[str]:
    """Describe every condition keeping the node in its warning state."""
    reasons = []
    for metric_type, field in METRIC_FIELDS.items():
        threshold = thresholds.get(metric_type)
        if threshold is None:
            continue

        value = getattr(metric, field)
        if value >= threshold.critical_value:
            severity = "critical"
            limit = threshold.critical_value
        elif value >= threshold.warning_value:
            severity = "warning"
            limit = threshold.warning_value
        else:
            continue

        label, condition, value_suffix = METRIC_DESCRIPTIONS[metric_type]
        reasons.append(
            f"{label} is {condition}: {value:.1f}%{value_suffix} "
            f"({severity} threshold: {limit:g}%)."
        )
    return reasons


def _node_out(node, latest, thresholds: dict) -> schemas.NodeOut:
    out = schemas.NodeOut.model_validate(node)
    out.disk_percent = latest.disk_percent if latest else None
    if node.status == "warning" and latest is not None:
        out.warning_reasons = _warning_reasons(latest, thresholds)
    return out


@router.get("/nodes", response_model=List[schemas.NodeOut])
def list_nodes(db: Session = Depends(get_db)):
    """Return all monitored nodes with their latest disk-space reading."""
    nodes = db.query(models.Node).order_by(models.Node.hostname).all()
    thresholds = {t.metric_type: t for t in db.query(models.Threshold).all()}
    result = []
    for node in nodes:
        latest = (
            db.query(models.Metric)
            .filter(models.Metric.node_id == node.id)
            .order_by(models.Metric.id.desc())
            .first()
        )
        result.append(_node_out(node, latest, thresholds))
    return result


@router.get("/nodes/{node_id}", response_model=schemas.NodeOut)
def get_node(node_id: int, db: Session = Depends(get_db)):
    """Return one node, used by the node detail page header."""
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")
    latest = (
        db.query(models.Metric)
        .filter(models.Metric.node_id == node.id)
        .order_by(models.Metric.id.desc())
        .first()
    )
    thresholds = {t.metric_type: t for t in db.query(models.Threshold).all()}
    return _node_out(node, latest, thresholds)


@router.get("/nodes/{node_id}/metrics", response_model=List[schemas.MetricOut])
def node_metrics(
    node_id: int,
    minutes: int = Query(60, ge=1, le=1440),
    db: Session = Depends(get_db),
):
    """Metric history for one node, oldest first, for the Chart.js charts."""
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if node is None:
        raise HTTPException(status_code=404, detail="Node not found")

    since = datetime.now() - timedelta(minutes=minutes)
    return (
        db.query(models.Metric)
        .filter(models.Metric.node_id == node_id, models.Metric.recorded_at >= since)
        .order_by(models.Metric.recorded_at.asc())
        .all()
    )
