from unittest.mock import Mock

import pytest

from app.services.classification_service import ClassificationService


def test_classify_email_saves_analysis():
    db = Mock()
    email = Mock()
    email.subject = "Facture octobre"
    email.sender = "comptabilite@example.com"
    email.body = "Payer avant demain."

    repository = Mock()
    repository.get_by_id.return_value = email
    repository.save_classification.return_value = email
    analyzer = Mock()
    analyzer.analyze.return_value = Mock(
        category="facture",
        priority=1,
        summary="Facture à payer avant demain.",
        expected_action="Confirmer le paiement.",
    )

    service = ClassificationService(db, analyzer=analyzer)
    service.repository = repository

    result = service.classify_email(42)

    analyzer.analyze.assert_called_once_with(
        subject="Facture octobre",
        sender="comptabilite@example.com",
        body="Payer avant demain.",
    )
    repository.save_classification.assert_called_once_with(
        email,
        category="facture",
        priority=1,
        summary="Facture à payer avant demain.",
        expected_action="Confirmer le paiement.",
    )
    assert result is email


def test_classify_email_raises_when_email_missing():
    db = Mock()
    repository = Mock()
    repository.get_by_id.return_value = None

    analyzer = Mock()
    service = ClassificationService(db, analyzer=analyzer)
    service.repository = repository

    with pytest.raises(ValueError, match="E-mail introuvable"):
        service.classify_email(999)

    analyzer.analyze.assert_not_called()