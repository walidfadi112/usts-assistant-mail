
from sqlalchemy.orm import Session

from app.models.email import Email


class EmailRepository:
    """Accès aux données des e-mails."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, email_id: int) -> Email | None:
        return self.db.get(Email, email_id)

    def save_classification(
        self,
        email: Email,
        *,
        category: str,
        priority: int,
        summary: str,
        expected_action: str,
    ) -> Email:
        email.category = category
        email.priority = priority
        email.summary = summary
        email.expected_action = expected_action

        self.db.add(email)
        self.db.commit()
        self.db.refresh(email)

        return email
