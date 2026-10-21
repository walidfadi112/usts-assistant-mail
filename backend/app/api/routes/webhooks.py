import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])
log = logging.getLogger("usts.webhooks")


def process_pending(limit: int = 10) -> dict:
    from app.db.session import SessionLocal
    from app.models.email import Email
    from app.services.classification_service import classify_email

    db = SessionLocal()
    try:
        pending = db.query(Email).filter(Email.category == "autre").limit(limit).all()
        ok, failed = 0, 0
        for e in pending:
            try:
                classify_email(e.id)
                ok += 1
            except Exception:
                failed += 1
        return {"processed": ok, "failed": failed}
    finally:
        db.close()


@router.post("/n8n")
async def n8n_webhook(request: Request):
    if request.headers.get("X-Webhook-Secret") != settings.webhook_secret:
        return JSONResponse(status_code=401, content={"detail": "Secret manquant ou invalide"})
    try:
        body = await request.json()
    except Exception:
        body = {}
    if body.get("action") == "ping":
        return {"status": "ok", "mode": "ping"}
    result = process_pending()
    return {"status": "ok", "result": result}


@router.post("/n8n/error")
async def n8n_error(request: Request):
    if request.headers.get("X-Webhook-Secret") != settings.webhook_secret:
        return JSONResponse(status_code=401, content={"detail": "Secret manquant ou invalide"})
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    log.error("Erreur n8n recue: %s", payload)
    return {"status": "logged"}
