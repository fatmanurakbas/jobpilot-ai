from pathlib import Path

from playwright.async_api import async_playwright

from app.schemas.resolved_form import ResolvedFormPlan
from app.schemas.form_fill import (
    FilledFieldResult,
    FormFillResult,
)
from app.schemas.form_verification import (
    FieldVerification,
    FormVerificationResult,
)


class ApplicationFormFiller:

    async def fill(
        self,
        plan: ResolvedFormPlan,
    ) -> FormFillResult:

        # -------------------------------------------------
        # SAFETY CHECK
        # -------------------------------------------------

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

                # -----------------------------------------
                # OPEN PAGE
                # -----------------------------------------

                await page.goto(
                    plan.url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )

                await page.wait_for_timeout(1000)

                elements = page.locator(
                    "input, textarea, select"
                )

                results: list[FilledFieldResult] = []

                filled_count = 0
                uploaded_count = 0
                failed_count = 0

                # -----------------------------------------
                # FILL FIELDS
                # -----------------------------------------

                for field in plan.fields:

                    # -------------------------------------
                    # SKIP
                    # -------------------------------------

                    if field.action == "SKIP":

                        results.append(
                            FilledFieldResult(
                                field_index=field.field_index,
                                field_name=field.field_name,
                                action="SKIP",
                                success=True,
                                message="Field skipped.",
                            )
                        )

                        continue

                    # -------------------------------------
                    # UNRESOLVED
                    # -------------------------------------

                    if field.action == "UNRESOLVED":

                        failed_count += 1

                        results.append(
                            FilledFieldResult(
                                field_index=field.field_index,
                                field_name=field.field_name,
                                action="UNRESOLVED",
                                success=False,
                                message=(
                                    "Unresolved field was "
                                    "not modified."
                                ),
                            )
                        )

                        continue

                    try:
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

                        # ---------------------------------
                        # FILE UPLOAD
                        # ---------------------------------

                        if field.action == "UPLOAD":

                            if (
                                tag != "input"
                                or input_type != "file"
                            ):
                                raise ValueError(
                                    "Target element is not "
                                    "a file input."
                                )

                            if not field.file_path:
                                raise ValueError(
                                    "Upload file path "
                                    "is missing."
                                )

                            path = Path(
                                field.file_path
                            )

                            if not path.exists():
                                raise FileNotFoundError(
                                    f"File not found: {path}"
                                )

                            await element.set_input_files(
                                str(path.resolve())
                            )

                            uploaded_count += 1

                            results.append(
                                FilledFieldResult(
                                    field_index=field.field_index,
                                    field_name=field.field_name,
                                    action="UPLOAD",
                                    success=True,
                                    message=(
                                        "File attached "
                                        "successfully."
                                    ),
                                )
                            )

                            continue

                        # ---------------------------------
                        # FILL
                        # ---------------------------------

                        if field.action == "FILL":

                            if field.value is None:
                                raise ValueError(
                                    "Field value is missing."
                                )

                            # -----------------------------
                            # SELECT
                            # -----------------------------

                            if tag == "select":

                                try:
                                    await element.select_option(
                                        value=field.value
                                    )

                                except Exception:
                                    await element.select_option(
                                        label=field.value
                                    )

                            # -----------------------------
                            # INPUT / TEXTAREA
                            # -----------------------------

                            else:
                                await element.fill(
                                    field.value
                                )

                            filled_count += 1

                            results.append(
                                FilledFieldResult(
                                    field_index=field.field_index,
                                    field_name=field.field_name,
                                    action="FILL",
                                    success=True,
                                    message=(
                                        "Field filled "
                                        "successfully."
                                    ),
                                )
                            )

                    except Exception as exc:

                        failed_count += 1

                        results.append(
                            FilledFieldResult(
                                field_index=field.field_index,
                                field_name=field.field_name,
                                action=field.action,
                                success=False,
                                message=str(exc),
                            )
                        )

                # =========================================
                # SCREENSHOT
                # =========================================
                #
                # Form doldurulduktan sonra,
                # browser kapanmadan önce screenshot alıyoruz.
                #

                screenshot_dir = (
                    Path("generated")
                    / f"application_{plan.application_id}"
                )

                screenshot_dir.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                screenshot_path = (
                    screenshot_dir
                    / "filled_application_form.png"
                )

                await page.screenshot(
                    path=str(screenshot_path),
                    full_page=True,
                )

                # =========================================
                # VERIFY FILLED VALUES
                # =========================================
                #
                # Formu doldurduktan sonra DOM'dan tekrar
                # okuyarak değerlerin gerçekten yazıldığını
                # kontrol ediyoruz.
                #

                verification = await self._verify_fields(
                    page=page,
                    plan=plan,
                )

                verification.screenshot_path = str(
                    screenshot_path
                )

                # =========================================
                # FINAL RESULT
                # =========================================

                overall_success = (
                    failed_count == 0
                    and verification.verified
                )

                return FormFillResult(
                    application_id=plan.application_id,
                    url=page.url,
                    success=overall_success,
                    filled_count=filled_count,
                    uploaded_count=uploaded_count,
                    failed_count=failed_count,

                    # IMPORTANT:
                    # This service NEVER submits the form.
                    submitted=False,

                    results=results,
                    verification=verification,

                    message=(
                        "Form filled and verified "
                        "successfully without submission."
                        if overall_success
                        else
                        "Form filling or verification "
                        "failed. The form was not submitted."
                    ),
                )

            finally:

                # Browser only closes AFTER:
                #
                # 1. filling
                # 2. screenshot
                # 3. verification
                #
                # are completed.

                await browser.close()

    # =====================================================
    # VERIFY FORM
    # =====================================================

    async def _verify_fields(
        self,
        page,
        plan: ResolvedFormPlan,
    ) -> FormVerificationResult:

        elements = page.locator(
            "input, textarea, select"
        )

        verifications: list[
            FieldVerification
        ] = []

        for field in plan.fields:

            # SKIP fields do not need verification.

            if field.action == "SKIP":
                continue

            # UNRESOLVED fields should never reach
            # the fill stage, but we ignore them here.

            if field.action == "UNRESOLVED":
                continue

            try:
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

                # -----------------------------------------
                # VERIFY FILE UPLOAD
                # -----------------------------------------

                if field.action == "UPLOAD":

                    if (
                        tag != "input"
                        or input_type != "file"
                    ):
                        raise ValueError(
                            "Target is not a file input."
                        )

                    file_count = await element.evaluate(
                        """
                        (el) =>
                            el.files
                                ? el.files.length
                                : 0
                        """
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

                    verified = (
                        file_count > 0
                        and actual_filename
                        == expected_filename
                    )

                    verifications.append(
                        FieldVerification(
                            field_index=field.field_index,
                            field_name=field.field_name,
                            action="UPLOAD",
                            verified=verified,
                            expected_value=expected_filename,
                            actual_value=actual_filename,
                            message=(
                                "Uploaded file verified."
                                if verified
                                else
                                "Uploaded file "
                                "verification failed."
                            ),
                        )
                    )

                    continue

                # -----------------------------------------
                # VERIFY FILLED VALUE
                # -----------------------------------------

                if field.action == "FILL":

                    actual_value = (
                        await element.input_value()
                    )

                    expected_value = (
                        field.value
                        if field.value is not None
                        else ""
                    )

                    # -------------------------------------
                    # SELECT
                    # -------------------------------------

                    if tag == "select":

                        selected_text = (
                            await element.locator(
                                "option:checked"
                            ).text_content()
                        )

                        selected_text = (
                            selected_text.strip()
                            if selected_text
                            else None
                        )

                        # Some forms use:
                        #
                        # value="yes"
                        #
                        # while displaying:
                        #
                        # Yes
                        #
                        # Therefore compare both value
                        # and visible label.

                        verified = (
                            actual_value
                            == expected_value
                            or selected_text
                            == expected_value
                            or (
                                selected_text
                                and selected_text.lower()
                                == expected_value.lower()
                            )
                            or (
                                actual_value
                                and actual_value.lower()
                                == expected_value.lower()
                            )
                        )

                        displayed_actual = (
                            selected_text
                            or actual_value
                        )

                    # -------------------------------------
                    # INPUT / TEXTAREA
                    # -------------------------------------

                    else:

                        verified = (
                            actual_value
                            == expected_value
                        )

                        displayed_actual = (
                            actual_value
                        )

                    verifications.append(
                        FieldVerification(
                            field_index=field.field_index,
                            field_name=field.field_name,
                            action="FILL",
                            verified=verified,
                            expected_value=expected_value,
                            actual_value=displayed_actual,
                            message=(
                                "Field value verified."
                                if verified
                                else
                                "Field value does not match."
                            ),
                        )
                    )

            except Exception as exc:

                verifications.append(
                    FieldVerification(
                        field_index=field.field_index,
                        field_name=field.field_name,
                        action=field.action,
                        verified=False,
                        expected_value=(
                            field.value
                            if field.action == "FILL"
                            else (
                                Path(field.file_path).name
                                if field.file_path
                                else None
                            )
                        ),
                        actual_value=None,
                        message=str(exc),
                    )
                )

        # ---------------------------------------------
        # COUNTS
        # ---------------------------------------------

        verified_count = sum(
            1
            for item in verifications
            if item.verified
        )

        failed_count = sum(
            1
            for item in verifications
            if not item.verified
        )

        return FormVerificationResult(
            verified=(
                failed_count == 0
            ),
            verified_count=verified_count,
            failed_count=failed_count,
            fields=verifications,
        )


application_form_filler = ApplicationFormFiller()