from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["alerts"])


def _to_out(alert: models.Alert) -> schemas.AlertOut:
    return schemas.AlertOut(
        id=alert.id,
        node_id=alert.node_id,
        hostname=alert.node.hostname,
        severity=alert.severity,
        trigger_reason=alert.trigger_reason,
        status=alert.status,
        created_at=alert.created_at,
        acknowledged_at=alert.acknowledged_at,
        acknowledged_by=alert.acknowledged_by,
    )


@router.get("/alerts", response_model=List[schemas.AlertOut])
def list_alerts(
    status: Optional[str] = Query(None, pattern="^(active|acknowledged)$"),
    db: Session = Depends(get_db),
):
    """List alerts newest first, optionally filtered by status."""
    query = db.query(models.Alert).join(models.Node)
    if status is not None:
        query = query.filter(models.Alert.status == status)
    alerts = query.order_by(models.Alert.created_at.desc()).all()
    return [_to_out(a) for a in alerts]


@router.post("/alerts/{alert_id}/acknowledge", response_model=schemas.AlertOut)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert acknowledged. Idempotent if it is already acknowledged."""
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status != "acknowledged":
        alert.status = "acknowledged"
        alert.acknowledged_at = datetime.now()
        # acknowledged_by is filled with the logged-in user once auth is added.
        db.commit()
        db.refresh(alert)
    return _to_out(alert)
