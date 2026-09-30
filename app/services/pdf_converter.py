from pathlib import Path
import shutil
import subprocess


class PDFConverter:

    def convert_docx_to_pdf(
        self,
        docx_path: str,
    ) -> str:

        source = Path(docx_path)

        if not source.exists():
            raise FileNotFoundError(
                f"DOCX file not found: {source}"
            )

        output_dir = source.parent

        # Docker/Linux environment
        libreoffice = shutil.which("libreoffice")

        # Some installations expose LibreOffice as "soffice"
        if not libreoffice:
            libreoffice = shutil.which("soffice")

        if not libreoffice:
            raise RuntimeError(
                "LibreOffice is not installed "
                "or is not available in PATH."
            )

        result = subprocess.run(
            [
                libreoffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(output_dir),
                str(source),
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )

        pdf_path = source.with_suffix(".pdf")

        if result.returncode != 0:
            raise RuntimeError(
                "LibreOffice PDF conversion failed. "
                f"stdout={result.stdout} "
                f"stderr={result.stderr}"
            )

        if not pdf_path.exists():
            raise RuntimeError(
                "LibreOffice completed but PDF file "
                f"was not created: {pdf_path}"
            )

        return str(pdf_path)


pdf_converter = PDFConverter()