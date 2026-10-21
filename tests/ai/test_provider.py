
from unittest.mock import MagicMock, patch

import pytest

from app.ai.provider import GroqProvider


def test_provider_rejects_missing_api_key():
    with patch("app.ai.provider.settings") as mock_settings:
        mock_settings.groq_api_key = ""
        mock_settings.groq_model = "openai/gpt-oss-20b"

        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            GroqProvider()


def test_generate_returns_model_text():
    with patch("app.ai.provider.settings") as mock_settings:
        mock_settings.groq_api_key = "test-key"
        mock_settings.groq_model = "openai/gpt-oss-20b"

        provider = GroqProvider()

    fake_response = MagicMock()
    fake_response.choices[0].message.content = "Réponse simulée"

    with patch.object(
        provider.client.chat.completions,
        "create",
        return_value=fake_response,
    ) as mock_create:
        result = provider.generate(
            messages=[
                {"role": "user", "content": "Bonjour"}
            ]
        )

    assert result == "Réponse simulée"
    mock_create.assert_called_once()

