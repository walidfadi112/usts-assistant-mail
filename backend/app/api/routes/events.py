import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.email import Email

router = APIRouter(prefix="/events", tags=["Events"])

POLL_SECONDS = 4


def _authenticate(token: str) -> int:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        if not subject:
            raise unauthorized
        return int(subject)
    except HTTPException:
        raise
    except Exception:
        raise unauthorized


@router.get("")
def event_stream(
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    _authenticate(token)

    async def stream():
        latest = db.scalar(select(Email.id).order_by(Email.id.desc()))
        last_id = latest or 0
        yield "event: ready\ndata: {}\n\n"

        while True:
            await asyncio.sleep(POLL_SECONDS)
            new_emails = db.scalars(
                select(Email).where(Email.id > last_id).order_by(Email.id.asc())
            ).all()
            for email in new_emails:
                last_id = email.id
                payload = {
                    "id": email.id,
                    "sender": email.sender,
                    "subject": email.subject,
                    "category": email.category,
                    "priority": email.priority,
                }
                yield (
                    "event: new_email\ndata: "
                    + json.dumps(payload, ensure_ascii=False)
                    + "\n\n"
                )

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )