
import logging
import random
import time

from groq import (
    Groq,
    RateLimitError,
    APIConnectionError,
    InternalServerError,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqProvider:
    def __init__(self, model: str | None = None) -> None:
        self.client = Groq(
            api_key=settings.groq_api_key,
            timeout=30.0,
            max_retries=0,
        )
        self.model = model or settings.groq_model

    def generate(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        **kwargs,
    ) -> str:
        for attempt in range(5):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                if not response.choices:
                    raise ValueError("Groq n'a renvoyé aucun choix.")

                choice = response.choices[0]
                content = choice.message.content

                if not content or not content.strip():
                    raise ValueError(
                        f"Réponse Groq vide (finish_reason={choice.finish_reason})."
                    )

                if choice.finish_reason == "length":
                    raise ValueError("Réponse Groq tronquée : limite de tokens atteinte.")

                return content.strip()

            except RateLimitError as exc:
                if attempt == 4:
                    logger.error("Limite Groq atteinte après 5 tentatives.")
                    raise

                # Attend au moins 10 secondes, avec un délai croissant.
                wait_seconds = min(10 * (2 ** attempt), 60) + random.uniform(0, 2)
                logger.warning(
                    "Limite Groq (429). Nouvelle tentative dans %.1f secondes.",
                    wait_seconds,
                )
                time.sleep(wait_seconds)

            except (APIConnectionError, InternalServerError):
                if attempt == 4:
                    raise
                time.sleep(min(2 ** attempt, 16))

        raise RuntimeError("Échec inattendu de l'appel Groq.")
