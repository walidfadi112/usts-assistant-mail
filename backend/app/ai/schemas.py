
from typing import Literal

from pydantic import BaseModel, Field


EmailCategory = Literal[
    "client",
    "facture",
    "rendez-vous",
    "newsletter",
    "spam probable",
    "autre",
]


class EmailAnalysis(BaseModel):
    category: EmailCategory

    priority: int = Field(ge=1, le=3)

    summary: str = Field(min_length=1)

    expected_action: str = Field(min_length=1)
