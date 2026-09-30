from pydantic import BaseModel, Field


class CoverLetterValidationIssue(BaseModel):
    field: str
    generated_text: str
    reason: str
    severity: str


class CoverLetterValidationResult(BaseModel):
    is_valid: bool

    issues: list[CoverLetterValidationIssue] = Field(
        default_factory=list
    )

    checked_claims: int = 0

    summary: str | None = None