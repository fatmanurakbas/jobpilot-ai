from typing import Literal

from pydantic import BaseModel, Field


class ResolvedFormField(BaseModel):
    field_index: int

    field_name: str | None = None
    field_label: str | None = None

    action: Literal[
        "FILL",
        "UPLOAD",
        "SKIP",
        "UNRESOLVED",
    ]

    value: str | None = None
    file_path: str | None = None

    resolved_from: str | None = None
    reason: str


class ResolvedFormPlan(BaseModel):
    application_id: int
    url: str

    fields: list[ResolvedFormField] = Field(
        default_factory=list
    )

    fill_count: int = 0
    upload_count: int = 0
    unresolved_count: int = 0
    skip_count: int = 0

    ready_to_fill: bool = False