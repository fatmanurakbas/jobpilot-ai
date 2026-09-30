from fastapi import APIRouter

from app.agents.cv_parser import cv_parser
from app.agents.match_agent import match_agent

from app.schemas.candidate_profile import (
    CandidateProfile,
    CVParseRequest
)

from app.schemas.job_match import (
    JobMatchRequest,
    JobMatchResult
)


router = APIRouter(
    prefix="/agents",
    tags=["AI Agents"]
)


@router.post(
    "/parse-cv",
    response_model=CandidateProfile
)
def parse_cv(
    request: CVParseRequest
):
    return cv_parser.parse(
        request.cv_text
    )


@router.post(
    "/match",
    response_model=JobMatchResult
)
def match_candidate(
    request: JobMatchRequest
):
    return match_agent.analyze(
        candidate=request.candidate,
        job=request.job
    )