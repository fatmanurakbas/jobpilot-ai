from pydantic import BaseModel, Field


class FieldVerification(BaseModel):
    field_index: int
    field_name: str | None = None

    action: str

    verified: bool

    expected_value: str | None = None
    actual_value: str | None = None

    message: str


class FormVerificationResult(BaseModel):
    verified: bool

    verified_count: int = 0
    failed_count: int = 0

    fields: list[FieldVerification] = Field(
        default_factory=list
    )

    screenshot_path: str | None = None