from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.email import Email
from app.services.draft_service import generate_draft

router = APIRouter(tags=["Replies"])

ALLOWED_TONES = ("formal", "neutral", "short")


def get_email(db: Session, email_id: int) -> Email:
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email " + str(email_id) + " introuvable")
    return email


@router.post("/emails/{email_id}/draft")
def create_draft(email_id: int, tone: str = Query(default="neutral")):
    if tone not in ALLOWED_TONES:
        raise HTTPException(
            status_code=422,
            detail="Ton invalide. Choix: " + ", ".join(ALLOWED_TONES),
        )
    db = SessionLocal()
    try:
        email = get_email(db, email_id)
        try:
            draft = generate_draft(email.subject or "", email.body or "", email.sender, tone)
        except Exception:
            raise HTTPException(status_code=502, detail="Echec de la generation du brouillon IA")
        return {"email_id": email_id, "tone": tone, "draft": draft}
    finally:
        db.close()


@router.post("/emails/{email_id}/send")
def send_reply(email_id: int):
    db = SessionLocal()
    try:
        email = get_email(db, email_id)
        if email.status == "envoy?":
            return {"email_id": email_id, "sent": False, "already_sent": True}
        email.status = "envoy?"
        db.commit()
        return {"email_id": email_id, "sent": True, "already_sent": False}
    finally:
        db.close()
