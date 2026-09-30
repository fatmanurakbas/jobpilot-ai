from app.schemas.candidate_profile import CandidateProfile
from app.schemas.form_mapping import FormFieldMapping
from app.schemas.resolved_form import ResolvedFormField


class FormValueResolver:

    def resolve(
        self,
        mapping: FormFieldMapping,
        candidate: CandidateProfile,
        application,
    ) -> ResolvedFormField:

        source = mapping.source

        # ---------------------------------------------
        # SKIP
        # ---------------------------------------------

        if mapping.status == "SKIP":
            return ResolvedFormField(
                field_index=mapping.field_index,
                field_name=mapping.field_name,
                field_label=mapping.field_label,
                action="SKIP",
                resolved_from=source,
                reason="Mapping agent marked this field as SKIP.",
            )

        # ---------------------------------------------
        # CANDIDATE VALUES
        # ---------------------------------------------

        candidate_sources = {
            "candidate.full_name": "full_name",
            "candidate.email": "email",
            "candidate.phone": "phone",
            "candidate.linkedin": "linkedin",
            "candidate.github": "github",
        }

        if source in candidate_sources:
            attribute = candidate_sources[source]

            value = getattr(
                candidate,
                attribute,
                None,
            )

            if value:
                return ResolvedFormField(
                    field_index=mapping.field_index,
                    field_name=mapping.field_name,
                    field_label=mapping.field_label,
                    action="FILL",
                    value=str(value),
                    resolved_from=source,
                    reason=(
                        "Value resolved directly from "
                        "CandidateProfile."
                    ),
                )

            return self._unresolved(
                mapping,
                reason=(
                    f"{source} is not available "
                    "in CandidateProfile."
                ),
            )

        # ---------------------------------------------
        # APPROVED CV
        # ---------------------------------------------

        if source == "approved_cv":

            if application.pdf_path:
                return ResolvedFormField(
                    field_index=mapping.field_index,
                    field_name=mapping.field_name,
                    field_label=mapping.field_label,
                    action="UPLOAD",
                    file_path=application.pdf_path,
                    resolved_from="approved_cv",
                    reason="Using approved CV PDF.",
                )

            return self._unresolved(
                mapping,
                reason="Approved CV PDF is unavailable.",
            )

        # ---------------------------------------------
        # APPROVED COVER LETTER FILE
        # ---------------------------------------------

        if source == "approved_cover_letter":

            if application.cover_letter_pdf_path:
                return ResolvedFormField(
                    field_index=mapping.field_index,
                    field_name=mapping.field_name,
                    field_label=mapping.field_label,
                    action="UPLOAD",
                    file_path=(
                        application.cover_letter_pdf_path
                    ),
                    resolved_from="approved_cover_letter",
                    reason=(
                        "Using approved cover letter PDF."
                    ),
                )

            return self._unresolved(
                mapping,
                reason=(
                    "Approved cover letter PDF "
                    "is unavailable."
                ),
            )

        # ---------------------------------------------
        # APPROVED COVER LETTER TEXT
        # ---------------------------------------------

        if source == "approved_cover_letter_text":

            text = self._build_cover_letter_text(
                application.cover_letter_data
            )

            if text:
                return ResolvedFormField(
                    field_index=mapping.field_index,
                    field_name=mapping.field_name,
                    field_label=mapping.field_label,
                    action="FILL",
                    value=text,
                    resolved_from=(
                        "approved_cover_letter_text"
                    ),
                    reason=(
                        "Cover letter text reconstructed "
                        "from approved stored data."
                    ),
                )

            return self._unresolved(
                mapping,
                reason=(
                    "Approved cover letter text "
                    "is unavailable."
                ),
            )

        # ---------------------------------------------
        # USER-PROVIDED ANSWERS
        # ---------------------------------------------

        if source == "user_required":

            answers = application.form_answers or {}

            field_name = mapping.field_name

            if (
                field_name
                and field_name in answers
                and str(answers[field_name]).strip()
            ):
                return ResolvedFormField(
                    field_index=mapping.field_index,
                    field_name=mapping.field_name,
                    field_label=mapping.field_label,
                    action="FILL",
                    value=str(
                        answers[field_name]
                    ).strip(),
                    resolved_from=(
                        f"form_answers.{field_name}"
                    ),
                    reason=(
                        "Value supplied explicitly "
                        "by the user."
                    ),
                )

            return self._unresolved(
                mapping,
                reason=(
                    "This field requires an explicit "
                    "user-provided answer."
                ),
            )

        # ---------------------------------------------
        # UNKNOWN SOURCE
        # ---------------------------------------------

        return self._unresolved(
            mapping,
            reason=(
                f"Unsupported mapping source: {source}"
            ),
        )

    # -------------------------------------------------
    # UNRESOLVED HELPER
    # -------------------------------------------------

    def _unresolved(
        self,
        mapping: FormFieldMapping,
        reason: str,
    ) -> ResolvedFormField:

        return ResolvedFormField(
            field_index=mapping.field_index,
            field_name=mapping.field_name,
            field_label=mapping.field_label,
            action="UNRESOLVED",
            resolved_from=mapping.source,
            reason=reason,
        )

    # -------------------------------------------------
    # COVER LETTER TEXT
    # -------------------------------------------------

    def _build_cover_letter_text(
        self,
        data: dict | None,
    ) -> str | None:

        if not data:
            return None

        parts: list[str] = []

        greeting = data.get("greeting")
        opening = data.get("opening")
        body_paragraphs = (
            data.get("body_paragraphs") or []
        )
        closing = data.get("closing")
        sign_off = data.get("sign_off")
        candidate_name = data.get("candidate_name")

        if greeting:
            parts.append(str(greeting).strip())

        if opening:
            parts.append(str(opening).strip())

        for paragraph in body_paragraphs:
            if paragraph:
                parts.append(str(paragraph).strip())

        if closing:
            parts.append(str(closing).strip())

        signature_parts = []

        if sign_off:
            signature_parts.append(
                str(sign_off).strip()
            )

        if candidate_name:
            signature_parts.append(
                str(candidate_name).strip()
            )

        if signature_parts:
            parts.append(
                "\n".join(signature_parts)
            )

        if not parts:
            return None

        return "\n\n".join(parts)


form_value_resolver = FormValueResolver()