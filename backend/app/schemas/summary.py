from datetime import date
from pydantic import BaseModel


class PriorityEmail(BaseModel):
    id: int
    sender: str
    subject: str
    priority: int
    category: str
    summary: str | None = None
    expected_action: str | None = None
    reason: str


class DailySummaryResponse(BaseModel):
    date: date
    total_emails: int
    high_priority_count: int
    category_counts: dict[str, int]
    overview: str
    top_priority_emails: list[PriorityEmail]
