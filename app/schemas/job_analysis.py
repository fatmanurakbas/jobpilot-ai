from pydantic import BaseModel, Field


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(
        min_length=50,
        description="Full text of the job advertisement"
    )


class JobAnalysis(BaseModel):
    company: str | None = None
    position: str | None = None
    location: str | None = None

    required_skills: list[str] = []
    preferred_skills: list[str] = []

    education_requirements: list[str] = []
    experience_level: str | None = None
    language_requirements: list[str] = []

    responsibilities: list[str] = []

    employment_type: str | None = None
    work_model: str | None = None

class JobAnalyzeAndSaveRequest(BaseModel):
    job_description: str = Field(
        min_length=50
    )

    job_url: str | None = None