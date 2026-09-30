import hashlib
import json

from pathlib import Path

from app.services.file_hash_service import (
    file_hash_service,
)


class SubmissionHashService:

    def create_hash(
        self,
        *,
        application,
        url: str,
    ) -> str:

        if not application.pdf_path:
            raise ValueError(
                "CV PDF is unavailable."
            )

        if not application.cover_letter_pdf_path:
            raise ValueError(
                "Cover letter PDF is unavailable."
            )

        # CV hash
        cv_hash = file_hash_service.sha256(
            application.pdf_path
        )

        # Cover Letter hash
        cover_letter_hash = (
            file_hash_service.sha256(
                application.cover_letter_pdf_path
            )
        )

        # Form cevapları
        form_answers = (
            application.form_answers or {}
        )

        # Kullanıcının gördüğü form screenshot'ı
        screenshot_path = (
            Path("generated")
            / f"application_{application.id}"
            / "filled_application_form.png"
        )

        if not screenshot_path.exists():
            raise FileNotFoundError(
                "Filled form screenshot not found."
            )

        screenshot_hash = (
            file_hash_service.sha256(
                str(screenshot_path)
            )
        )

        # Final approval payload
        payload = {
            "application_id": application.id,
            "candidate_id": application.candidate_id,
            "job_id": application.job_id,
            "url": url,
            "cv_hash": cv_hash,
            "cover_letter_hash": cover_letter_hash,
            "form_answers": form_answers,
            "screenshot_hash": screenshot_hash,
        }

        # Her zaman aynı JSON sıralamasını üret
        canonical_json = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

        # Final SHA-256
        return hashlib.sha256(
            canonical_json.encode("utf-8")
        ).hexdigest()


submission_hash_service = SubmissionHashService()