from typing import Literal

from pydantic import BaseModel, Field


class FormFieldMapping(BaseModel):
    field_index: int

    field_name: str | None = None
    field_label: str | None = None

    status: Literal[
        "AUTO_FILL",
        "FILE_UPLOAD",
        "NEEDS_USER_INPUT",
        "SKIP",
    ]

    source: str | None = None

    value: str | None = None

    reason: str


class FormFieldMappingList(BaseModel):
    mappings: list[FormFieldMapping] = Field(
        default_factory=list
    )


class FormMappingResult(BaseModel):
    application_id: int
    url: str

    mappings: list[FormFieldMapping] = Field(
        default_factory=list
    )

    auto_fill_count: int = 0
    file_upload_count: int = 0
    needs_user_input_count: int = 0
    skip_count: int = 0

    ready_to_fill: bool = False