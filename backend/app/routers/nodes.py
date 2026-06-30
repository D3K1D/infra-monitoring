from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["nodes"])


@router.get("/nodes", response_model=List[schemas.NodeOut])
def list_nodes(db: Session = Depends(get_db)):
    """Return all monitored nodes for the dashboard."""
    return db.query(models.Node).order_by(models.Node.hostname).all()
