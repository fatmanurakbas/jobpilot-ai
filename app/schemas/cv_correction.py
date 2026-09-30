from pydantic import BaseModel, Field

from app.schemas.cv_tailoring import CVTailoringPlan


class CVCorrectionResult(BaseModel):
    corrected: bool

    corrections_made: list[str] = Field(
        default_factory=list
    )

    corrected_plan: CVTailoringPlan