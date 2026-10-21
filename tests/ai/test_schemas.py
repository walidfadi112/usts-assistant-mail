
import pytest
from pydantic import ValidationError

from app.ai.schemas import EmailAnalysis


def test_valid_analysis_is_accepted():
    analysis = EmailAnalysis(
        category="facture",
        priority=1,
        summary="Le client demande une confirmation.",
        expected_action="Confirmer la réception.",
    )

    assert analysis.category == "facture"
    assert analysis.priority == 1


@pytest.mark.parametrize("priority", [0, 4, 7, -1])
def test_invalid_priority_is_rejected(priority):
    with pytest.raises(ValidationError):
        EmailAnalysis(
            category="facture",
            priority=priority,
            summary="Test",
            expected_action="Confirmer",
        )


def test_unknown_category_is_rejected():
    with pytest.raises(ValidationError):
        EmailAnalysis(
            category="inconnu",
            priority=1,
            summary="Test",
            expected_action="Confirmer",
        )


@pytest.mark.parametrize("field", ["summary", "expected_action"])
def test_empty_text_is_rejected(field):
    data = {
        "category": "facture",
        "priority": 1,
        "summary": "Test",
        "expected_action": "Confirmer",
    }
    data[field] = ""

    with pytest.raises(ValidationError):
        EmailAnalysis(**data)

