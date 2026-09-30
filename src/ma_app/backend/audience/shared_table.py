"""Placeholder repository for a FUTURE supported cross-workspace audience source.

IMPORTANT: this is a clearly-marked placeholder. It does NOT assume that a CMEG table
or an undocumented CustomerLake API is reachable. When `audience_source_mode=shared_table`,
it validates that the configured table exists and that the App service principal has
SELECT on it, and FAILS CLEARLY otherwise (never silently falling back to a different
audience). A real deployment would point `MA_APP_AUDIENCE_TABLE` at a Delta Sharing
table, a supported shared table, or a reverse-ETL destination validated with the product.
"""

from __future__ import annotations

from ..db import Db, SqlError
from ..models import AudienceDetail, AudienceMember, AudienceSummary, Distribution
from .interface import AudienceNotFound, AudienceSourceUnavailable


class SharedTableAudienceRepository:
    def __init__(self, db: Db):
        self._db = db
        self._table = db.config.audience_table
        self._validate_access()

    def _validate_access(self) -> None:
        """Fail fast if the configured shared table is missing or not readable."""
        try:
            self._db.execute(f"SELECT 1 FROM {self._table} LIMIT 1")
        except SqlError as exc:  # pragma: no cover - depends on live grants
            raise AudienceSourceUnavailable(
                f"Configured shared audience table '{self._table}' is not reachable or "
                f"the App service principal lacks SELECT. Refusing to fall back to a "
                f"different audience. Underlying error: {exc}"
            ) from exc

    def _distribution(self, audience_id: str, column: str) -> list[Distribution]:
        rows = self._db.execute(
            f"SELECT {column} AS label, COUNT(*) AS count FROM {self._table} "
            f"WHERE audience_id = :aid GROUP BY {column} ORDER BY count DESC",
            {"aid": audience_id},
        )
        return [
            Distribution(label=str(r["label"]), count=int(r["count"])) for r in rows
        ]

    def list_audiences(self) -> list[AudienceSummary]:
        rows = self._db.execute(
            f"SELECT audience_id, ANY_VALUE(audience_version) AS audience_version, "
            f"COUNT(*) AS member_count FROM {self._table} GROUP BY audience_id"
        )
        return [
            AudienceSummary(
                audience_id=r["audience_id"],
                audience_name=r["audience_id"],
                audience_version=r.get("audience_version") or "shared",
                source_type="SHARED_TABLE",
                source_workspace="shared",
                source_table=self._table,
                member_count=int(r["member_count"]),
            )
            for r in rows
        ]

    def get_audience(
        self, audience_id: str, version: str | None = None
    ) -> AudienceDetail:
        rows = self._db.execute(
            f"SELECT COUNT(*) AS c FROM {self._table} WHERE audience_id = :aid",
            {"aid": audience_id},
        )
        count = int(rows[0]["c"]) if rows else 0
        if count == 0:
            raise AudienceNotFound(audience_id)
        return AudienceDetail(
            audience_id=audience_id,
            audience_name=audience_id,
            audience_version=version or "shared",
            source_type="SHARED_TABLE",
            source_workspace="shared",
            source_table=self._table,
            member_count=count,
            account_status_distribution=self._distribution(
                audience_id, "account_status"
            ),
            preferred_channel_distribution=self._distribution(
                audience_id, "preferred_channel"
            ),
            loyalty_distribution=self._distribution(audience_id, "loyalty_status"),
        )

    def get_members(
        self, audience_id: str, version: str | None = None
    ) -> list[AudienceMember]:
        rows = self._db.execute(
            f"SELECT customer_id, first_name, last_name, email, phone, country, "
            f"state_province, metro_area, loyalty_status, account_status, "
            f"preferred_channel, customer_segment "
            f"FROM {self._table} WHERE audience_id = :aid ORDER BY customer_id",
            {"aid": audience_id},
        )
        return [AudienceMember(**r) for r in rows]
