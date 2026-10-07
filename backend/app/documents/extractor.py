import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_CONVERTER_INSTANCE = None


def get_converter():
    """
    Lazy-load DocumentConverter with OCR explicitly disabled.
    This prevents RapidOCR/Tesseract/Torch vision models from loading into RAM,
    ensuring memory fits well within the 512MB target.
    """
    global _CONVERTER_INSTANCE
    if _CONVERTER_INSTANCE is None:
        try:
            from docling.document_converter import DocumentConverter, PdfFormatOption
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions

            pipeline_options = PdfPipelineOptions(do_ocr=False)
            _CONVERTER_INSTANCE = DocumentConverter(
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
            logger.info("[DOCLING] DocumentConverter initialized with do_ocr=False (No OCR pipeline).")
        except Exception as exc:
            logger.error(f"[DOCLING] Failed to initialize converter with do_ocr=False: {exc}")
            from docling.document_converter import DocumentConverter
            _CONVERTER_INSTANCE = DocumentConverter()

    return _CONVERTER_INSTANCE


def extract_pdf_text(file_path: str) -> str:
    """
    Extract structured text from a PDF using Docling without OCR.
    Runs once per analysis.
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"PDF file not found: {file_path}"
        )

    converter = get_converter()
    result = converter.convert(str(path))
    document = result.document

    return document.export_to_markdown()