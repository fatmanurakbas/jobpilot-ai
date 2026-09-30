from playwright.async_api import async_playwright

from app.schemas.application_form import (
    ApplicationFormField,
    ApplicationFormInspection,
    ApplicationFormOption,
)


class ApplicationFormInspector:

    async def inspect(
        self,
        url: str,
    ) -> ApplicationFormInspection:

        async with async_playwright() as playwright:

            browser = await playwright.chromium.launch(
                headless=True
            )

            try:
                page = await browser.new_page()

                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=30_000,
                )

                # Give JS-rendered forms a short opportunity
                # to appear.
                await page.wait_for_timeout(1500)

                title = await page.title()
                final_url = page.url

                elements = page.locator(
                    "input, textarea, select"
                )

                count = await elements.count()

                fields: list[ApplicationFormField] = []

                for index in range(count):

                    element = elements.nth(index)

                    tag = await element.evaluate(
                        "(el) => el.tagName.toLowerCase()"
                    )

                    field_type = await element.get_attribute(
                        "type"
                    )

                    # textarea/select do not normally have
                    # a useful type attribute.
                    if not field_type:
                        field_type = tag

                    field_id = await element.get_attribute("id")
                    name = await element.get_attribute("name")

                    placeholder = await element.get_attribute(
                        "placeholder"
                    )

                    accept = await element.get_attribute(
                        "accept"
                    )

                    required = await element.evaluate(
                        "(el) => el.required === true"
                    )

                    disabled = await element.is_disabled()

                    readonly = await element.evaluate(
                        "(el) => el.readOnly === true"
                    )

                    # -----------------------------------------
                    # LABEL DISCOVERY
                    # -----------------------------------------

                    label = None

                    if field_id:
                        label_locator = page.locator(
                            f'label[for="{field_id}"]'
                        )

                        if await label_locator.count() > 0:
                            label = (
                                await label_locator.first.inner_text()
                            ).strip()

                    # Input wrapped by <label>...</label>
                    if not label:
                        label = await element.evaluate(
                            """
                            (el) => {
                                const parent =
                                    el.closest("label");

                                if (!parent) {
                                    return null;
                                }

                                return parent.innerText.trim();
                            }
                            """
                        )

                    # Accessibility fallback
                    if not label:
                        label = await element.get_attribute(
                            "aria-label"
                        )

                    if not label:
                        labelled_by = (
                            await element.get_attribute(
                                "aria-labelledby"
                            )
                        )

                        if labelled_by:
                            label = await page.evaluate(
                                """
                                (id) => {
                                    const node =
                                        document.getElementById(id);

                                    return node
                                        ? node.innerText.trim()
                                        : null;
                                }
                                """,
                                labelled_by,
                            )

                    # -----------------------------------------
                    # SELECT OPTIONS
                    # -----------------------------------------

                    options: list[
                        ApplicationFormOption
                    ] = []

                    if tag == "select":

                        option_elements = element.locator(
                            "option"
                        )

                        option_count = (
                            await option_elements.count()
                        )

                        for option_index in range(
                            option_count
                        ):

                            option = option_elements.nth(
                                option_index
                            )

                            options.append(
                                ApplicationFormOption(
                                    value=(
                                        await option.get_attribute(
                                            "value"
                                        )
                                    ),
                                    text=(
                                        await option.inner_text()
                                    ).strip(),
                                )
                            )

                    fields.append(
                        ApplicationFormField(
                            index=index,
                            tag=tag,
                            type=field_type,
                            name=name,
                            id=field_id,
                            label=label,
                            placeholder=placeholder,
                            required=required,
                            disabled=disabled,
                            readonly=readonly,
                            accept=accept,
                            options=options,
                        )
                    )

                return ApplicationFormInspection(
                    url=url,
                    final_url=final_url,
                    page_title=title,
                    fields=fields,
                    field_count=len(fields),
                )

            finally:
                await browser.close()


application_form_inspector = (
    ApplicationFormInspector()
)