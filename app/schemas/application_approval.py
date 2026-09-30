from datetime import datetime

from pydantic import BaseModel


class ApplicationApprovalResult(BaseModel):
    application_id: int

    approved: bool

    approved_at: datetime | None = None

    cv_hash: str | None = None
    cover_letter_hash: str | None = None

    message: str

class ApplicationApprovalStatus(BaseModel):
    application_id: int

    approved: bool
    approval_valid: bool

    approved_at: datetime | None = None

    cv_unchanged: bool = False
    cover_letter_unchanged: bool = False

    message: str    