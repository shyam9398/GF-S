from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

from app.bis.bis_web import BISWebProvider
from app.bis.document_service import BISDocumentService


class BISEvidenceService:
    """
    Enrich canonical BIS standard candidates with authoritative evidence.

    Important BIS identifier rules:

    - standardEncId:
        Identifier returned by the BIS Know Your Standards search result.
        Used for standard-detail retrieval and cross-reference retrieval.

    - detail.data.standardId:
        Encrypted identifier returned by
        getWebsiteStandardDetails.
        Used by amendment, summary, corrigendum, gazette, product manual,
        CRS, MCS, laboratory, licence and format-document endpoints.

    This service collects BIS evidence.

    It does NOT decide whether a standard is applicable.

    Applicability decisions are handled separately by
    BISApplicabilityService.
    """

    def __init__(
        self,
        provider: BISWebProvider | None = None,
        document_service: BISDocumentService | None = None,
        max_concurrency: int = 4,
    ):
        self.provider = (
            provider
            or BISWebProvider()
        )

        self.document_service = (
            document_service
            or BISDocumentService()
        )

        # This semaphore limits actual BIS HTTP operations globally.
        #
        # Important:
        # A single candidate may require many BIS endpoints.
        # Therefore limiting candidates alone is insufficient.
        self.max_concurrency = max(
            1,
            max_concurrency,
        )

        self._semaphore = asyncio.Semaphore(
            self.max_concurrency
        )

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _success(
        *,
        endpoint: str,
        data: Any = None,
        message: str | None = None,
    ) -> dict[str, Any]:
        return {
            "success": True,
            "endpoint": endpoint,
            "data": data,
            "message": message,
            "error": None,
        }

    @staticmethod
    def _failure(
        *,
        endpoint: str,
        error: str,
    ) -> dict[str, Any]:
        return {
            "success": False,
            "endpoint": endpoint,
            "data": None,
            "message": None,
            "error": error,
        }

    async def _safe_call(
        self,
        endpoint_name: str,
        operation: Callable[
            [],
            Awaitable[Any],
        ],
    ) -> dict[str, Any]:
        """
        Execute a BIS operation under the global concurrency limit.

        One failed optional BIS endpoint must not stop enrichment of
        the complete candidate set.

        A BIS response such as "No Data Found" is considered a valid
        response when the provider itself returns it successfully.
        """

        try:
            async with self._semaphore:
                result = await operation()

            return self._success(
                endpoint=endpoint_name,
                data=result,
            )

        except Exception as exc:
            return self._failure(
                endpoint=endpoint_name,
                error=str(exc),
            )

    @staticmethod
    def _extract_data(
        response: Any,
    ) -> Any:
        """
        Normalize provider responses.

        Provider methods may return either:

        1. the API data directly
        2. a complete response containing `data`
        """

        if not isinstance(
            response,
            dict,
        ):
            return response

        if "data" in response:
            return response.get(
                "data"
            )

        return response

    @staticmethod
    def _extract_list(
        response: Any,
    ) -> list[dict[str, Any]]:
        """
        Extract records from common BIS response structures.
        """

        data = (
            BISEvidenceService._extract_data(
                response
            )
        )

        if isinstance(
            data,
            list,
        ):
            return [
                item
                for item in data
                if isinstance(
                    item,
                    dict,
                )
            ]

        if not isinstance(
            data,
            dict,
        ):
            return []

        possible_keys = [
            "data",
            "records",
            "items",
            "results",
            "crossRefData",
            "crossFollowRefData",
            "product_manuals_details",
        ]

        for key in possible_keys:
            value = data.get(key)

            if isinstance(
                value,
                list,
            ):
                return [
                    item
                    for item in value
                    if isinstance(
                        item,
                        dict,
                    )
                ]

        return []

    @staticmethod
    def _get_first_value(
        record: dict[str, Any],
        *keys: str,
    ) -> Any:
        for key in keys:
            value = record.get(
                key
            )

            if (
                value is not None
                and value != ""
            ):
                return value

        return None

    # ------------------------------------------------------------------
    # Candidate identity
    # ------------------------------------------------------------------

    @staticmethod
    def _get_standard_number(
        candidate: dict[str, Any],
    ) -> str | None:
        return BISEvidenceService._get_first_value(
            candidate,
            "standardNumber",
            "standard_number",
        )

    @staticmethod
    def _get_search_encrypted_id(
        candidate: dict[str, Any],
    ) -> str | None:
        """
        Get the BIS search encrypted identifier.

        Supports:

        1. normalized top-level candidate
        2. primaryRecord
        3. primaryRecord.raw
        4. records
        5. records[].raw

        The canonical normalized candidate normally contains
        `standardEncId` at the top level, but this method also
        supports nested BIS records for robustness.
        """

        # --------------------------------------------------------------
        # 1. Normalized top-level candidate
        # --------------------------------------------------------------
        value = BISEvidenceService._get_first_value(
            candidate,
            "standardEncId",
            "standard_enc_id",
            "encId",
            "enc_id",
        )

        if value:
            return str(value)

        # --------------------------------------------------------------
        # 2. Primary record
        # --------------------------------------------------------------
        primary_record = candidate.get(
            "primaryRecord"
        )

        if isinstance(
            primary_record,
            dict,
        ):
            value = BISEvidenceService._get_first_value(
                primary_record,
                "standardEncId",
                "standard_enc_id",
                "encId",
                "enc_id",
            )

            if value:
                return str(value)

            # ----------------------------------------------------------
            # 3. Raw BIS search record inside primaryRecord
            # ----------------------------------------------------------
            raw = primary_record.get(
                "raw"
            )

            if isinstance(
                raw,
                dict,
            ):
                value = BISEvidenceService._get_first_value(
                    raw,
                    "standardEncId",
                    "standard_enc_id",
                    "encId",
                    "enc_id",
                )

                if value:
                    return str(value)

        # --------------------------------------------------------------
        # 4. Search through individual records
        # --------------------------------------------------------------
        records = candidate.get(
            "records"
        )

        if isinstance(
            records,
            list,
        ):
            for record in records:
                if not isinstance(
                    record,
                    dict,
                ):
                    continue

                value = BISEvidenceService._get_first_value(
                    record,
                    "standardEncId",
                    "standard_enc_id",
                    "encId",
                    "enc_id",
                )

                if value:
                    return str(value)

                # ------------------------------------------------------
                # 5. Raw BIS search record
                # ------------------------------------------------------
                raw = record.get(
                    "raw"
                )

                if isinstance(
                    raw,
                    dict,
                ):
                    value = BISEvidenceService._get_first_value(
                        raw,
                        "standardEncId",
                        "standard_enc_id",
                        "encId",
                        "enc_id",
                    )

                    if value:
                        return str(value)

        return None

    @staticmethod
    def _get_detail_encrypted_id(
        detail: dict[str, Any],
    ) -> str | None:
        """
        Get detail.data.standardId.

        This is intentionally different from standardEncId.
        """

        return BISEvidenceService._get_first_value(
            detail,
            "standardId",
            "standard_id",
        )

    # ------------------------------------------------------------------
    # Individual evidence collectors
    # ------------------------------------------------------------------

    async def _collect_standard_details(
        self,
        search_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getWebsiteStandardDetails",
            lambda: self.provider.get_standard(
                search_encrypted_id
            ),
        )

    async def _collect_amendments(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getAmendmentDetails",
            lambda: self.provider.get_amendments(
                detail_encrypted_id
            ),
        )

    async def _collect_cross_references(
        self,
        search_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getCrossRefDetails",
            lambda: self.provider.get_relationships(
                search_encrypted_id
            ),
        )

    async def _collect_summary(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getSummaryDetails",
            lambda: self.provider.get_summary(
                detail_encrypted_id
            ),
        )

    async def _collect_corrigenda(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getCorrigendumDetails",
            lambda: self.provider.get_corrigenda(
                detail_encrypted_id
            ),
        )

    async def _collect_gazette(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getGazettedetails",
            lambda: self.provider.get_gazette(
                detail_encrypted_id
            ),
        )

    async def _collect_product_manuals(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getProductManualDetails",
            lambda: self.provider.get_product_manuals(
                detail_encrypted_id
            ),
        )

    async def _collect_crs(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getStandardCRSDetails",
            lambda: self.provider.get_all_crs(
                detail_encrypted_id
            ),
        )

    async def _collect_mcs(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getStandardMCSDetails",
            lambda: self.provider.get_all_mcs(
                detail_encrypted_id
            ),
        )

    async def _collect_laboratories(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getStandardLaboratoryDetails",
            lambda: self.provider.get_all_laboratories(
                detail_encrypted_id
            ),
        )

    async def _collect_licenses(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getStandardLicenseDetails",
            lambda: self.provider.get_all_licenses(
                detail_encrypted_id
            ),
        )

    async def _collect_format_documents(
        self,
        detail_encrypted_id: str,
    ) -> dict[str, Any]:

        return await self._safe_call(
            "getStandardFormatDocumentDetails",
            lambda: self.provider.get_format_documents(
                detail_encrypted_id
            ),
        )

    # ------------------------------------------------------------------
    # Candidate enrichment
    # ------------------------------------------------------------------

    async def enrich_candidate(
        self,
        candidate: dict[str, Any],
        *,
        include_certification: bool = True,
        include_laboratories: bool = True,
        include_licenses: bool = True,
        include_format_documents: bool = True,
    ) -> dict[str, Any]:

        standard_number = (
            self._get_standard_number(
                candidate
            )
        )

        search_encrypted_id = (
            self._get_search_encrypted_id(
                candidate
            )
        )

        evidence: dict[str, Any] = {
            "standard_number": standard_number,

            "search_encrypted_id_available": bool(
                search_encrypted_id
            ),

            "detail_encrypted_id_available": False,

            "standard": None,
            "amendments": None,
            "relationships": None,
            "summary": None,
            "corrigenda": None,
            "gazette": None,
            "product_manuals": None,
            "crs": None,
            "mcs": None,
            "laboratories": None,
            "licenses": None,
            "format_documents": None,

            "errors": [],
        }

        # --------------------------------------------------------------
        # Candidate cannot be enriched without standardEncId.
        # --------------------------------------------------------------

        if not search_encrypted_id:
            evidence["errors"].append(
                {
                    "endpoint": (
                        "getWebsiteStandardDetails"
                    ),
                    "error": (
                        "No standardEncId/encId was "
                        "available for this candidate."
                    ),
                }
            )

            return {
                "candidate": candidate,
                "evidence": evidence,
                "success": False,
            }

        # --------------------------------------------------------------
        # Step 1:
        # Retrieve authoritative BIS standard details.
        # --------------------------------------------------------------

        detail_result = (
            await self._collect_standard_details(
                search_encrypted_id
            )
        )

        evidence["standard"] = (
            detail_result
        )

        if not detail_result["success"]:
            evidence["errors"].append(
                {
                    "endpoint": (
                        detail_result[
                            "endpoint"
                        ]
                    ),
                    "error": (
                        detail_result[
                            "error"
                        ]
                    ),
                }
            )

            return {
                "candidate": candidate,
                "evidence": evidence,
                "success": False,
            }

        detail_response = (
            detail_result.get(
                "data"
            )
        )

        detail_data = (
            self._extract_data(
                detail_response
            )
        )

        if not isinstance(
            detail_data,
            dict,
        ):
            evidence["errors"].append(
                {
                    "endpoint": (
                        "getWebsiteStandardDetails"
                    ),
                    "error": (
                        "BIS returned an unexpected "
                        "standard detail structure."
                    ),
                }
            )

            return {
                "candidate": candidate,
                "evidence": evidence,
                "success": False,
            }

        detail_encrypted_id = (
            self._get_detail_encrypted_id(
                detail_data
            )
        )

        if not detail_encrypted_id:
            evidence["errors"].append(
                {
                    "endpoint": (
                        "getWebsiteStandardDetails"
                    ),
                    "error": (
                        "BIS standard details did not "
                        "contain detail.data.standardId."
                    ),
                }
            )

            return {
                "candidate": candidate,
                "evidence": evidence,
                "success": False,
            }

        evidence[
            "detail_encrypted_id_available"
        ] = True

        # --------------------------------------------------------------
        # Step 2:
        # Collect dependent evidence.
        #
        # These calls are individually concurrency-limited by
        # _safe_call().
        # --------------------------------------------------------------

        tasks: dict[
            str,
            asyncio.Task,
        ] = {}

        tasks[
            "amendments"
        ] = asyncio.create_task(
            self._collect_amendments(
                detail_encrypted_id
            )
        )

        tasks[
            "summary"
        ] = asyncio.create_task(
            self._collect_summary(
                detail_encrypted_id
            )
        )

        tasks[
            "corrigenda"
        ] = asyncio.create_task(
            self._collect_corrigenda(
                detail_encrypted_id
            )
        )

        tasks[
            "gazette"
        ] = asyncio.create_task(
            self._collect_gazette(
                detail_encrypted_id
            )
        )

        tasks[
            "product_manuals"
        ] = asyncio.create_task(
            self._collect_product_manuals(
                detail_encrypted_id
            )
        )

        if include_certification:
            tasks[
                "crs"
            ] = asyncio.create_task(
                self._collect_crs(
                    detail_encrypted_id
                )
            )

            tasks[
                "mcs"
            ] = asyncio.create_task(
                self._collect_mcs(
                    detail_encrypted_id
                )
            )

        if include_laboratories:
            tasks[
                "laboratories"
            ] = asyncio.create_task(
                self._collect_laboratories(
                    detail_encrypted_id
                )
            )

        if include_licenses:
            tasks[
                "licenses"
            ] = asyncio.create_task(
                self._collect_licenses(
                    detail_encrypted_id
                )
            )

        if include_format_documents:
            tasks[
                "format_documents"
            ] = asyncio.create_task(
                self._collect_format_documents(
                    detail_encrypted_id
                )
            )

        # Cross-reference retrieval uses search encrypted ID.
        tasks[
            "relationships"
        ] = asyncio.create_task(
            self._collect_cross_references(
                search_encrypted_id
            )
        )

        results = await asyncio.gather(
            *tasks.values(),
            return_exceptions=True,
        )

        # --------------------------------------------------------------
        # Step 3:
        # Store every endpoint result independently.
        # --------------------------------------------------------------

        for name, result in zip(
            tasks.keys(),
            results,
        ):
            if isinstance(
                result,
                Exception,
            ):
                error_result = (
                    self._failure(
                        endpoint=name,
                        error=str(result),
                    )
                )

                evidence[name] = (
                    error_result
                )

                evidence[
                    "errors"
                ].append(
                    {
                        "endpoint": name,
                        "error": str(
                            result
                        ),
                    }
                )

                continue

            evidence[name] = result

            if not result.get(
                "success",
                False,
            ):
                evidence[
                    "errors"
                ].append(
                    {
                        "endpoint": (
                            result.get(
                                "endpoint",
                                name,
                            )
                        ),
                        "error": (
                            result.get(
                                "error"
                            )
                        ),
                    }
                )

        # --------------------------------------------------------------
        # IMPORTANT:
        #
        # The candidate is considered successfully enriched when the
        # authoritative standard detail was successfully retrieved.
        #
        # Optional evidence failures are retained as warnings/errors
        # but do not discard the candidate.
        # --------------------------------------------------------------

        return {
            "candidate": candidate,
            "evidence": evidence,
            "success": True,
            "partial_evidence": bool(
                evidence["errors"]
            ),
        }

    # ------------------------------------------------------------------
    # Multiple candidate enrichment
    # ------------------------------------------------------------------

    async def enrich_candidates(
        self,
        candidates: list[dict[str, Any]],
        *,
        include_certification: bool = True,
        include_laboratories: bool = True,
        include_licenses: bool = True,
        include_format_documents: bool = True,
    ) -> dict[str, Any]:

        if not candidates:
            return {
                "success": True,
                "total_candidates": 0,
                "successful_candidates": 0,
                "failed_candidates": 0,
                "partial_candidates": 0,
                "results": [],
            }

        tasks = [
            asyncio.create_task(
                self.enrich_candidate(
                    candidate,
                    include_certification=(
                        include_certification
                    ),
                    include_laboratories=(
                        include_laboratories
                    ),
                    include_licenses=(
                        include_licenses
                    ),
                    include_format_documents=(
                        include_format_documents
                    ),
                )
            )
            for candidate in candidates
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        normalized_results: list[
            dict[str, Any]
        ] = []

        for candidate, result in zip(
            candidates,
            results,
        ):
            if isinstance(
                result,
                Exception,
            ):
                normalized_results.append(
                    {
                        "candidate": candidate,
                        "evidence": {
                            "standard_number": (
                                self._get_standard_number(
                                    candidate
                                )
                            ),
                            "errors": [
                                {
                                    "endpoint": (
                                        "candidate_enrichment"
                                    ),
                                    "error": str(
                                        result
                                    ),
                                }
                            ],
                        },
                        "success": False,
                    }
                )

            else:
                normalized_results.append(
                    result
                )

        successful = sum(
            1
            for result
            in normalized_results
            if result.get(
                "success",
                False,
            )
        )

        failed = (
            len(normalized_results)
            - successful
        )

        partial = sum(
            1
            for result
            in normalized_results
            if (
                result.get(
                    "success",
                    False,
                )
                and result.get(
                    "partial_evidence",
                    False,
                )
            )
        )

        return {
            "success": failed == 0,
            "total_candidates": len(
                candidates
            ),
            "successful_candidates": successful,
            "failed_candidates": failed,
            "partial_candidates": partial,
            "results": normalized_results,
        }

    # ------------------------------------------------------------------
    # Document evidence
    # ------------------------------------------------------------------

    async def download_evidence_document(
        self,
        file_path: str,
        file_name: str | None = None,
        *,
        extract_text: bool = True,
    ) -> dict[str, Any]:

        if not file_path:
            return {
                "success": False,
                "error": (
                    "No BIS document file path "
                    "was supplied."
                ),
            }

        try:
            if extract_text:
                return await (
                    self.document_service
                    .fetch_and_extract(
                        file_path=file_path,
                        file_name=file_name,
                    )
                )

            downloaded = await (
                self.document_service
                .download_document(
                    file_path=file_path,
                    file_name=file_name,
                )
            )

            return {
                "success": True,
                "file_path": file_path,
                "file_name": file_name,
                "download": downloaded,
                "text": None,
                "error": None,
            }

        except Exception as exc:
            return {
                "success": False,
                "file_path": file_path,
                "file_name": file_name,
                "text": None,
                "error": str(exc),
            }

    async def enrich_summary_document(
        self,
        summary_response: dict[str, Any],
    ) -> dict[str, Any]:

        if not summary_response.get(
            "success"
        ):
            return {
                "success": False,
                "error": (
                    summary_response.get(
                        "error"
                    )
                ),
            }

        data = self._extract_data(
            summary_response.get(
                "data"
            )
        )

        if not isinstance(
            data,
            dict,
        ):
            return {
                "success": False,
                "error": (
                    "Summary response did not contain "
                    "document metadata."
                ),
            }

        file_path = data.get(
            "file_path"
        )

        file_name = data.get(
            "file_name"
        )

        if not file_path:
            return {
                "success": False,
                "error": (
                    "No summary PDF path was "
                    "returned by BIS."
                ),
                "metadata": data,
            }

        document = await (
            self.download_evidence_document(
                file_path=file_path,
                file_name=file_name,
                extract_text=True,
            )
        )

        return {
            "success": document.get(
                "success",
                False,
            ),
            "metadata": data,
            "document": document,
        }

    async def enrich_product_manual_document(
        self,
        manual_response: dict[str, Any],
    ) -> list[dict[str, Any]]:

        if not manual_response.get(
            "success"
        ):
            return [
                {
                    "success": False,
                    "error": (
                        manual_response.get(
                            "error"
                        )
                    ),
                }
            ]

        manual_records = (
            self._extract_list(
                manual_response.get(
                    "data"
                )
            )
        )

        results: list[
            dict[str, Any]
        ] = []

        for manual in manual_records:

            file_path = manual.get(
                "file_path"
            )

            file_name = manual.get(
                "file_name"
            )

            if not file_path:
                results.append(
                    {
                        "success": False,
                        "metadata": manual,
                        "error": (
                            "Product manual record "
                            "has no file_path."
                        ),
                    }
                )

                continue

            document = await (
                self.download_evidence_document(
                    file_path=file_path,
                    file_name=file_name,
                    extract_text=True,
                )
            )

            results.append(
                {
                    "success": document.get(
                        "success",
                        False,
                    ),
                    "metadata": manual,
                    "document": document,
                }
            )

        return results

    # ------------------------------------------------------------------
    # Candidate evidence summary
    # ------------------------------------------------------------------

    @staticmethod
    def build_evidence_summary(
        enriched_candidate: dict[str, Any],
    ) -> dict[str, Any]:

        candidate = (
            enriched_candidate.get(
                "candidate",
                {},
            )
        )

        evidence = (
            enriched_candidate.get(
                "evidence",
                {},
            )
        )

        def successful(
            name: str,
        ) -> bool:

            value = evidence.get(
                name
            )

            return (
                isinstance(
                    value,
                    dict,
                )
                and value.get(
                    "success"
                )
                is True
            )

        def record_count(
            name: str,
        ) -> int:

            value = evidence.get(
                name
            )

            if not isinstance(
                value,
                dict,
            ):
                return 0

            data = (
                BISEvidenceService
                ._extract_data(
                    value.get(
                        "data"
                    )
                )
            )

            if isinstance(
                data,
                list,
            ):
                return len(data)

            if isinstance(
                data,
                dict,
            ):
                for key in (
                    "records",
                    "items",
                    "data",
                    "product_manuals_details",
                    "crossRefData",
                    "crossFollowRefData",
                ):
                    records = data.get(
                        key
                    )

                    if isinstance(
                        records,
                        list,
                    ):
                        return len(
                            records
                        )

            return 0

        relationships = evidence.get(
            "relationships"
        )

        relationship_data = (
            BISEvidenceService
            ._extract_data(
                relationships.get(
                    "data"
                )
                if isinstance(
                    relationships,
                    dict,
                )
                else None
            )
        )

        cross_ref_count = 0
        cross_follow_ref_count = 0

        if isinstance(
            relationship_data,
            dict,
        ):
            cross_ref = (
                relationship_data.get(
                    "crossRefData"
                )
            )

            cross_follow = (
                relationship_data.get(
                    "crossFollowRefData"
                )
            )

            if isinstance(
                cross_ref,
                list,
            ):
                cross_ref_count = len(
                    cross_ref
                )

            if isinstance(
                cross_follow,
                list,
            ):
                cross_follow_ref_count = len(
                    cross_follow
                )

        return {
            "standard_number": (
                candidate.get(
                    "standardNumber"
                )
                or candidate.get(
                    "standard_number"
                )
            ),

            "standard_name": (
                candidate.get(
                    "standardName"
                )
                or candidate.get(
                    "standard_name"
                )
            ),

            "details_available": successful(
                "standard"
            ),

            "amendments_available": successful(
                "amendments"
            ),

            "summary_available": successful(
                "summary"
            ),

            "corrigenda_available": successful(
                "corrigenda"
            ),

            "gazette_available": successful(
                "gazette"
            ),

            "product_manual_available": successful(
                "product_manuals"
            ),

            "crs_available": successful(
                "crs"
            ),

            "mcs_available": successful(
                "mcs"
            ),

            "laboratory_records": record_count(
                "laboratories"
            ),

            "license_records": record_count(
                "licenses"
            ),

            "format_document_available": successful(
                "format_documents"
            ),

            "cross_reference_count": (
                cross_ref_count
            ),

            "cross_follow_reference_count": (
                cross_follow_ref_count
            ),

            "error_count": len(
                evidence.get(
                    "errors",
                    [],
                )
            ),

            "partial_evidence": bool(
                enriched_candidate.get(
                    "partial_evidence",
                    False,
                )
            ),
        }

    # ------------------------------------------------------------------
    # Complete enrichment helper
    # ------------------------------------------------------------------

    async def enrich_discovery_result(
        self,
        discovery_result: dict[str, Any],
        *,
        include_certification: bool = True,
        include_laboratories: bool = True,
        include_licenses: bool = True,
        include_format_documents: bool = True,
    ) -> dict[str, Any]:

        candidates = discovery_result.get(
            "candidates",
            [],
        )

        enrichment = (
            await self.enrich_candidates(
                candidates,
                include_certification=(
                    include_certification
                ),
                include_laboratories=(
                    include_laboratories
                ),
                include_licenses=(
                    include_licenses
                ),
                include_format_documents=(
                    include_format_documents
                ),
            )
        )

        summaries = [
            self.build_evidence_summary(
                result
            )
            for result in enrichment[
                "results"
            ]
        ]

        return {
            "success": enrichment[
                "success"
            ],

            "discovery": discovery_result,

            "enrichment": enrichment,

            "evidence_summary": summaries,

            "coverage": {
                "candidate_count": len(
                    candidates
                ),

                "enriched_count": enrichment[
                    "successful_candidates"
                ],

                "failed_enrichment_count": enrichment[
                    "failed_candidates"
                ],

                "partial_evidence_count": enrichment[
                    "partial_candidates"
                ],
            },
        }

    # ------------------------------------------------------------------
    # Resource cleanup
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self.provider.close()

        await self.document_service.close()