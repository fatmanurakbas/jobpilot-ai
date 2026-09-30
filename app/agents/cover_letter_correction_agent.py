import json

from openai import OpenAI

from app.config import settings
from app.schemas.candidate_profile import CandidateProfile
from app.schemas.cover_letter import CoverLetter
from app.schemas.cover_letter_validation import (
    CoverLetterValidationResult,
)
from app.schemas.cover_letter_correction import (
    CoverLetterCorrectionResult,
)


class CoverLetterCorrectionAgent:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def correct(
        self,
        candidate: CandidateProfile,
        cover_letter: CoverLetter,
        validation: CoverLetterValidationResult,
        job_data: dict,
    ) -> CoverLetterCorrectionResult:

        system_prompt = """
You are a factual correction agent for job application
cover letters.

Your task is to correct factual problems identified by the
Cover Letter Validator while preserving the quality and intent
of the letter.

SOURCE-OF-TRUTH RULES:

1. Candidate Profile is the ONLY source of truth for factual
   claims about the candidate.

2. Job Data is the source of truth only for facts about:
   - company
   - position
   - location
   - work arrangement
   - requirements
   - information explicitly stated in the job posting

3. Job requirements are NOT evidence that the candidate
   possesses those qualifications.

4. Do not use outside knowledge.

5. Never invent or infer unsupported:
   - skills
   - technologies
   - responsibilities
   - employment
   - projects
   - achievements
   - metrics
   - education
   - certifications
   - language levels
   - dates
   - production experience

CORRECTION RULES:

1. Correct every validation issue with severity "error".

2. Resolve warnings whenever possible without damaging the
   meaning or relevance of the letter.

3. Prefer weakening or clarifying an unsupported statement
   rather than replacing it with another inferred claim.

4. Preserve all valid content unless a change is necessary
   to fix a validation issue.

5. Do NOT perform unrelated rewriting.

6. Do NOT make the letter more impressive by adding new facts.

7. Preserve the original language.

8. Preserve the CoverLetter structured format.

9. Pay special attention to compositional hallucinations.
   Do not combine separately supported facts into a new
   unsupported relationship.

10. A statement about relevance may remain a statement about
    relevance, but must not become a historical claim.

Example:

Unsupported:
"I deployed machine learning models with Docker."

If evidence only supports Docker application/container
management and separate machine-learning projects, prefer:

"I gained experience with Docker-based container management,
which provides relevant infrastructure knowledge for model
serving environments."

Do not claim actual ML model deployment unless explicitly
supported.

Set corrected=true if at least one change was made.

corrections_made must clearly describe each meaningful
correction.

Return the complete corrected CoverLetter, not only the changed
sentences.
11. When a validation issue identifies a compositional
    hallucination, prefer SPLITTING the claims into separate
    factual sentences.

    Do not merely weaken the connecting phrase.

    Example:

    Evidence:
    - machine learning model development exists
    - Docker/microservice/API experience exists separately

    Unsafe:
    "I used Docker and microservices during model development."

    Still potentially misleading:
    "My Docker experience supports my model development work."

    Preferred:
    "I developed machine learning models in my AI projects.
    Separately, I gained experience with Docker, microservice
    architecture and RESTful APIs in backend projects."

    Preserve the separation unless the Candidate Profile
    explicitly proves that the technologies were used together.
"""


        payload = {
            "candidate_profile": candidate.model_dump(),
            "job_data": job_data,
            "cover_letter": cover_letter.model_dump(),
            "validation": validation.model_dump(),
        }

        response = self.client.responses.parse(
            model=settings.openai_model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        payload,
                        ensure_ascii=False,
                        default=str,
                    ),
                },
            ],
            text_format=CoverLetterCorrectionResult,
        )

        if not response.output_parsed:
            raise RuntimeError(
                "Cover Letter Correction Agent did not "
                "return a structured result."
            )

        return response.output_parsed


cover_letter_correction_agent = (
    CoverLetterCorrectionAgent()
)