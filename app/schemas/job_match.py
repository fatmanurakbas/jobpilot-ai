from pydantic import BaseModel, Field

from app.schemas.candidate_profile import CandidateProfile
from app.schemas.job_analysis import JobAnalysis


class SkillEvidence(BaseModel):
    skill: str
    evidence: str
    source: str


class JobMatchAnalysis(BaseModel):

    matched_required_skills: list[SkillEvidence] = Field(
        default_factory=list
    )

    matched_preferred_skills: list[SkillEvidence] = Field(
        default_factory=list
    )

    missing_required_skills: list[str] = Field(
        default_factory=list
    )

    missing_preferred_skills: list[str] = Field(
        default_factory=list
    )

    strengths: list[str] = Field(
        default_factory=list
    )

    gaps: list[str] = Field(
        default_factory=list
    )

    relevant_projects: list[str] = Field(
        default_factory=list
    )

    relevant_experiences: list[str] = Field(
        default_factory=list
    )


class JobMatchResult(JobMatchAnalysis):
    match_percentage: int
    application_id: int | None = None


class JobMatchRequest(BaseModel):
    candidate: CandidateProfile
    job: JobAnalysis
