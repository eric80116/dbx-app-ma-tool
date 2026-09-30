"""Default audience repository: reads the local synthetic snapshot in this workspace.

Reads `app_audience_catalog` + `app_audience_members` from the App-owned schema. This
is a SYNTHETIC_SNAPSHOT — it is NOT a native Campaign Agents output and the App does
not call any CustomerLake API.
"""

from __future__ import annotations

from ..db import Db
from ..models import AudienceDetail, AudienceMember, AudienceSummary, Distribution
from .interface import AudienceNotFound


class LocalSnapshotAudienceRepository:
    def __init__(self, db: Db):
        self._db = db
        self._catalog_tbl = db.config.table("app_audience_catalog")
        self._members_tbl = db.config.table("app_audience_members")

    def list_audiences(self) -> list[AudienceSummary]:
        rows = self._db.execute(
            f"SELECT audience_id, audience_name, audience_version, source_type, "
            f"source_workspace, source_table, member_count, description, "
            f"CAST(last_refreshed_at AS STRING) AS last_refreshed_at, is_active "
            f"FROM {self._catalog_tbl} WHERE is_active = true "
            f"ORDER BY audience_name"
        )
        return [AudienceSummary(**r) for r in rows]

    def _get_summary(self, audience_id: str) -> AudienceSummary:
        rows = self._db.execute(
            f"SELECT audience_id, audience_name, audience_version, source_type, "
            f"source_workspace, source_table, member_count, description, "
            f"CAST(last_refreshed_at AS STRING) AS last_refreshed_at, is_active "
            f"FROM {self._catalog_tbl} WHERE audience_id = :aid LIMIT 1",
            {"aid": audience_id},
        )
        if not rows:
            raise AudienceNotFound(audience_id)
        return AudienceSummary(**rows[0])

    def _distribution(self, audience_id: str, column: str) -> list[Distribution]:
        rows = self._db.execute(
            f"SELECT {column} AS label, COUNT(*) AS count FROM {self._members_tbl} "
            f"WHERE audience_id = :aid GROUP BY {column} ORDER BY count DESC",
            {"aid": audience_id},
        )
        return [
            Distribution(label=str(r["label"]), count=int(r["count"])) for r in rows
        ]

    def get_audience(
        self, audience_id: str, version: str | None = None
    ) -> AudienceDetail:
        summary = self._get_summary(audience_id)
        return AudienceDetail(
            **summary.model_dump(),
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
        where = "audience_id = :aid"
        params: dict = {"aid": audience_id}
        if version:
            where += " AND audience_version = :ver"
            params["ver"] = version
        rows = self._db.execute(
            f"SELECT customer_id, first_name, last_name, email, phone, country, "
            f"state_province, metro_area, loyalty_status, account_status, "
            f"preferred_channel, customer_segment "
            f"FROM {self._members_tbl} WHERE {where} ORDER BY customer_id",
            params,
        )
        return [AudienceMember(**r) for r in rows]
