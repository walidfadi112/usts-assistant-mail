from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.routes.auth import get_current_user
from app.schemas.summary import DailySummaryResponse
from app.services.email_service import DailySummaryService

router = APIRouter(prefix="/summary", tags=["Summary"])


@router.get("/today", response_model=DailySummaryResponse)
def get_daily_summary(
    target_date: date | None = Query(default=None, alias="date"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return DailySummaryService(db).build(target_date or date.today())
