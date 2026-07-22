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

    active_query = db.query(models.Alert).filter(models.Alert.status == "active")
    active_alerts = active_query.count()
    ongoing_alerts = active_query.filter(models.Alert.cleared_at.is_(None)).count()
    recovered_unacknowledged = active_query.filter(
        models.Alert.cleared_at.isnot(None)
    ).count()

    return schemas.SummaryOut(
        total_nodes=len(nodes),
        online=counts["online"],
        warning=counts["warning"],
        offline=counts["offline"],
        active_alerts=active_alerts,
        ongoing_alerts=ongoing_alerts,
        recovered_unacknowledged=recovered_unacknowledged,
        uptime_percent=metric_service.uptime_percent(db, minutes),
        window_minutes=minutes,
    )
