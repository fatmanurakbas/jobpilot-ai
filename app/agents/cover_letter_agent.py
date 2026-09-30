import json

from openai import OpenAI

from app.config import settings
from app.schemas.candidate_profile import CandidateProfile
from app.schemas.cv_tailoring import CVTailoringPlan
from app.schemas.cover_letter import CoverLetter


class CoverLetterAgent:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def generate(
        self,
        candidate: CandidateProfile,
        tailoring_plan: CVTailoringPlan,
        job_data: dict,
    ) -> CoverLetter:

        system_prompt = """
You are a professional job application cover letter writer.

Your task is to write a concise, professional and factual cover
letter tailored to the supplied job posting.

CRITICAL FACTUAL RULES:

1. The Candidate Profile is the ONLY source of truth for factual
   claims about the candidate.

2. Never invent:
   - skills
   - technologies
   - employment
   - internships
   - projects
   - responsibilities
   - achievements
   - metrics
   - certifications
   - education
   - dates
   - leadership experience
   - years of experience

3. The CV Tailoring Plan may be used to determine emphasis and
   relevance, but it is NOT an independent factual source.

4. The Job Data describes the employer and role. Job requirements
   are NOT evidence that the candidate possesses those skills.

5. You may explain why an existing candidate experience is relevant
   to the role, but you must not transform relevance into a factual
   claim that the candidate performed something they did not perform.

6. Avoid unsupported causal or compositional claims.
   Two independently true facts must not be combined in a way that
   creates a new unsupported claim.

7. Preserve the language of the candidate's CV.
   If cv_language is "tr", write the letter in Turkish.
   If cv_language is "en", write the letter in English.

8. Do not exaggerate proficiency.
   Do not use terms such as "expert", "advanced", "extensive",
   "highly experienced" or equivalents unless directly supported
   by the Candidate Profile.

9. Do not invent company-specific facts.
   Only mention company information explicitly supplied in Job Data.

10. Keep the letter concise.
    Prefer approximately 250-400 words.

11. Do not repeat the CV mechanically.
    Select the most relevant supported experiences and explain their
    relevance to the role.

12. The tone should be professional, natural and specific.
    Avoid generic AI-style filler.

13. Do not claim that the candidate satisfies every requirement
    unless the Candidate Profile actually supports that statement.

14. Return data matching the requested structured schema.
"""

        payload = {
            "candidate_profile": candidate.model_dump(),
            "cv_tailoring_plan": tailoring_plan.model_dump(),
            "job_data": job_data,
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
            text_format=CoverLetter,
        )

        if not response.output_parsed:
            raise RuntimeError(
                "Cover Letter Agent did not return "
                "a structured result."
            )

        return response.output_parsed


cover_letter_agent = CoverLetterAgent()