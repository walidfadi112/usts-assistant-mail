
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.services.sync_service import sync_gmail

router = APIRouter(prefix="/gmail", tags=["Gmail"])


@router.post("/sync")
def synchronize_gmail(
    max_results: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return sync_gmail(db, max_results=max_results)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Synchronisation Gmail échouée : {str(exc)[:500]}",
        ) from exc
