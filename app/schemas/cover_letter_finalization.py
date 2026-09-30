from pydantic import BaseModel, Field

from app.schemas.cover_letter_validation import (
    CoverLetterValidationResult,
)


class CoverLetterFinalizationResult(BaseModel):
    success: bool
    application_id: int

    correction_attempts: int = 0
    warning_cleanup_attempts: int = 0

    corrections_made: list[str] = Field(
        default_factory=list
    )

    final_validation: CoverLetterValidationResult

    cover_letter_path: str | None = None
    cover_letter_pdf_path: str | None = None

    message: str