
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class EmailThread(Base):
    __tablename__ = "email_threads"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    gmail_thread_id: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )
    subject: Mapped[str] = mapped_column(String(500), default="")
