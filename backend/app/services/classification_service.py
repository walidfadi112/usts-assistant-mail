
from sqlalchemy.orm import Session

from app.ai.analyzer import EmailAnalyzer
from app.ai.schemas import EmailAnalysis
from app.models.email import Email
from app.repositories.email_repository import EmailRepository


class ClassificationService:
    """Coordonne l'analyse IA et la sauvegarde des résultats."""

    def __init__(
        self,
        db: Session,
        analyzer: EmailAnalyzer | None = None,
    ) -> None:
        self.repository = EmailRepository(db)
        self.analyzer = analyzer or EmailAnalyzer()

    def classify_email(self, email_id: int) -> Email:
        email = self.repository.get_by_id(email_id)

        if email is None:
            raise ValueError(f"E-mail introuvable : {email_id}")

        analysis: EmailAnalysis = self.analyzer.analyze(
            subject=email.subject,
            sender=email.sender,
            body=email.body,
        )

        return self.repository.save_classification(
            email,
            category=analysis.category,
            priority=analysis.priority,
            summary=analysis.summary,
            expected_action=analysis.expected_action,
        )
