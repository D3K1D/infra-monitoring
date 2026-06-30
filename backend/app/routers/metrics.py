from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..services import metric_service

router = APIRouter(prefix="/api", tags=["metrics"])


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def ingest_metric(payload: schemas.MetricIn, db: Session = Depends(get_db)):
    """Receive one reading from an agent, register/refresh its node, and store it."""
    metric = metric_service.store_metric(db, payload)
    return {"status": "stored", "metric_id": metric.id, "node_id": metric.node_id}
