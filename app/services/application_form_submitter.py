from pathlib import Path
from datetime import datetime, timezone
import re

from playwright.async_api import async_playwright

from app.schemas.resolved_form import ResolvedFormPlan
from app.schemas.form_submission import (
    FormSubmissionResult,
)


class ApplicationFormSubmitter:

    async def submit(
        self,
        plan: ResolvedFormPlan,
    ) -> FormSubmissionResult:

        # -----------------------------------------
        # 1. Plan submit için hazır mı?
        # -----------------------------------------

        if not plan.ready_to_fill:
            raise ValueError(
                "Form plan contains unresolved fields."
            )

        async with async_playwright() as playwright:

            browser = await playwright.chromium.launch(
                headless=True
            )

            try:
                page = await browser.new_page()

                # ---------------------------------
                # 2. Başvuru sayfasını aç
                # ---------------------------------

                await page.goto(
                    plan.url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )

                await page.wait_for_timeout(1000)

                elements = page.locator(
                    "input, textarea, select"
                )

                # ---------------------------------
                # 3. Formu yeniden doldur
                # ---------------------------------

                for field in plan.fields:

                    if field.action == "SKIP":
                        continue

                    if field.action == "UNRESOLVED":
                        raise ValueError(
                            "Unresolved field: "
                            f"{field.field_name}"
                        )

                    element = elements.nth(
                        field.field_index
                    )

                    tag = await element.evaluate(
                        """
                        (el) =>
                            el.tagName.toLowerCase()
                        """
                    )

                    input_type = (
                        await element.get_attribute(
                            "type"
                        )
                    )

                    # -----------------------------
                    # FILE UPLOAD
                    # -----------------------------

                    if field.action == "UPLOAD":

                        if (
                            tag != "input"
                            or input_type != "file"
                        ):
                            raise ValueError(
                                "Upload target is not "
                                "a file input: "
                                f"{field.field_name}"
                            )

                        if not field.file_path:
                            raise ValueError(
                                "Upload file path missing: "
                                f"{field.field_name}"
                            )

                        file_path = Path(
                            field.file_path
                        )

                        if not file_path.exists():
                            raise FileNotFoundError(
                                "Upload file not found: "
                                f"{file_path}"
                            )

                        await element.set_input_files(
                            str(file_path.resolve())
                        )

                        continue

                    # -----------------------------
                    # NORMAL FIELD
                    # -----------------------------

                    if field.action == "FILL":

                        if field.value is None:
                            raise ValueError(
                                "Field value missing: "
                                f"{field.field_name}"
                            )

                        # SELECT
                        if tag == "select":

                            try:
                                await element.select_option(
                                    value=field.value
                                )

                            except Exception:
                                await element.select_option(
                                    label=field.value
                                )

                        # INPUT / TEXTAREA
                        else:
                            await element.fill(
                                field.value
                            )

                # ---------------------------------
                # 4. Alanları yeniden doğrula
                # ---------------------------------

                for field in plan.fields:

                    if field.action in {
                        "SKIP",
                        "UNRESOLVED",
                    }:
                        continue

                    element = elements.nth(
                        field.field_index
                    )

                    tag = await element.evaluate(
                        """
                        (el) =>
                            el.tagName.toLowerCase()
                        """
                    )

                    input_type = (
                        await element.get_attribute(
                            "type"
                        )
                    )

                    # -----------------------------
                    # UPLOAD VERIFICATION
                    # -----------------------------

                    if field.action == "UPLOAD":

                        if (
                            tag != "input"
                            or input_type != "file"
                        ):
                            raise ValueError(
                                "Upload verification target "
                                "is not a file input: "
                                f"{field.field_name}"
                            )

                        file_count = (
                            await element.evaluate(
                                """
                                (el) =>
                                    el.files
                                        ? el.files.length
                                        : 0
                                """
                            )
                        )

                        if file_count < 1:
                            raise ValueError(
                                "File verification failed: "
                                f"{field.field_name}"
                            )

                        actual_filename = (
                            await element.evaluate(
                                """
                                (el) =>
                                    el.files &&
                                    el.files.length > 0
                                        ? el.files[0].name
                                        : null
                                """
                            )
                        )

                        expected_filename = (
                            Path(
                                field.file_path
                            ).name
                            if field.file_path
                            else None
                        )

                        if (
                            actual_filename
                            != expected_filename
                        ):
                            raise ValueError(
                                "Uploaded file does not "
                                "match expected file: "
                                f"{field.field_name}"
                            )

                        continue

                    # -----------------------------
                    # VALUE VERIFICATION
                    # -----------------------------

                    if field.action == "FILL":

                        actual_value = (
                            await element.input_value()
                        )

                        expected_value = (
                            field.value or ""
                        )

                        # SELECT
                        if tag == "select":

                            selected_text = (
                                await element.locator(
                                    "option:checked"
                                ).text_content()
                            )

                            selected_text = (
                                selected_text.strip()
                                if selected_text
                                else ""
                            )

                            actual_normalized = (
                                actual_value
                                .strip()
                                .lower()
                            )

                            selected_normalized = (
                                selected_text
                                .strip()
                                .lower()
                            )

                            expected_normalized = (
                                expected_value
                                .strip()
                                .lower()
                            )

                            matches = (
                                actual_normalized
                                == expected_normalized
                                or selected_normalized
                                == expected_normalized
                            )

                        else:
                            matches = (
                                actual_value
                                == expected_value
                            )

                        if not matches:
                            raise ValueError(
                                "Field verification failed: "
                                f"{field.field_name}"
                            )

                # ---------------------------------
                # 5. Submit butonunu bul
                # ---------------------------------

                submit_button = page.locator(
                    'button[type="submit"], '
                    'input[type="submit"]'
                ).first

                if await submit_button.count() == 0:
                    raise ValueError(
                        "Submit button not found."
                    )

                if not await submit_button.is_visible():
                    raise ValueError(
                        "Submit button is not visible."
                    )

                if not await submit_button.is_enabled():
                    raise ValueError(
                        "Submit button is disabled."
                    )

                # ---------------------------------
                # 6. GERÇEK SUBMIT
                # ---------------------------------

                await submit_button.click()

                # ---------------------------------
                # 7. Başarı sinyalini bekle
                # ---------------------------------

                await page.wait_for_timeout(5000)
                evidence_selector = page.locator(
                    '#submission-success, [data-testid*="success" i], '
                    '[role="alert"], [aria-live="polite"]'
                )
                candidates = []
                for index in range(min(await evidence_selector.count(), 30)):
                    item = evidence_selector.nth(index)
                    if await item.is_visible():
                        text = (await item.inner_text()).strip()
                        if text:
                            candidates.append(text)
                confirmation_text = None
                confirmation_pattern = re.compile(
                    r"\b(thank you for applying|thank you for your application|"
                    r"application (was )?submitted|"
                    r"successfully submitted|submission (is )?complete|"
                    r"we (have )?received your application|"
                    r"application received|your application is complete)\b",
                    re.IGNORECASE,
                )
                for text in candidates:
                    if confirmation_pattern.search(text):
                        confirmation_text = text[:2000]
                        break

                screenshot_dir = Path("generated") / f"application_{plan.application_id}"
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                screenshot_path = screenshot_dir / "submission_confirmation.png"
                await page.screenshot(path=str(screenshot_path), full_page=True)

                confirmed = bool(confirmation_text)
                return FormSubmissionResult(
                    application_id=plan.application_id,
                    success=confirmed,
                    submitted=confirmed,
                    status="SUBMITTED" if confirmed else "SUBMISSION_UNCONFIRMED",
                    final_url=page.url,
                    confirmation=confirmation_text,
                    submitted_at=datetime.now(timezone.utc).isoformat() if confirmed else None,
                    screenshot_available=screenshot_path.exists(),
                    message=(
                        "Platform confirmation detected after submission."
                        if confirmed
                        else "Submit action was triggered, but reliable platform confirmation was not detected. Do not retry automatically."
                    ),
                )

            finally:

                # Hata olsa bile browser kapanır.
                await browser.close()


application_form_submitter = (
    ApplicationFormSubmitter()
)
