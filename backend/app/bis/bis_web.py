from typing import Any

# pyrefly: ignore [missing-import]
import httpx

from app.bis.base import BISRetrievalProvider


class BISWebProvider(BISRetrievalProvider):

    # =========================================================
    # BIS API ENDPOINTS
    # =========================================================

    SEARCH_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//searchKnowStandards"
    )

    DETAIL_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getWebsiteStandardDetails"
    )

    AMENDMENT_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getAmendmentDetails"
    )

    CROSS_REF_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getCrossRefDetails"
    )

    SUMMARY_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getSummaryDetails"
    )

    CORRIGENDUM_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getCorrigendumDetails"
    )

    GAZETTE_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getGazettedetails"
    )

    PRODUCT_MANUAL_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getProductManualDetails"
    )

    CRS_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getStandardCRSDetails"
    )

    MCS_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getStandardMCSDetails"
    )

    LABORATORY_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getStandardLaboratoryDetails"
    )

    LICENSE_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getStandardLicenseDetails"
    )

    FORMAT_DOCUMENT_URL = (
        "https://standardsadmin.bis.gov.in/"
        "review-service//getStandardFormatDocumentDetails"
    )

    # =========================================================
    # DEFAULT PAGINATION
    # =========================================================

    DEFAULT_PAGE_SIZE = 50

    # =========================================================
    # INITIALIZE HTTP CLIENT
    # =========================================================

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
        )
        self._search_cache: dict[str, list[dict[str, Any]]] = {}

    # =========================================================
    # COMMON POST HELPER
    # =========================================================

    async def _post_json(
        self,
        url: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        response = await self.client.post(
            url,
            json=payload,
        )

        response.raise_for_status()

        result = response.json()

        if not isinstance(result, dict):
            return {}

        return result

    # =========================================================
    # SEARCH BIS STANDARDS
    # =========================================================

    async def search_standards_detailed(
        self,
        query: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Execute BIS standard search with explicit status differentiation:
        - SUCCESS_WITH_RESULTS
        - SUCCESS_NO_RESULTS
        - BIS_HTTP_ERROR
        - BIS_API_ERROR
        - INVALID_RESPONSE
        - TIMEOUT
        - PARSER_ERROR
        """
        if not query or not query.strip():
            return {
                "status": "SUCCESS_NO_RESULTS",
                "records": [],
                "error": None,
            }

        cleaned_query = query.strip()
        cache_key = cleaned_query.casefold()

        if cache_key in self._search_cache:
            cached = self._search_cache[cache_key]
            return {
                "status": "SUCCESS_WITH_RESULTS" if cached else "SUCCESS_NO_RESULTS",
                "records": cached,
                "error": None,
            }

        payload = {
            "searchText": cleaned_query,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        try:
            response = await self.client.post(
                self.SEARCH_URL,
                json=payload,
            )

            if response.status_code != 200:
                return {
                    "status": "BIS_HTTP_ERROR",
                    "records": [],
                    "error": f"BIS server returned HTTP {response.status_code}",
                }

            try:
                result = response.json()
            except Exception as json_err:
                return {
                    "status": "INVALID_RESPONSE",
                    "records": [],
                    "error": f"Invalid JSON in BIS response: {json_err}",
                }

            if not isinstance(result, dict):
                return {
                    "status": "INVALID_RESPONSE",
                    "records": [],
                    "error": "BIS response is not a valid JSON dictionary",
                }

            api_status = result.get("status")
            if api_status != "SUCCESS":
                msg = str(result.get("message") or "")
                if "no data" in msg.lower() or "not found" in msg.lower():
                    self._search_cache[cache_key] = []
                    return {
                        "status": "SUCCESS_NO_RESULTS",
                        "records": [],
                        "error": None,
                    }
                return {
                    "status": "BIS_API_ERROR",
                    "records": [],
                    "error": f"BIS API returned status '{api_status}': {msg}",
                }

            data = result.get("data", [])
            if not isinstance(data, list):
                self._search_cache[cache_key] = []
                return {
                    "status": "SUCCESS_NO_RESULTS",
                    "records": [],
                    "error": None,
                }

            try:
                records = [item for item in data if isinstance(item, dict)]
            except Exception as parse_err:
                return {
                    "status": "PARSER_ERROR",
                    "records": [],
                    "error": f"Error parsing BIS records: {parse_err}",
                }

            self._search_cache[cache_key] = records
            return {
                "status": "SUCCESS_WITH_RESULTS" if records else "SUCCESS_NO_RESULTS",
                "records": records,
                "error": None,
            }

        except httpx.TimeoutException:
            return {
                "status": "TIMEOUT",
                "records": [],
                "error": f"Timeout connecting to BIS search endpoint for query '{cleaned_query}'",
            }
        except Exception as exc:
            return {
                "status": "BIS_HTTP_ERROR",
                "records": [],
                "error": f"Connection error reaching BIS: {exc}",
            }

    async def search_standards(
        self,
        query: str,
        **kwargs,
    ) -> list[dict[str, Any]]:
        detailed = await self.search_standards_detailed(query, **kwargs)
        return detailed.get("records", [])

    # =========================================================
    # GET STANDARD DETAILS
    # =========================================================

    async def get_standard(
        self,
        standard_id: str,
    ) -> dict[str, Any] | None:

        if not standard_id:
            return None

        payload = {
            "encId": standard_id,
            "fromPage": "guestUserPage",
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.DETAIL_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return None

        data = result.get("data")

        if not isinstance(data, dict):
            return None

        return data

    # =========================================================
    # GET AMENDMENTS
    # =========================================================

    async def get_amendments(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:

        if not standard_id:
            return []

        payload = {
            "standardId": standard_id,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.AMENDMENT_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return []

        data = result.get("data", [])

        if not isinstance(data, list):
            return []

        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    # =========================================================
    # GET CROSS REFERENCES
    # =========================================================

    async def get_relationships(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:

        if not standard_id:
            return []

        payload = {
            "encId": standard_id,
            "fromPage": "guestUserPage",
            "refreshToken": None,
            "sub": None,
            "token": None,
            "clientId": None,
            "clientSecret": None,
        }

        result = await self._post_json(
            self.CROSS_REF_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return []

        data = result.get("data", {})

        if not isinstance(data, dict):
            return []

        relationships: list[dict[str, Any]] = []

        # -----------------------------------------------------
        # CROSS REFERENCES
        # -----------------------------------------------------

        cross_ref_data = data.get(
            "crossRefData",
            [],
        )

        if isinstance(cross_ref_data, list):

            for item in cross_ref_data:

                if not isinstance(item, dict):
                    continue

                relationship = dict(item)

                relationship["relationshipType"] = (
                    "CROSS_REFERENCE"
                )

                relationships.append(
                    relationship
                )

        # -----------------------------------------------------
        # CROSS FOLLOW REFERENCES
        # -----------------------------------------------------

        cross_follow_ref_data = data.get(
            "crossFollowRefData",
            [],
        )

        if isinstance(cross_follow_ref_data, list):

            for item in cross_follow_ref_data:

                if not isinstance(item, dict):
                    continue

                relationship = dict(item)

                relationship["relationshipType"] = (
                    "CROSS_FOLLOW_REFERENCE"
                )

                relationships.append(
                    relationship
                )

        return relationships

    # =========================================================
    # GET STANDARD SUMMARY
    # =========================================================

    async def get_summary(
        self,
        standard_id: str,
    ) -> dict[str, Any] | None:

        if not standard_id:
            return None

        payload = {
            "standardId": standard_id,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.SUMMARY_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return None

        data = result.get("data")

        if not isinstance(data, dict):
            return None

        return data

    # =========================================================
    # GET CORRIGENDUM DETAILS
    # =========================================================

    async def get_corrigenda(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:

        if not standard_id:
            return []

        payload = {
            "standardId": standard_id,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.CORRIGENDUM_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return []

        data = result.get("data", [])

        if not isinstance(data, list):
            return []

        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    # =========================================================
    # GET GAZETTE DETAILS
    # =========================================================

    async def get_gazette(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:

        if not standard_id:
            return []

        payload = {
            "standardId": standard_id,
            "fromPage": "guestUserPage",
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.GAZETTE_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return []

        data = result.get("data", [])

        if not isinstance(data, list):
            return []

        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    # =========================================================
    # GET PRODUCT MANUAL DETAILS
    # =========================================================

    async def get_product_manuals(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:

        if not standard_id:
            return []

        payload = {
            "standardId": standard_id,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.PRODUCT_MANUAL_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return []

        data = result.get("data", {})

        if not isinstance(data, dict):
            return []

        manuals = data.get(
            "product_manuals_details",
            [],
        )

        if not isinstance(manuals, list):
            return []

        return [
            item
            for item in manuals
            if isinstance(item, dict)
        ]

    # =========================================================
    # GET CRS DETAILS
    # =========================================================

    async def get_crs(
        self,
        standard_id: str,
        search_text: str = "",
        status: str = "Operative",
        page: int = 1,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:

        if not standard_id:
            return {
                "data": [],
                "pagination": {},
            }

        payload = {
            "standardId": standard_id,
            "searchText": search_text,
            "status": status,
            "page": page,
            "limit": limit,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.CRS_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return {
                "data": [],
                "pagination": {},
            }

        data = result.get("data", [])

        if not isinstance(data, list):
            data = []

        pagination = result.get(
            "pagination",
            {},
        )

        if not isinstance(pagination, dict):
            pagination = {}

        return {
            "data": data,
            "pagination": pagination,
        }

    # =========================================================
    # GET MCS DETAILS
    # =========================================================

    async def get_mcs(
        self,
        standard_id: str,
        search_text: str = "",
        page: int = 1,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:

        if not standard_id:
            return {
                "data": [],
                "pagination": {},
            }

        payload = {
            "standardId": standard_id,
            "searchText": search_text,
            "page": page,
            "limit": limit,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.MCS_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return {
                "data": [],
                "pagination": {},
            }

        data = result.get("data", [])

        if not isinstance(data, list):
            data = []

        pagination = result.get(
            "pagination",
            {},
        )

        if not isinstance(pagination, dict):
            pagination = {}

        return {
            "data": data,
            "pagination": pagination,
        }

    # =========================================================
    # GET LABORATORY DETAILS
    # =========================================================

    async def get_laboratories(
        self,
        standard_id: str,
        search_text: str = "",
        page: int = 1,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:

        if not standard_id:
            return {
                "data": [],
                "pagination": {},
            }

        payload = {
            "standardId": standard_id,
            "searchText": search_text,
            "page": page,
            "limit": limit,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.LABORATORY_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return {
                "data": [],
                "pagination": {},
            }

        data = result.get("data", [])

        if not isinstance(data, list):
            data = []

        pagination = result.get(
            "pagination",
            {},
        )

        if not isinstance(pagination, dict):
            pagination = {}

        return {
            "data": data,
            "pagination": pagination,
        }

    # =========================================================
    # GET LICENSE DETAILS
    # =========================================================

    async def get_licenses(
        self,
        standard_id: str,
        search_text: str = "",
        status: str = "Operative",
        page: int = 1,
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> dict[str, Any]:

        if not standard_id:
            return {
                "data": [],
                "pagination": {},
            }

        payload = {
            "standardId": standard_id,
            "searchText": search_text,
            "status": status,
            "page": page,
            "limit": limit,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.LICENSE_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return {
                "data": [],
                "pagination": {},
            }

        data = result.get("data", [])

        if not isinstance(data, list):
            data = []

        pagination = result.get(
            "pagination",
            {},
        )

        if not isinstance(pagination, dict):
            pagination = {}

        return {
            "data": data,
            "pagination": pagination,
        }

    # =========================================================
    # GET STANDARD FORMAT DOCUMENT DETAILS
    # =========================================================

    async def get_format_documents(
        self,
        standard_id: str,
    ) -> list[dict[str, Any]]:

        if not standard_id:
            return []

        payload = {
            "standardId": standard_id,
            "token": None,
            "refreshToken": None,
            "clientId": None,
            "clientSecret": None,
            "sub": None,
        }

        result = await self._post_json(
            self.FORMAT_DOCUMENT_URL,
            payload,
        )

        if result.get("status") != "SUCCESS":
            return []

        data = result.get("data", [])

        if not isinstance(data, list):
            return []

        return [
            item
            for item in data
            if isinstance(item, dict)
        ]

    # =========================================================
    # GENERIC PAGINATION HELPER
    # =========================================================

    async def _get_all_paginated_records(
        self,
        fetch_page,
        max_pages: int = 1,
    ) -> list[dict[str, Any]]:

        all_records: list[dict[str, Any]] = []

        page = 1

        while page <= max_pages:

            result = await fetch_page(page)

            if not isinstance(result, dict):
                break

            records = result.get(
                "data",
                [],
            )

            if not isinstance(records, list):
                break

            valid_records = [
                item
                for item in records
                if isinstance(item, dict)
            ]

            all_records.extend(
                valid_records
            )

            pagination = result.get(
                "pagination",
                {},
            )

            if not isinstance(
                pagination,
                dict,
            ):
                break

            total_pages = pagination.get(
                "totalPages"
            )

            current_page = pagination.get(
                "currentPage",
                page,
            )

            last_page = pagination.get(
                "lastPage"
            )

            if (
                isinstance(total_pages, int)
                and total_pages > 0
                and current_page >= total_pages
            ):
                break

            if last_page is True:
                break

            if not valid_records:
                break

            page += 1

        return all_records

    # =========================================================
    # GET ALL LABORATORIES
    # =========================================================

    async def get_all_laboratories(
        self,
        standard_id: str,
        search_text: str = "",
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:

        async def fetch_page(
            page: int,
        ) -> dict[str, Any]:

            return await self.get_laboratories(
                standard_id=standard_id,
                search_text=search_text,
                page=page,
                limit=limit,
            )

        return await self._get_all_paginated_records(
            fetch_page
        )

    # =========================================================
    # GET ALL LICENSES
    # =========================================================

    async def get_all_licenses(
        self,
        standard_id: str,
        search_text: str = "",
        status: str = "Operative",
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:

        async def fetch_page(
            page: int,
        ) -> dict[str, Any]:

            return await self.get_licenses(
                standard_id=standard_id,
                search_text=search_text,
                status=status,
                page=page,
                limit=limit,
            )

        return await self._get_all_paginated_records(
            fetch_page
        )

    # =========================================================
    # GET ALL CRS RECORDS
    # =========================================================

    async def get_all_crs(
        self,
        standard_id: str,
        search_text: str = "",
        status: str = "Operative",
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:

        async def fetch_page(
            page: int,
        ) -> dict[str, Any]:

            return await self.get_crs(
                standard_id=standard_id,
                search_text=search_text,
                status=status,
                page=page,
                limit=limit,
            )

        return await self._get_all_paginated_records(
            fetch_page
        )

    # =========================================================
    # GET ALL MCS RECORDS
    # =========================================================

    async def get_all_mcs(
        self,
        standard_id: str,
        search_text: str = "",
        limit: int = DEFAULT_PAGE_SIZE,
    ) -> list[dict[str, Any]]:

        async def fetch_page(
            page: int,
        ) -> dict[str, Any]:

            return await self.get_mcs(
                standard_id=standard_id,
                search_text=search_text,
                page=page,
                limit=limit,
            )

        return await self._get_all_paginated_records(
            fetch_page
        )

    # =========================================================
    # CLOSE HTTP CLIENT
    # =========================================================

    async def close(self):
        await self.client.aclose()