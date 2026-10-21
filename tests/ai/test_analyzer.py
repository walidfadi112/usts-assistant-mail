
from unittest.mock import Mock

from app.ai.analyzer import EmailAnalyzer


def test_analyzer_returns_valid_analysis():
    provider = Mock()
    provider.generate.return_value = (
        '{"category":"facture",'
        '"priority":1,'
        '"summary":"Une facture doit être réglée.",'
        '"expected_action":"Vérifier la date limite de paiement."}'
    )

    analyzer = EmailAnalyzer(provider=provider)

    result = analyzer.analyze(
        subject="Facture octobre",
        sender="comptabilite@example.com",
        body="Merci de régler la facture avant vendredi.",
    )

    assert result.category == "facture"
    assert result.priority == 1
    assert result.summary == "Une facture doit être réglée."
    provider.generate.assert_called_once()


def test_analyzer_retries_invalid_json():
    provider = Mock()
    provider.generate.side_effect = [
        "ceci n'est pas du JSON",
        (
            '{"category":"client",'
            '"priority":2,'
            '"summary":"Un client pose une question.",'
            '"expected_action":"Répondre au client."}'
        ),
    ]

    analyzer = EmailAnalyzer(provider=provider)

    result = analyzer.analyze(
        subject="Question",
        sender="client@example.com",
        body="Pouvez-vous me renseigner ?",
    )

    assert result.category == "client"
    assert provider.generate.call_count == 2


def test_analyzer_falls_back_after_two_invalid_responses():
    provider = Mock()
    provider.generate.return_value = "réponse invalide"

    analyzer = EmailAnalyzer(provider=provider)

    result = analyzer.analyze(
        subject="Message",
        sender="unknown@example.com",
        body="Contenu quelconque",
    )

    assert result.category == "autre"
    assert result.summary == "Analyse automatique indisponible."
    assert provider.generate.call_count == 2
