import json

from openai import OpenAI

from app.config import settings
from app.schemas.candidate_profile import CandidateProfile
from app.schemas.application_form import (
    ApplicationFormInspection,
)
from app.schemas.form_mapping import (
    FormFieldMapping,
    FormFieldMappingList,
)


class FormMappingAgent:

    def __init__(self):
        self.client = OpenAI(
            api_key=settings.openai_api_key
        )

    def map_fields(
        self,
        candidate: CandidateProfile,
        inspection: ApplicationFormInspection,
        cover_letter: dict | None = None,
    ) -> list[FormFieldMapping]:

        system_prompt = """
You are a job application form mapping agent.

Your ONLY task is to determine how each discovered application
form field should be handled.

You do NOT fill the form.
You do NOT submit the form.


SOURCE OF TRUTH

Candidate Profile is the ONLY source of truth for personal,
professional, educational and technical information about
the candidate.

Approved Cover Letter is the source of truth for cover-letter
text that has already passed the application's validation and
approval pipeline.

Never invent, assume or infer missing candidate information.


CLASSIFICATION

For every form field return exactly one status:

AUTO_FILL
Use only when the requested value is explicitly supported by
Candidate Profile.

Also use AUTO_FILL for a cover-letter textarea when an
Approved Cover Letter is supplied.

When using the Approved Cover Letter for a textarea:
- Use source = "approved_cover_letter_text"
- Use only the supplied approved cover-letter content.
- Do not add new claims.
- Do not modify factual claims.

FILE_UPLOAD
Use only for actual file input fields.

For resume/CV file fields:
- source = "approved_cv"
- value = null

For cover-letter file fields:
- source = "approved_cover_letter"
- value = null

NEEDS_USER_INPUT
Use when the requested information is not explicitly available
from the allowed sources.

For NEEDS_USER_INPUT:
- source = "user_required"
- value = null

SKIP
Use only when the field should not be filled or is clearly
irrelevant/non-user-input.


SOURCE VALUES ARE STRICT

When status is AUTO_FILL, use one of these source identifiers
when applicable:

candidate.full_name
candidate.email
candidate.phone
candidate.linkedin
candidate.github
candidate.education
candidate.languages
approved_cover_letter_text

For resume/CV file upload:
approved_cv

For cover-letter file upload:
approved_cover_letter

For missing information:
user_required

Do not create alternative source names such as:
"candidate_profile"
"profile"
"candidate data"
or similar.


IMPORTANT SAFETY RULES

1. Never infer work authorization.
2. Never infer visa or sponsorship status.
3. Never infer expected salary.
4. Never infer notice period.
5. Never infer relocation willingness.
6. Never infer demographic information.
7. Never infer disability or veteran status.
8. Never infer race, ethnicity or gender.
9. Never infer availability or start date.
10. Never answer legal attestations or consent questions.
11. Never treat a job requirement as candidate information.
12. Do not invent an answer because a field is required.
13. Never calculate years of experience unless explicitly
    represented in Candidate Profile.
14. For select fields, AUTO_FILL values must correspond to
    one of the supplied options when possible.


NAME HANDLING

Do not split Candidate Profile full_name into first name and
last name unless Candidate Profile explicitly contains those
separate values.

For example:

Candidate Profile:
full_name = "Example Full Name"

Form:
First Name

If Candidate Profile does not explicitly contain first_name,
return NEEDS_USER_INPUT.

Do not guess how a person's name should be divided.


COVER LETTER HANDLING

If Approved Cover Letter is supplied and the form contains a
textarea whose purpose is clearly a cover letter:

status = "AUTO_FILL"
source = "approved_cover_letter_text"

Construct the value exclusively from the supplied Approved
Cover Letter fields.

Do not say that no cover letter exists when
approved_cover_letter is non-null.

If the form contains a FILE input for the cover letter:

status = "FILE_UPLOAD"
source = "approved_cover_letter"
value = null


Return a mapping for EVERY supplied form field.
"""

        payload = {
            "candidate_profile": candidate.model_dump(),
            "approved_cover_letter": cover_letter,
            "form": inspection.model_dump(),
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
            text_format=FormFieldMappingList,
        )

        if not response.output_parsed:
            raise RuntimeError(
                "Form Mapping Agent did not return "
                "a structured result."
            )

        mappings = response.output_parsed.mappings

        # Apply deterministic rules after the LLM mapping.
        # Clear file inputs should never depend on
        # nondeterministic LLM classification.
        mappings = self._apply_deterministic_rules(
            inspection=inspection,
            mappings=mappings,
        )

        return mappings

    def _apply_deterministic_rules(
        self,
        inspection: ApplicationFormInspection,
        mappings: list[FormFieldMapping],
    ) -> list[FormFieldMapping]:

        fields_by_index = {
            field.index: field
            for field in inspection.fields
        }

        for mapping in mappings:

            field = fields_by_index.get(
                mapping.field_index
            )

            if field is None:
                continue

            tag = (field.tag or "").lower()
            field_type = (field.type or "").lower()

            # Deterministic rules below apply only
            # to actual file inputs.
            if (
                tag != "input"
                or field_type != "file"
            ):
                continue

            searchable_text = " ".join(
                str(value)
                for value in [
                    field.name,
                    field.id,
                    field.label,
                    field.placeholder,
                ]
                if value
            ).lower()

            normalized_words = (
                searchable_text
                .replace("_", " ")
                .replace("-", " ")
                .split()
            )

            # ----------------------------------------
            # COVER LETTER FILE
            # ----------------------------------------

            is_cover_letter = (
                "cover letter" in searchable_text
                or "coverletter" in searchable_text
                or (
                    "cover" in normalized_words
                    and "letter" in normalized_words
                )
                or "ön yazı" in searchable_text
                or "önyazı" in searchable_text
                or "on yazi" in searchable_text
            )

            if is_cover_letter:

                mapping.status = "FILE_UPLOAD"
                mapping.source = (
                    "approved_cover_letter"
                )
                mapping.value = None
                mapping.reason = (
                    "Deterministic rule: "
                    "cover-letter file input uses "
                    "the approved cover letter."
                )

                continue

            # ----------------------------------------
            # RESUME / CV FILE
            # ----------------------------------------

            is_resume = (
                "resume" in searchable_text
                or "résumé" in searchable_text
                or "curriculum vitae"
                in searchable_text
                or "cv" in normalized_words
                or "özgeçmiş" in searchable_text
                or "ozgecmis" in searchable_text
            )

            if is_resume:

                mapping.status = "FILE_UPLOAD"
                mapping.source = "approved_cv"
                mapping.value = None
                mapping.reason = (
                    "Deterministic rule: "
                    "resume/CV file input uses "
                    "the approved CV."
                )

        return mappings


form_mapping_agent = FormMappingAgent()