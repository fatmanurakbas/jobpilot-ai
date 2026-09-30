from pydantic import BaseModel, Field

from app.schemas.cv_validation import CVValidationResult


class CVFinalizationResult(BaseModel):
    success: bool

    application_id: int

    attempts: int = 0

    corrections_made: list[str] = Field(
        default_factory=list
    )

    validation: CVValidationResult

    cv_path: str | None = None

    pdf_path: str | None = None

    message: str