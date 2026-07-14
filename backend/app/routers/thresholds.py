from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, require_admin

router = APIRouter(
    prefix="/api", tags=["thresholds"], dependencies=[Depends(get_current_user)]
)

VALID_METRIC_TYPES = ("cpu", "memory", "disk")


@router.get("/thresholds", response_model=List[schemas.ThresholdOut])
def list_thresholds(db: Session = Depends(get_db)):
    """Return the configured thresholds for each metric type."""
    return db.query(models.Threshold).order_by(models.Threshold.metric_type).all()


@router.put(
    "/thresholds/{metric_type}",
    response_model=schemas.ThresholdOut,
    dependencies=[Depends(require_admin)],
)
def update_threshold(
    metric_type: str,
    payload: schemas.ThresholdUpdate,
    db: Session = Depends(get_db),
):
    """Update one metric's warning/critical limits. Admin only."""
    if metric_type not in VALID_METRIC_TYPES:
        raise HTTPException(status_code=404, detail="Unknown metric type")
    if payload.warning_value > payload.critical_value:
        raise HTTPException(
            status_code=400, detail="warning_value cannot exceed critical_value"
        )

    threshold = (
        db.query(models.Threshold)
        .filter(models.Threshold.metric_type == metric_type)
        .first()
    )
    if threshold is None:
        raise HTTPException(status_code=404, detail="Threshold not configured")

    threshold.warning_value = payload.warning_value
    threshold.critical_value = payload.critical_value
    db.commit()
    db.refresh(threshold)
    return threshold
