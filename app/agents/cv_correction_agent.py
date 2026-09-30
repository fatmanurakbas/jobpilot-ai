import json

from app.schemas.candidate_profile import CandidateProfile
from app.schemas.cv_tailoring import CVTailoringPlan
from app.schemas.cv_validation import CVValidationResult
from app.schemas.cv_correction import CVCorrectionResult
from app.services.llm_service import llm_service


SYSTEM_PROMPT = """
You are the CV Correction Agent of JobPilot AI.

Your task is to correct a tailored CV plan using validation feedback.

The master candidate profile is the ONLY source of factual truth.

STRICT RULES:

1. Never invent information.
2. Never add a skill that is unsupported by the candidate profile.
3. Never add technologies that are unsupported.
4. Never invent years of experience.
5. Never invent metrics, percentages, achievements or results.
6. Never invent organizations, job titles, education or certifications.
7. Correct every error reported by the validator.
8. Resolve warnings when they can be made more precise without losing
   useful information.
9. Preserve valid content that does not need correction.
10. Do not make unrelated improvements.
11. Keep the source CV language.
12. If cv_language is "tr", generated content must remain Turkish.
13. If cv_language is "en", generated content must remain English.
14. Prefer precise evidence-backed wording over broad claims.
15. Do not turn job requirements into candidate experience.
16. corrected_plan must remain a complete CVTailoringPlan.
17. corrections_made must briefly describe the changes that were actually made.

The goal is factual consistency, not making the candidate sound more experienced.
"""


class CVCorrectionAgent:

    def correct(
        self,
        candidate: CandidateProfile,
        tailoring_plan: CVTailoringPlan,
        validation: CVValidationResult,
    ) -> CVCorrectionResult:

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

        validation_json = json.dumps(
            validation.model_dump(),
            ensure_ascii=False,
            indent=2,
        )

        user_prompt = f"""
Correct the tailored CV plan using the validation report.

SOURCE CV LANGUAGE:
{candidate.cv_language}

MASTER CANDIDATE PROFILE:

{candidate_json}


CURRENT TAILORED CV PLAN:

{tailoring_json}


VALIDATION REPORT:

{validation_json}


Return a complete corrected CV tailoring plan.

Only change content when required by the validation report.
Every corrected factual statement must be supported by the
master candidate profile.
"""

        return llm_service.parse(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=CVCorrectionResult,
        )


cv_correction_agent = CVCorrectionAgent()