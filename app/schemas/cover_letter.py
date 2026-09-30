from pydantic import BaseModel, Field


class CoverLetter(BaseModel):
    language: str

    target_position: str

    subject: str | None = None

    greeting: str

    opening: str

    body_paragraphs: list[str] = Field(
        default_factory=list
    )

    closing: str

    sign_off: str

    candidate_name: str