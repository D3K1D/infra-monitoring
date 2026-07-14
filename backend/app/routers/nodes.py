from typing import List

from fastapi import APIRouter, Depends
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
