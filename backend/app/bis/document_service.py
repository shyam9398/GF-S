from pathlib import Path
from typing import Any

import httpx
from app.documents.extractor import get_converter


class BISDocumentService:
    """
    Downloads and extracts text from BIS-hosted documents.

    BIS API responses provide document paths such as:

        BisProd/bisProd/Standard_Review/Standard_Summary/....

    This service converts those paths into BIS document URLs,
    downloads the documents, and extracts their content.

    The service does not generate or modify BIS content.
    """

    BIS_DOCUMENT_BASE_URL = (
        "https://standards.bis.gov.in/"
    )

    def __init__(
        self,
        download_directory: str = "bis_documents",
        timeout: float = 60.0,
    ):
        self.download_directory = Path(
            download_directory
        )

        self.download_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        )

    # =========================================================
    # BUILD BIS DOCUMENT URL
    # =========================================================

    def build_document_url(
        self,
        file_path: str,
    ) -> str | None:

        if not file_path:
            return None

        normalized_path = (
            str(file_path)
            .replace("\\/", "/")
            .lstrip("/")
        )

        return (
            self.BIS_DOCUMENT_BASE_URL
            + normalized_path
        )

    # =========================================================
    # DOWNLOAD BIS DOCUMENT
    # =========================================================

    async def download_document(
        self,
        file_path: str,
        file_name: str | None = None,
    ) -> Path | None:

        document_url = self.build_document_url(
            file_path
        )

        if not document_url:
            return None

        if not file_name:
            file_name = Path(
                file_path
            ).name

        safe_file_name = (
            Path(file_name).name
        )

        destination = (
            self.download_directory
            / safe_file_name
        )

        response = await self.client.get(
            document_url
        )

        response.raise_for_status()

        content_type = (
            response.headers.get(
                "content-type",
                "",
            ).lower()
        )

        content = response.content

        if not content:
            return None

        # -----------------------------------------------------
        # BASIC PDF VALIDATION
        # -----------------------------------------------------

        if (
            not content.startswith(b"%PDF")
            and "pdf" not in content_type
        ):
            raise ValueError(
                "BIS document response does not "
                "appear to be a PDF."
            )

        destination.write_bytes(
            content
        )

        return destination

    # =========================================================
    # EXTRACT DOCUMENT TEXT
    # =========================================================

    def extract_text(
        self,
        document_path: Path,
    ) -> str:

        if not document_path.exists():
            raise FileNotFoundError(
                f"Document not found: "
                f"{document_path}"
            )

        converter = get_converter()
        result = converter.convert(
            str(document_path)
        )

        document = result.document

        markdown = document.export_to_markdown()

        if not markdown:
            return ""

        return markdown.strip()

    # =========================================================
    # DOWNLOAD + EXTRACT
    # =========================================================

    async def fetch_and_extract(
        self,
        file_path: str,
        file_name: str | None = None,
    ) -> dict[str, Any]:

        document_url = self.build_document_url(
            file_path
        )

        if not document_url:
            return {
                "success": False,
                "file_path": file_path,
                "file_name": file_name,
                "url": None,
                "local_path": None,
                "text": "",
                "error": "Missing BIS file path.",
            }

        try:
            local_path = await self.download_document(
                file_path=file_path,
                file_name=file_name,
            )

            if local_path is None:
                return {
                    "success": False,
                    "file_path": file_path,
                    "file_name": file_name,
                    "url": document_url,
                    "local_path": None,
                    "text": "",
                    "error": "Document download returned no content.",
                }

            text = self.extract_text(
                local_path
            )

            return {
                "success": True,
                "file_path": file_path,
                "file_name": file_name,
                "url": document_url,
                "local_path": str(local_path),
                "text": text,
                "error": None,
            }

        except Exception as exc:

            return {
                "success": False,
                "file_path": file_path,
                "file_name": file_name,
                "url": document_url,
                "local_path": None,
                "text": "",
                "error": (
                    f"{type(exc).__name__}: {exc}"
                ),
            }

    # =========================================================
    # SUMMARY DOCUMENT
    # =========================================================

    async def fetch_summary(
        self,
        summary_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(
            summary_data,
            dict,
        ):
            return {
                "success": False,
                "error": "Invalid summary data.",
            }

        file_path = summary_data.get(
            "file_path"
        )

        file_name = summary_data.get(
            "file_name"
        )

        return await self.fetch_and_extract(
            file_path=file_path,
            file_name=file_name,
        )

    # =========================================================
    # PRODUCT MANUAL
    # =========================================================

    async def fetch_product_manual(
        self,
        manual_data: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(
            manual_data,
            dict,
        ):
            return {
                "success": False,
                "error": "Invalid product manual data.",
            }

        file_path = manual_data.get(
            "file_path"
        )

        file_name = manual_data.get(
            "file_name"
        )

        return await self.fetch_and_extract(
            file_path=file_path,
            file_name=file_name,
        )

    # =========================================================
    # CLOSE CLIENT
    # =========================================================

    async def close(self):
        await self.client.aclose()