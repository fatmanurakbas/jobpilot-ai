from pydantic import BaseModel, Field


class FormAnswerItem(BaseModel):
    field_name: str
    value: str


class SaveFormAnswersRequest(BaseModel):
    answers: list[FormAnswerItem] = Field(
        default_factory=list
    )


class SaveFormAnswersResult(BaseModel):
    application_id: int
    saved_answers: dict[str, str]
    message: str