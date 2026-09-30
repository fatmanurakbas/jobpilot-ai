from datetime import datetime
from pydantic import BaseModel

from app.schemas.cv_validation import CVValidationResult
from app.schemas.cover_letter_validation import (
    CoverLetterValidationResult,
)


class ApplicationPackage(BaseModel):
    application_id: int

    status: str | None = None
    form_prepared_at: datetime | None = None
    form_verification: dict | None = None
    submitted_at: datetime | None = None
    submission_url: str | None = None
    submission_confirmation: str | None = None
    submission_screenshot_available: bool = False

    candidate_id: int
    job_id: int

    match_percentage: float | None = None

    cv_plan_ready: bool = False
    cv_validation_ready: bool = False
    cover_letter_ready: bool = False
    cover_letter_validation_ready: bool = False

    cv_validated: bool = False
    cover_letter_validated: bool = False

    cv_docx_ready: bool = False
    cv_pdf_ready: bool = False

    cover_letter_docx_ready: bool = False
    cover_letter_pdf_ready: bool = False

    cv_path: str | None = None
    cv_pdf_path: str | None = None

    cover_letter_path: str | None = None
    cover_letter_pdf_path: str | None = None

    cv_validation: CVValidationResult | None = None

    cover_letter_validation: (
        CoverLetterValidationResult | None
    ) = None

    ready_for_review: bool = False
