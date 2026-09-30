from pydantic import BaseModel, Field

from app.schemas.cover_letter import CoverLetter


class CoverLetterCorrectionResult(BaseModel):
    corrected: bool

    corrections_made: list[str] = Field(
        default_factory=list
    )

    corrected_cover_letter: CoverLetter