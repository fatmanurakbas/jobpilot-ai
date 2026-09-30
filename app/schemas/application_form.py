from pydantic import BaseModel, Field
from pydantic import BaseModel, Field, HttpUrl 
 
class ApplicationFormOption(BaseModel):
    value: str | None = None
    text: str | None = None


class ApplicationFormField(BaseModel):
    index: int

    tag: str
    type: str | None = None

    name: str | None = None
    id: str | None = None

    label: str | None = None
    placeholder: str | None = None

    required: bool = False
    disabled: bool = False
    readonly: bool = False

    accept: str | None = None

    options: list[ApplicationFormOption] = Field(
        default_factory=list
    )


class ApplicationFormInspection(BaseModel):
    url: str
    final_url: str

    page_title: str | None = None

    fields: list[ApplicationFormField] = Field(
        default_factory=list
    )

    field_count: int = 0

class ApplicationFormInspectionRequest(BaseModel):
    url: str    

class ApplicationFormInspectionRequest(BaseModel):
    url: HttpUrl