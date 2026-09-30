from datetime import datetime

from pydantic import BaseModel


class SubmissionApprovalRequest(BaseModel):
    url: str


class SubmissionApprovalResult(BaseModel):
    application_id: int

    approved: bool
    approved_at: datetime | None = None

    submission_hash: str | None = None
    url: str

    message: str


class SubmissionApprovalStatus(BaseModel):
    application_id: int

    approved: bool
    approval_valid: bool

    approved_at: datetime | None = None

    url_unchanged: bool = False
    submission_unchanged: bool = False

    message: str