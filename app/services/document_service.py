from io import BytesIO
from pathlib import Path

from docx import Document
from pypdf import PdfReader


class DocumentService:

    def extract_text(
        self,
        filename: str,
        file_bytes: bytes,
    ) -> str:

        extension = Path(
            filename
        ).suffix.lower()

        if extension == ".pdf":
            return self.extract_pdf_text(
                file_bytes
            )

        if extension == ".docx":
            return self.extract_docx_text(
                file_bytes
            )

        raise ValueError(
            "Unsupported file type. "
            "Only PDF and DOCX are supported."
        )

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------

    def extract_pdf_text(
        self,
        file_bytes: bytes,
    ) -> str:

        reader = PdfReader(
            BytesIO(file_bytes)
        )

        content = []
        discovered_urls = []

        for page in reader.pages:

            # Normal visible text
            text = page.extract_text()

            if text:
                content.append(text)

            # PDF hyperlinks / annotations
            annotations = page.get(
                "/Annots"
            )

            if not annotations:
                continue

            for annotation_ref in annotations:

                try:
                    annotation = (
                        annotation_ref.get_object()
                    )

                    if annotation.get(
                        "/Subtype"
                    ) != "/Link":
                        continue

                    action = annotation.get(
                        "/A"
                    )

                    if not action:
                        continue

                    uri = action.get(
                        "/URI"
                    )

                    if not uri:
                        continue

                    url = str(uri).strip()

                    if (
                        self._is_web_url(url)
                        and url not in discovered_urls
                    ):
                        discovered_urls.append(
                            url
                        )

                except Exception:
                    # A broken annotation should not
                    # prevent the CV from being parsed.
                    continue

        # Give the parser explicit access to URLs
        if discovered_urls:

            content.append(
                "\nDOCUMENT LINKS:"
            )

            content.extend(
                discovered_urls
            )

        return "\n".join(
            content
        ).strip()

    # ---------------------------------------------------------
    # DOCX
    # ---------------------------------------------------------

    def extract_docx_text(
        self,
        file_bytes: bytes,
    ) -> str:

        document = Document(
            BytesIO(file_bytes)
        )

        content = []
        discovered_urls = []

        for paragraph in document.paragraphs:

            text = paragraph.text.strip()

            if text:
                content.append(text)

            # Extract actual URLs from hyperlinks
            hyperlinks = paragraph._p.xpath(
                ".//w:hyperlink"
            )

            for hyperlink in hyperlinks:

                relationship_id = hyperlink.get(
                    (
                        "{http://schemas.openxmlformats.org/"
                        "officeDocument/2006/"
                        "relationships}id"
                    )
                )

                if not relationship_id:
                    continue

                relationship = (
                    document.part.rels.get(
                        relationship_id
                    )
                )

                if not relationship:
                    continue

                url = (
                    relationship.target_ref
                )

                if (
                    self._is_web_url(url)
                    and url not in discovered_urls
                ):
                    discovered_urls.append(
                        url
                    )

        if discovered_urls:

            content.append(
                "\nDOCUMENT LINKS:"
            )

            content.extend(
                discovered_urls
            )

        return "\n".join(
            content
        ).strip()

    # ---------------------------------------------------------
    # URL VALIDATION
    # ---------------------------------------------------------

    def _is_web_url(
        self,
        value: str | None,
    ) -> bool:

        if not value:
            return False

        value = value.strip().lower()

        return (
            value.startswith("http://")
            or value.startswith("https://")
        )


document_service = DocumentService()