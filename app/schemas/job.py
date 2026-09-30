"""Schemas for job-related data."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    company: str
    position: str
    location: str | None = None
    job_url: str | None = None
    description: str


class JobResponse(JobCreate):
    id: int
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )