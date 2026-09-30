from pydantic import BaseModel, Field

from app.schemas.form_verification import (
    FormVerificationResult,
)


class FormFillRequest(BaseModel):
    url: str


class FilledFieldResult(BaseModel):
    field_index: int
    field_name: str | None = None

    action: str
    success: bool

    message: str


class FormFillResult(BaseModel):
    application_id: int
    url: str

    success: bool

    filled_count: int = 0
    uploaded_count: int = 0
    failed_count: int = 0

    submitted: bool = False
    status: str = "FORM_PREPARED"
    prepared_at: str | None = None

    results: list[FilledFieldResult] = Field(
        default_factory=list
    )

    verification: FormVerificationResult | None = None

    message: str
