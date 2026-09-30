import json

from app.schemas.candidate_profile import CandidateProfile
from app.schemas.job_analysis import JobAnalysis
from app.schemas.job_match import JobMatchResult
from app.schemas.cv_tailoring import CVTailoringPlan

from app.services.llm_service import llm_service


SYSTEM_PROMPT = """
You are the CV Tailoring Agent of JobPilot AI.

Your task is to adapt an existing candidate profile to a specific
job advertisement without fabricating information.

STRICT RULES:

1. Never invent skills.
2. Never invent technologies.
3. Never invent responsibilities.
4. Never invent achievements.
5. Never invent metrics or numbers.
6. Never claim experience that is not supported by the candidate profile.
7. Never convert a missing job requirement into a candidate skill.
8. Every tailored bullet must preserve the factual meaning of the original.
9. You may change wording, emphasis and ordering.
10. Prioritize candidate evidence that is relevant to the target job.
11. Deprioritize irrelevant information rather than deleting factual history.
12. Use concise, professional CV language.
13. Do not use unsupported adjectives such as "expert", "advanced",
    "highly skilled" or "proficient".
14. The match analysis is supporting context, not permission to create facts.
15. Preserve the language of the candidate's master CV.
16. If cv_language is "tr", all generated CV text must be Turkish.
17. If cv_language is "en", all generated CV text must be English.
18. Never translate a Turkish CV into English or an English CV into Turkish unless explicitly requested.
The master candidate profile is the source of truth.
"""


class CVTailoringAgent:

    def tailor(
        self,
        candidate: CandidateProfile,
        job: JobAnalysis,
        match: JobMatchResult
    ) -> CVTailoringPlan:

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

        match_json = json.dumps(
            match.model_dump(),
            ensure_ascii=False,
            indent=2
        )
        user_prompt = f"""
        Create a CV tailoring plan.

        SOURCE CV LANGUAGE:
        {candidate.cv_language}

        CANDIDATE PROFILE:
        {candidate_json}

        TARGET JOB:
        {job_json}

        MATCH ANALYSIS:
        {match_json}

        Only use factual information contained in the candidate profile.

        IMPORTANT:
        Generate all new CV content in the source CV language:
        {candidate.cv_language}
       """

        return llm_service.parse(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=CVTailoringPlan
        )


cv_tailoring_agent = CVTailoringAgent()