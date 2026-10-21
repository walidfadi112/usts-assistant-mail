from fastapi import FastAPI
from app.api.routes.gmail import router as gmail_router

import app.models
from app.api.routes.auth import router as auth_router
from app.api.routes.emails import router as emails_router
from app.db.session import Base, engine

app = FastAPI(
    title="USTS Assistant Mail",
    description="API de gestion des emails, brouillons et réponses.",
    version="0.1.0",
)

app.include_router(auth_router)
app.include_router(emails_router)
app.include_router(gmail_router)
from app.api.routes.summary import router as summary_router
app.include_router(summary_router)
from app.api.routes.replies import router as replies_router
app.include_router(replies_router)

from app.api.routes.events import router as events_router
from app.api.routes.webhooks import router as webhooks_router
app.include_router(events_router)
app.include_router(webhooks_router)



@app.on_event("startup")
def initialize_database():
    Base.metadata.create_all(bind=engine)


@app.get("/", tags=["System"])
def root():
    return {
        "message": "USTS Assistant Mail API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "usts-mail-assistant"}
