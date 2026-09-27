from abc import ABC, abstractmethod
from typing import Any


class BISRetrievalProvider(ABC):
    """
    Abstract interface for retrieving authoritative BIS
    standard information.

    The implementation must retrieve information from
    authoritative BIS sources and must not generate or
    invent Indian Standard information.
    """

    # =========================================================
    # STANDARD SEARCH
    # =========================================================

    @abstractmethod
    async def search_standards(
        self,
        query: str,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """
        Search BIS standards using a natural-language or
        keyword query.
        """
        raise NotImplementedError

    # =========================================================
    # STANDARD DETAILS
    # =========================================================

    @abstractmethod
    async def get_standard(
        self,
        standard_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve authoritative details for a BIS standard.
        """
        raise NotImplementedError

    # =========================================================
    # AMENDMENTS
    # =========================================================

    @abstractmethod
    async def get_amendments(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve amendments associated with a BIS standard.
        """
        raise NotImplementedError

    # =========================================================
    # CROSS REFERENCES
    # =========================================================

    @abstractmethod
    async def get_relationships(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve BIS cross-reference relationships.
        """
        raise NotImplementedError

    # =========================================================
    # STANDARD SUMMARY
    # =========================================================

    @abstractmethod
    async def get_summary(
        self,
        standard_id: str,
    ) -> dict[str, Any] | None:
        """
        Retrieve the BIS standard summary document metadata.
        """
        raise NotImplementedError

    # =========================================================
    # CORRIGENDUM
    # =========================================================

    @abstractmethod
    async def get_corrigenda(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve corrigendum information for a BIS standard.
        """
        raise NotImplementedError

    # =========================================================
    # GAZETTE
    # =========================================================

    @abstractmethod
    async def get_gazette(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve Gazette information associated with a
        BIS standard.
        """
        raise NotImplementedError

    # =========================================================
    # PRODUCT MANUAL
    # =========================================================

    @abstractmethod
    async def get_product_manuals(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve BIS product manual document information.
        """
        raise NotImplementedError

    # =========================================================
    # CRS
    # =========================================================

    @abstractmethod
    async def get_crs(
        self,
        standard_id: str,
        search_text: str = "",
        status: str = "Operative",
        page: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Retrieve one page of CRS records associated with
        a BIS standard.
        """
        raise NotImplementedError

    # =========================================================
    # MCS
    # =========================================================

    @abstractmethod
    async def get_mcs(
        self,
        standard_id: str,
        search_text: str = "",
        page: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Retrieve one page of MCS records associated with
        a BIS standard.
        """
        raise NotImplementedError

    # =========================================================
    # LABORATORIES
    # =========================================================

    @abstractmethod
    async def get_laboratories(
        self,
        standard_id: str,
        search_text: str = "",
        page: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Retrieve one page of laboratory records associated
        with a BIS standard.
        """
        raise NotImplementedError

    # =========================================================
    # LICENSES
    # =========================================================

    @abstractmethod
    async def get_licenses(
        self,
        standard_id: str,
        search_text: str = "",
        status: str = "Operative",
        page: int = 1,
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Retrieve one page of BIS license records associated
        with a standard.
        """
        raise NotImplementedError

    # =========================================================
    # FORMAT DOCUMENTS
    # =========================================================

    @abstractmethod
    async def get_format_documents(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:
        """
        Retrieve standard format-document information.
        """
        raise NotImplementedError

    # =========================================================
    # CLOSE PROVIDER
    # =========================================================

    @abstractmethod
    async def close(self):
        """
        Close the underlying HTTP client/resources.
        """
        raise NotImplementedError