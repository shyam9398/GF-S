from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.documents.extractor import extract_pdf_text
from app.models.analysis import ProcurementAnalysis
from app.models.document import ProcurementDocument
from app.schemas.document import DocumentResponse


router = APIRouter()

# ------------------------------------------------------------------
# Upload configuration
# ------------------------------------------------------------------

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB


# ------------------------------------------------------------------
# Upload Procurement PDF
# ------------------------------------------------------------------

@router.post(
    "/{analysis_id}/upload",
    response_model=DocumentResponse,
)
async def upload_document(
    analysis_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------------
    # 1. Check whether analysis exists
    # --------------------------------------------------------------

    analysis = db.get(
        ProcurementAnalysis,
        analysis_id,
    )

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found",
        )

    # --------------------------------------------------------------
    # 2. Validate filename
    # --------------------------------------------------------------

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    original_filename = Path(
        file.filename
    ).name

    if not original_filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    # --------------------------------------------------------------
    # 3. Validate PDF
    # --------------------------------------------------------------

    is_pdf_extension = (
        original_filename
        .lower()
        .endswith(".pdf")
    )

    is_pdf_content_type = (
        file.content_type == "application/pdf"
    )

    if not is_pdf_extension:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    # Some clients may provide an empty or unusual MIME type.
    # The .pdf extension is therefore also checked.
    if (
        file.content_type
        and not is_pdf_content_type
    ):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file must be a PDF document",
        )

    # --------------------------------------------------------------
    # 4. Read uploaded file
    # --------------------------------------------------------------

    content = await file.read()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Uploaded PDF is empty",
        )

    # --------------------------------------------------------------
    # 5. Enforce backend file-size limit
    # --------------------------------------------------------------

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="PDF file size must not exceed 25 MB",
        )

    # --------------------------------------------------------------
    # 6. Generate unique document ID
    # --------------------------------------------------------------

    document_id = str(
        uuid.uuid4()
    )

    safe_filename = (
        f"{document_id}_{original_filename}"
    )

    file_path = (
        UPLOAD_DIR /
        safe_filename
    )

    # --------------------------------------------------------------
    # 7. Save uploaded PDF
    # --------------------------------------------------------------

    try:
        file_path.write_bytes(
            content
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to save the uploaded PDF: "
                f"{str(error)}"
            ),
        )

    # --------------------------------------------------------------
    # 8. Extract PDF text using Docling
    # --------------------------------------------------------------

    try:
        extracted_text = extract_pdf_text(
            str(file_path)
        )

    except Exception as error:
        # Keep the PDF for debugging/reprocessing.
        raise HTTPException(
            status_code=500,
            detail=(
                "PDF uploaded successfully, "
                "but text extraction failed: "
                f"{str(error)}"
            ),
        )

    # --------------------------------------------------------------
    # 9. Validate extracted content
    # --------------------------------------------------------------

    if not extracted_text:
        extracted_text = ""

    # --------------------------------------------------------------
    # 10. Store document metadata and extracted text
    # --------------------------------------------------------------

    document = ProcurementDocument(
        id=document_id,
        analysis_id=analysis_id,
        filename=original_filename,
        content_type="application/pdf",
        file_path=str(file_path),
        extracted_text=extracted_text,
        status="EXTRACTED",
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "PDF was processed, but the document "
                "record could not be saved: "
                f"{str(error)}"
            ),
        )

    # --------------------------------------------------------------
    # 11. Return document
    # --------------------------------------------------------------

    return document