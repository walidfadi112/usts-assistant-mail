
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.db.session import get_db
from app.models.email import Email
from app.models.user import User
from app.services.classification_service import ClassificationService

router = APIRouter(prefix="/emails", tags=["Emails"])

Category = Literal[
    "client", "facture", "rendez-vous",
    "newsletter", "spam probable", "autre",
]

EmailStatus = Literal[
    "nouveau", "en_cours", "traite", "archive",
    "à traiter", "à vérifier",
]


class EmailCreate(BaseModel):
    gmail_message_id: str = Field(min_length=1, max_length=255)
    sender: str = Field(min_length=1, max_length=320)
    recipients: str = ""
    subject: str = ""
    body: str = ""
    received_at: datetime | None = None
    category: Category = "autre"
    priority: int = Field(default=2, ge=1, le=3)
    summary: str | None = None
    expected_action: str | None = None
    status: EmailStatus = "nouveau"


class EmailUpdate(BaseModel):
    category: Category | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    status: EmailStatus | None = None
    summary: str | None = None
    expected_action: str | None = None


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    gmail_message_id: str
    thread_id: int | None = None
    sender: str
    recipients: str
    subject: str
    body: str
    received_at: datetime | None = None
    category: str | None = None
    priority: int | None = None
    summary: str | None = None
    expected_action: str | None = None
    status: str | None = None


@router.get("", response_model=dict)
def list_emails(
    search: str | None = Query(default=None, max_length=200),
    subject: str | None = Query(default=None, max_length=200),
    body: str | None = Query(default=None, max_length=500),
    sender: str | None = Query(default=None, max_length=320),
    category: Category | None = None,
    priority: int | None = Query(default=None, ge=1, le=3),
    email_status: EmailStatus | None = Query(default=None, alias="status"),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from doit être antérieure à date_to.",
        )

    query = select(Email)

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Email.sender.ilike(term),
                Email.subject.ilike(term),
                Email.body.ilike(term),
            )
        )

    if subject and subject.strip():
        query = query.where(
            Email.subject.ilike(f"%{subject.strip()}%")
        )

    if body and body.strip():
        query = query.where(
            Email.body.ilike(f"%{body.strip()}%")
        )

    if sender and sender.strip():
        query = query.where(
            Email.sender.ilike(f"%{sender.strip()}%")
        )

    if category:
        query = query.where(Email.category == category)

    if priority is not None:
        query = query.where(Email.priority == priority)

    if email_status:
        query = query.where(Email.status == email_status)

    if date_from:
        query = query.where(Email.received_at >= date_from)

    if date_to:
        query = query.where(Email.received_at <= date_to)

    total = db.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0

    items = db.scalars(
        query.order_by(
            Email.received_at.desc(),
            Email.id.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return {
        "items": [
            EmailResponse.model_validate(item) for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/{email_id}", response_model=EmailResponse)
def get_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    email = db.get(Email, email_id)

    if email is None:
        raise HTTPException(
            status_code=404,
            detail="Email introuvable",
        )

    return email


@router.post(
    "",
    response_model=EmailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_email(
    payload: EmailCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = db.scalar(
        select(Email).where(
            Email.gmail_message_id == payload.gmail_message_id
        )
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Cet email existe déjà.",
        )

    email = Email(**payload.model_dump())
    db.add(email)

    try:
        db.commit()
        db.refresh(email)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Import impossible : identifiant dupliqué ou données invalides.",
        ) from exc

    return email


@router.patch("/{email_id}", response_model=EmailResponse)
def update_email(
    email_id: int,
    payload: EmailUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    email = db.get(Email, email_id)

    if email is None:
        raise HTTPException(
            status_code=404,
            detail="Email introuvable",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(email, field, value)

    try:
        db.commit()
        db.refresh(email)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail="Modification impossible.",
        ) from exc

    return email


@router.post("/{email_id}/classify", response_model=EmailResponse)
def classify_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ClassificationService(db)

    try:
        return service.classify_email(email_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
