from pydantic import BaseModel, Field


class ExperienceItem(BaseModel):
    title: str
    organization: str | None = None
    description: list[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    name: str
    description: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: str
    degree: str | None = None
    department: str | None = None
    graduation_year: int | None = None


class CandidateProfile(BaseModel):
    full_name: str | None = None

    email: str | None = None
    phone: str | None = None

    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None

    cv_language: str | None = None

    summary: str | None = None

    skills: list[str] = Field(default_factory=list)

    education: list[EducationItem] = Field(
        default_factory=list
    )

    experiences: list[ExperienceItem] = Field(
        default_factory=list
    )

    projects: list[ProjectItem] = Field(
        default_factory=list
    )

    certifications: list[str] = Field(
        default_factory=list
    )

    languages: list[str] = Field(
        default_factory=list
    )
class CVParseRequest(BaseModel):
    cv_text: str = Field(
        min_length=100,
        description="Raw text extracted from the candidate's master CV"
    )