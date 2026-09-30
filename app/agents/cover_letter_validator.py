import json

from openai import OpenAI

from app.config import settings
from app.schemas.candidate_profile import CandidateProfile
from app.schemas.cover_letter import CoverLetter
from app.schemas.cover_letter_validation import (
    CoverLetterValidationResult,
)


class CoverLetterValidator:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def validate(
        self,
        candidate: CandidateProfile,
        cover_letter: CoverLetter,
        job_data: dict,
    ) -> CoverLetterValidationResult:

        system_prompt = """
You are a strict factual validator for a job application
cover letter.

Your task is NOT to improve the writing.

Your task is to verify whether factual claims in the cover
letter are supported by the supplied evidence.

SOURCE-OF-TRUTH RULES:

1. Candidate Profile is the ONLY source of truth for factual
   claims about the candidate.

2. Job Data is the source of truth only for factual claims
   about:
   - the company
   - the position
   - job requirements
   - location
   - work arrangement
   - information explicitly contained in the job posting

3. A job requirement is NEVER evidence that the candidate
   possesses that skill.

4. Do not use outside knowledge.

5. Do not assume missing facts.

VALIDATION RULES:

Check factual claims concerning:

- skills
- technologies
- education
- graduation information
- employment
- internships
- projects
- project responsibilities
- certifications
- languages
- proficiency levels
- achievements
- metrics
- dates
- responsibilities
- tools
- frameworks
- work arrangement
- company facts

COMPOSITIONAL HALLUCINATION:

Pay special attention to claims that combine two independently
true facts into a new unsupported relationship.

Example:

Candidate Profile:
- candidate built an LLM project
- candidate performed API testing during an internship

Cover Letter:
"I performed API testing in my LLM project."

This must be considered unsupported unless the Candidate Profile
explicitly supports that relationship.

RELEVANCE VS FACT:

Statements explaining that an existing skill or project may be
relevant to a job requirement are allowed.

However, relevance must not be rewritten as a historical fact.

Example:

Allowed:
"My Docker experience is relevant to environments where models
are deployed as services."

Not automatically allowed:
"I deployed machine learning models with Docker."

The second statement requires explicit evidence.

SUBJECTIVE / FUTURE STATEMENTS:

Reasonable expressions of:
- interest
- motivation
- willingness to learn
- desire to contribute

are not factual hallucinations.

However, concrete claims about availability, relocation,
work authorization, ability to work at a location, or ability
to comply with a specific work arrangement require evidence
when presented as established facts.

SEVERITY:

Use "error" when:
- a material factual claim about the candidate is unsupported
- a company/job fact contradicts Job Data
- two supported facts are combined into an unsupported claim
- proficiency or responsibility is materially exaggerated

Use "warning" when:
- wording could reasonably create a misleading impression
- a statement is stronger than the underlying evidence
- support exists but the wording should be more precise

VALID RESULT:

is_valid must be false if at least one material unsupported
factual claim has severity "error".

Warnings alone do not require is_valid=false.

checked_claims should represent the approximate number of
material factual claims that were checked.

Return the requested structured schema.
"""

        payload = {
            "candidate_profile": candidate.model_dump(),
            "job_data": job_data,
            "cover_letter": cover_letter.model_dump(),
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
            text_format=CoverLetterValidationResult,
        )

        if not response.output_parsed:
            raise RuntimeError(
                "Cover Letter Validator did not "
                "return a structured result."
            )

        return response.output_parsed


cover_letter_validator = CoverLetterValidator()