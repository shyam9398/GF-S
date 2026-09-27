from __future__ import annotations

from datetime import date, datetime
from typing import Any


class BISStandardNormalizer:
    """
    Normalizes BIS search/detail records into a canonical
    representation.

    Important:
    - standardNumber is the canonical identity.
    - BIS standardId values are preserved as source identifiers.
    - No standard is created or invented by this class.
    - Duplicate BIS records are merged only when their
      normalized standard numbers match.
    - All source records are preserved as evidence.
    - Primary-record selection is conservative and must not
      rely only on publication date.
    """

    # =========================================================
    # STANDARD NUMBER NORMALIZATION
    # =========================================================

    @staticmethod
    def normalize_standard_number(
        standard_number: Any,
    ) -> str | None:

        if standard_number is None:
            return None

        value = str(
            standard_number
        ).strip()

        if not value:
            return None

        value = " ".join(
            value.split()
        )

        # Normalize the common BIS forms:
        #
        # IS 2925 : 1984
        # IS 2925:1984
        # is 2925 : 1984
        #
        # into:
        #
        # IS 2925:1984

        if value.upper().startswith("IS "):
            value = value[3:].strip()

        value = value.replace(
            " : ",
            ":",
        )

        value = value.replace(
            " :",
            ":",
        )

        value = value.replace(
            ": ",
            ":",
        )

        return f"IS {value}"

    # =========================================================
    # DATE HELPERS
    # =========================================================

    @staticmethod
    def _parse_date(
        value: Any,
    ) -> date | None:

        if value is None:
            return None

        if isinstance(
            value,
            datetime,
        ):
            return value.date()

        if isinstance(
            value,
            date,
        ):
            return value

        text = str(
            value
        ).strip()

        if not text:
            return None

        # BIS commonly returns ISO-style dates such as:
        # 1985-01-31
        # 2025-06-20

        try:
            return datetime.fromisoformat(
                text[:10]
            ).date()
        except ValueError:
            pass

        # Additional defensive formats.

        for fmt in (
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
        ):
            try:
                return datetime.strptime(
                    text,
                    fmt,
                ).date()
            except ValueError:
                continue

        return None

    @staticmethod
    def _is_future_or_current(
        value: Any,
    ) -> bool:

        parsed = (
            BISStandardNormalizer._parse_date(
                value
            )
        )

        if parsed is None:
            return False

        return parsed >= date.today()

    # =========================================================
    # NORMALIZE SEARCH RECORD
    # =========================================================

    @classmethod
    def normalize_search_record(
        cls,
        record: dict[str, Any],
    ) -> dict[str, Any] | None:

        if not isinstance(
            record,
            dict,
        ):
            return None

        standard_number = (
            cls.normalize_standard_number(
                record.get(
                    "standardNumber"
                )
            )
        )

        if not standard_number:
            return None

        return {
            "standardNumber": standard_number,

            "standardName": record.get(
                "standardName"
            ),

            "standardNameInHindi": record.get(
                "standardNameInHindi"
            ),

            "standardId": record.get(
                "standardId"
            ),

            "standardEncId": record.get(
                "standardEncId"
            ),

            "departmentId": record.get(
                "departmentId"
            ),

            "committeeId": record.get(
                "committeeId"
            ),

            "publishedOn": record.get(
                "publishedOn"
            ),

            "validUpto": record.get(
                "validUpto"
            ),

            "withdrawStatus": record.get(
                "withdrawStatus"
            ),

            "withdrawOn": record.get(
                "withdrawOn"
            ),

            "isStatus": record.get(
                "isStatus"
            ),

            "matched_standard": record.get(
                "matched_standard"
            ),

            # Preserve the original retrieval provenance.
            "_retrieval_query": record.get(
                "_retrieval_query"
            ),

            "source": "BIS",
            "sourceType": "search",

            # Preserve the complete source record.
            "raw": record,
        }

    # =========================================================
    # NORMALIZE DETAIL RECORD
    # =========================================================

    @classmethod
    def normalize_detail_record(
        cls,
        record: dict[str, Any],
    ) -> dict[str, Any] | None:

        if not isinstance(
            record,
            dict,
        ):
            return None

        standard_number = (
            cls.normalize_standard_number(
                record.get(
                    "standardNumber"
                )
            )
        )

        if not standard_number:
            return None

        return {
            "standardNumber": standard_number,

            "standardName": record.get(
                "standardName"
            ),

            "standardId": record.get(
                "standardId"
            ),

            "rowStandardId": record.get(
                "rowStandardId"
            ),

            "pk_is_id": record.get(
                "pk_is_id"
            ),

            "publishedOn": record.get(
                "publishedOn"
            ),

            "committeeId": record.get(
                "committeeId"
            ),

            "departmentId": record.get(
                "departmentId"
            ),

            "groupName": record.get(
                "groupName"
            ),

            "subGroupName": record.get(
                "subGroupName"
            ),

            "subSubGroupName": record.get(
                "subSubGroupName"
            ),

            "noOfRevision": record.get(
                "noOfRevision"
            ),

            "noOfAmendment": record.get(
                "noOfAmendment"
            ),

            "typeOfStandardId": record.get(
                "typeOfStandardId"
            ),

            "languageId": record.get(
                "languageId"
            ),

            "shortTitle": record.get(
                "shortTitle"
            ),

            "reAffirmationYear": record.get(
                "reAffirmationYear"
            ),

            "reviewOn": record.get(
                "reviewOn"
            ),

            "equivalentIs": record.get(
                "equivalentIs"
            ),

            "is_documents": record.get(
                "is_documents"
            ),

            "withdrawStatus": record.get(
                "withdrawStatus"
            ),

            "withdrawOn": record.get(
                "withdrawOn"
            ),

            "isStatus": record.get(
                "isStatus"
            ),

            "superseded_byis": record.get(
                "superseded_byis"
            ),

            "committeeName": record.get(
                "committeeName"
            ),

            "departmentName": record.get(
                "departmentName"
            ),

            "source": "BIS",
            "sourceType": "detail",
            "raw": record,
        }

    # =========================================================
    # MERGE RECORDS
    # =========================================================

    @classmethod
    def merge_records(
        cls,
        records: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:

        canonical: dict[
            str,
            dict[str, Any],
        ] = {}

        for record in records:

            normalized = (
                cls.normalize_search_record(
                    record
                )
            )

            if not normalized:
                continue

            standard_number = normalized[
                "standardNumber"
            ]

            if standard_number not in canonical:

                canonical[
                    standard_number
                ] = {
                    "standardNumber": (
                        standard_number
                    ),

                    "standardName": (
                        normalized.get(
                            "standardName"
                        )
                    ),

                    "standardNameInHindi": (
                        normalized.get(
                            "standardNameInHindi"
                        )
                    ),

                    "records": [],

                    "standardIds": [],

                    "standardEncIds": [],

                    "source": "BIS",
                }

            entry = canonical[
                standard_number
            ]

            entry["records"].append(
                normalized
            )

            standard_id = normalized.get(
                "standardId"
            )

            if (
                standard_id is not None
                and standard_id not in entry[
                    "standardIds"
                ]
            ):
                entry[
                    "standardIds"
                ].append(
                    standard_id
                )

            standard_enc_id = normalized.get(
                "standardEncId"
            )

            if (
                standard_enc_id is not None
                and standard_enc_id not in entry[
                    "standardEncIds"
                ]
            ):
                entry[
                    "standardEncIds"
                ].append(
                    standard_enc_id
                )

        return canonical

    # =========================================================
    # PRIMARY RECORD SCORING
    # =========================================================

    @classmethod
    def _primary_record_key(
        cls,
        record: dict[str, Any],
    ) -> tuple[int, int, int, int, str]:

        withdrawn = (
            record.get(
                "withdrawStatus"
            ) == 1
        )

        valid_upto = record.get(
            "validUpto"
        )

        valid_current = cls._is_future_or_current(
            valid_upto
        )

        review_on = record.get(
            "reviewOn"
        )

        review_date = cls._parse_date(
            review_on
        )

        published_on = record.get(
            "publishedOn"
        )

        published_date = cls._parse_date(
            published_on
        )

        # Priority:
        #
        # 1. Non-withdrawn records
        # 2. Records whose validity extends to the current date
        # 3. Records with review/reaffirmation information
        # 4. Latest review date
        # 5. Latest publication date
        #
        # This prevents a later-published but expired duplicate
        # from automatically replacing a currently valid record.

        has_review_information = (
            review_date is not None
            or bool(
                record.get(
                    "reAffirmationYear"
                )
            )
        )

        review_timestamp = (
            review_date.toordinal()
            if review_date
            else 0
        )

        published_timestamp = (
            published_date.toordinal()
            if published_date
            else 0
        )

        return (
            0 if withdrawn else 1,
            1 if valid_current else 0,
            1 if has_review_information else 0,
            review_timestamp,
            str(published_timestamp),
        )

    # =========================================================
    # SELECT PRIMARY SEARCH RECORD
    # =========================================================

    @classmethod
    def select_primary_record(
        cls,
        records: list[dict[str, Any]],
    ) -> dict[str, Any] | None:

        if not records:
            return None

        valid_records = [
            record
            for record in records
            if isinstance(
                record,
                dict,
            )
        ]

        if not valid_records:
            return None

        return max(
            valid_records,
            key=cls._primary_record_key,
        )

    # =========================================================
    # BUILD CANONICAL STANDARD
    # =========================================================

    @classmethod
    def build_canonical_standard(
        cls,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        grouped = cls.merge_records(
            records
        )

        result: list[
            dict[str, Any]
        ] = []

        for standard_number, group in grouped.items():

            primary = (
                cls.select_primary_record(
                    group["records"]
                )
            )

            result.append(
                {
                    "standardNumber": (
                        standard_number
                    ),

                    "standardName": (
                        primary.get(
                            "standardName"
                        )
                        if primary
                        else group.get(
                            "standardName"
                        )
                    ),

                    "primaryRecord": primary,

                    # IMPORTANT:
                    # Keep every BIS search record as evidence.
                    "records": group[
                        "records"
                    ],

                    "standardIds": group[
                        "standardIds"
                    ],

                    "standardEncIds": group[
                        "standardEncIds"
                    ],

                    "recordCount": len(
                        group[
                            "records"
                        ]
                    ),

                    "source": "BIS",
                }
            )

        return result