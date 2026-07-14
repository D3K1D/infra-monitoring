from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..services import metric_service

router = APIRouter(
    prefix="/api", tags=["summary"], dependencies=[Depends(get_current_user)]
)


@router.get("/summary", response_model=schemas.SummaryOut)
def get_summary(
    minutes: int = Query(1440, ge=1, le=10080),
    db: Session = Depends(get_db),
):
    """Fleet totals for the dashboard cards. Uptime is check-in coverage:
    readings received vs. expected at the agent reporting interval."""
    nodes = db.query(models.Node).all()
    counts = {"online": 0, "warning": 0, "offline": 0}
    for node in nodes:
        counts[node.status] += 1

    active_alerts = (
        db.query(models.Alert).filter(models.Alert.status == "active").count()
    )

    return schemas.SummaryOut(
        total_nodes=len(nodes),
        online=counts["online"],
        warning=counts["warning"],
        offline=counts["offline"],
        active_alerts=active_alerts,
        uptime_percent=metric_service.uptime_percent(db, minutes),
        window_minutes=minutes,
    )
