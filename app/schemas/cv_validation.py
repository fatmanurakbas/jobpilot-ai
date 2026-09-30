from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    field: str

    generated_text: str

    reason: str

    severity: str


class CVValidationResult(BaseModel):
    is_valid: bool

    issues: list[ValidationIssue] = Field(
        default_factory=list
    )

    checked_claims: int = 0

    summary: str | None = None