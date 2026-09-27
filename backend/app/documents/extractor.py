from pathlib import Path

from docling.document_converter import DocumentConverter


converter = DocumentConverter()


def extract_pdf_text(file_path: str) -> str:
    """
    Extract text from a PDF using Docling.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    result = converter.convert(str(path))

    document = result.document

    return document.export_to_markdown()