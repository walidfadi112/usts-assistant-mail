from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Email(Base):
    __tablename__ = "emails"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gmail_message_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    thread_id: Mapped[int | None] = mapped_column(
        ForeignKey("email_threads.id"), nullable=True
    )
    sender: Mapped[str] = mapped_column(String(320))
    recipients: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    received_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    category: Mapped[str] = mapped_column(String(50), default="autre")
    priority: Mapped[int] = mapped_column(Integer, default=2)
    summary: Mapped[str] = mapped_column(Text, default="")
    expected_action: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="à traiter")