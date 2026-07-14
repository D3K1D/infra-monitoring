from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(
    prefix="/api", tags=["nodes"], dependencies=[Depends(get_current_user)]
)


@router.get("/nodes", response_model=List[schemas.NodeOut])
def list_nodes(db: Session = Depends(get_db)):
    """Return all monitored nodes with their latest disk-space reading."""
    nodes = db.query(models.Node).order_by(models.Node.hostname).all()
    result = []
    for node in nodes:
        latest = (
            db.query(models.Metric)
            .filter(models.Metric.node_id == node.id)
            .order_by(models.Metric.id.desc())
            .first()
        )
        out = schemas.NodeOut.model_validate(node)
        out.disk_percent = latest.disk_percent if latest else None
        result.append(out)
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
    out = schemas.NodeOut.model_validate(node)
    out.disk_percent = latest.disk_percent if latest else None
    return out


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
