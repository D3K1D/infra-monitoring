from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import schemas
from ..database import get_db
from ..deps import require_agent_key
from ..services import metric_service

# Ingest is authenticated by the shared agent key, not a user session.
router = APIRouter(
    prefix="/api", tags=["metrics"], dependencies=[Depends(require_agent_key)]
)


@router.post("/metrics", status_code=status.HTTP_201_CREATED)
def ingest_metric(payload: schemas.MetricIn, db: Session = Depends(get_db)):
    """Receive one reading from an agent, register/refresh its node, and store it."""
    metric = metric_service.store_metric(db, payload)
    return {"status": "stored", "metric_id": metric.id, "node_id": metric.node_id}
