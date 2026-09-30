import json

from app.schemas.candidate_profile import CandidateProfile
from app.schemas.job_analysis import JobAnalysis
from app.schemas.job_match import JobMatchAnalysis
from app.services.llm_service import llm_service


SYSTEM_PROMPT = """
You are the Candidate-Job Match Agent of JobPilot AI.

Compare documented candidate evidence against explicit job requirements.

STRICT RULES:

1. Use only information contained in the candidate profile.
2. Never invent candidate skills.
3. Never assume that the candidate knows a technology.
4. Every matched skill must have concrete evidence.
5. Evidence must come from the supplied candidate profile.
6. Clearly distinguish required and preferred skills.
7. Missing skills must remain missing.
8. Do not calculate a match percentage.
9. Do not estimate hiring probability.
10. Do not exaggerate candidate experience.

Semantic equivalents may count as matches only when the candidate
profile provides clear evidence.

Example:

Job requirement:
"Machine Learning"

Candidate evidence:
"Developed a TensorFlow recommendation model"

This may be considered supporting evidence.

But weak or speculative relationships must not be considered matches.
"""


class MatchAgent:

    def analyze(
        self,
        candidate: CandidateProfile,
        job: JobAnalysis
    ) -> JobMatchAnalysis:

        candidate_json = json.dumps(
            candidate.model_dump(),
            ensure_ascii=False,
            indent=2
        )

        job_json = json.dumps(
            job.model_dump(),
            ensure_ascii=False,
            indent=2
        )

        user_prompt = f"""
Compare the candidate against the job requirements.

CANDIDATE:

{candidate_json}

JOB:

{job_json}
"""

        return llm_service.parse(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=JobMatchAnalysis
        )


match_agent = MatchAgent()