from pydantic import BaseModel


class FormSubmissionResult(BaseModel):
    application_id: int
    success: bool

    submitted: bool = False

    final_url: str | None = None
    confirmation: str | None = None
    submitted_at: str | None = None
    screenshot_available: bool = False
    status: str = "SUBMISSION_UNCONFIRMED"

    message: str
