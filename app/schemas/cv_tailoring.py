from pydantic import BaseModel, Field


class TailoredBullet(BaseModel):
    original: str
    tailored: str
    reason: str


class TailoredProject(BaseModel):
    project_name: str

    relevance_reason: str

    tailored_bullets: list[TailoredBullet] = Field(
        default_factory=list
    )


class TailoredExperience(BaseModel):
    experience_title: str

    relevance_reason: str

    tailored_bullets: list[TailoredBullet] = Field(
        default_factory=list
    )


class CVTailoringPlan(BaseModel):

    target_position: str | None = None

    professional_summary: str | None = None

    prioritized_skills: list[str] = Field(
        default_factory=list
    )

    projects: list[TailoredProject] = Field(
        default_factory=list
    )

    experiences: list[TailoredExperience] = Field(
        default_factory=list
    )

    omitted_or_deprioritized_sections: list[str] = Field(
        default_factory=list
    )