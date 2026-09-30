import json

from app.schemas.candidate_profile import CandidateProfile
from app.schemas.cv_tailoring import CVTailoringPlan
from app.schemas.cv_validation import CVValidationResult
from app.services.llm_service import llm_service


SYSTEM_PROMPT = """
You are the CV Validator of JobPilot AI.

Your task is to verify that a tailored CV plan is factually supported
by the candidate's master profile.

The candidate profile is the ONLY source of truth.

STRICT RULES:

1. Check every factual claim in the tailored CV plan.
2. A claim must be supported by the candidate profile.
3. Never assume missing information.
4. Never infer years of experience unless explicitly supported.
5. Never allow invented technologies.
6. Never allow invented skills.
7. Never allow invented responsibilities.
8. Never allow invented achievements.
9. Never allow invented metrics, percentages, numbers, rankings or results.
10. Never allow invented job titles or organizations.
11. Never allow invented education or certifications.
12. Rewording is allowed when factual meaning is preserved.
13. General professional phrasing is allowed only when it does not introduce
    a new factual claim.
14. A technology appearing only in the target job is NOT evidence that the
    candidate knows that technology.
15. Missing job requirements must not be converted into candidate experience.
16. Evaluate the professional summary as carefully as project and experience
    bullets.
17. Evaluate prioritized skills against the candidate profile.
18. Return is_valid=false if any material unsupported factual claim exists.
19. Use severity="error" for unsupported factual claims.
20. Use severity="warning" only for wording that may be misleading but is not
    clearly false.

Do not improve or rewrite the CV.
Only validate it.
"""


class CVValidator:

    def validate(
        self,
        candidate: CandidateProfile,
        tailoring_plan: CVTailoringPlan,
    ) -> CVValidationResult:

        candidate_json = json.dumps(
            candidate.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        tailoring_json = json.dumps(
            tailoring_plan.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = f"""
Validate the following tailored CV plan against the candidate's
master profile.

MASTER CANDIDATE PROFILE:

{candidate_json}


TAILORED CV PLAN:

{tailoring_json}


Determine whether every factual claim in the tailored CV is supported
by the master candidate profile.

The target job requirements are not evidence of candidate experience.
"""

        result = llm_service.parse(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=CVValidationResult,
        )

        return result


cv_validator = CVValidator()