from datetime import datetime

from pydantic import BaseModel


class ApplicationSummary(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    company: str | None = None
    position: str | None = None
    match_percentage: float | None = None
    status: str
    created_at: datetime
    submitted_at: datetime | None = None
