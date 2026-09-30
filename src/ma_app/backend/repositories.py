"""Delta-table data access for App-owned operational tables.

All state lives in Delta (never in-memory). Identifiers come from config; request
values are bound as parameters. Bulk event inserts use batched multi-row VALUES with
escaped literals (synthetic/derived data only).
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from .db import Db, Ts, bulk_insert_values
from .models import (
    ApprovalOut,
    AuditOut,
    CampaignOut,
    DeliveryEventOut,
    DispatchRunOut,
    OfferOut,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}"


class AppRepository:
    def __init__(self, db: Db):
        self.db = db
        self.c = db.config

    # ------------------------------------------------------------------ offers
    def list_offers(self, active_only: bool = False) -> list[OfferOut]:
        where = "WHERE active_flag = true" if active_only else ""
        rows = self.db.execute(
            f"SELECT offer_id, offer_name, offer_type, CAST(discount_value AS DOUBLE) "
            f"AS discount_value, CAST(min_spend AS DOUBLE) AS min_spend, "
            f"CAST(valid_from AS STRING) AS valid_from, CAST(valid_to AS STRING) AS valid_to, "
            f"eligible_channel, active_flag FROM {self.c.table('app_offer_catalog')} "
            f"{where} ORDER BY offer_id"
        )
        return [OfferOut(**r) for r in rows]

    def get_offer(self, offer_id: str) -> OfferOut | None:
        rows = self.db.execute(
            f"SELECT offer_id, offer_name, offer_type, CAST(discount_value AS DOUBLE) "
            f"AS discount_value, CAST(min_spend AS DOUBLE) AS min_spend, "
            f"CAST(valid_from AS STRING) AS valid_from, CAST(valid_to AS STRING) AS valid_to, "
            f"eligible_channel, active_flag FROM {self.c.table('app_offer_catalog')} "
            f"WHERE offer_id = :oid LIMIT 1",
            {"oid": offer_id},
        )
        return OfferOut(**rows[0]) if rows else None

    def offer_valid_on(self, offer_id: str, on_date: str | None) -> bool:
        offer = self.get_offer(offer_id)
        if offer is None or not offer.active_flag:
            return False
        if on_date is None:
            return True
        day = on_date[:10]
        if offer.valid_from and day < offer.valid_from[:10]:
            return False
        if offer.valid_to and day > offer.valid_to[:10]:
            return False
        return True

    # --------------------------------------------------------------- campaigns
    _CAMPAIGN_COLS = (
        "campaign_id, audience_id, audience_version, campaign_name, channel, offer_id, "
        "message_title, message_body, deep_link, CAST(scheduled_at AS STRING) AS scheduled_at, "
        "status, created_by, approved_by, CAST(created_at AS STRING) AS created_at, "
        "CAST(updated_at AS STRING) AS updated_at, idempotency_key"
    )

    def list_campaigns(self) -> list[CampaignOut]:
        rows = self.db.execute(
            f"SELECT {self._CAMPAIGN_COLS} FROM {self.c.table('app_campaign')} "
            f"ORDER BY created_at DESC"
        )
        return [CampaignOut(**r) for r in rows]

    def get_campaign(self, campaign_id: str) -> CampaignOut | None:
        rows = self.db.execute(
            f"SELECT {self._CAMPAIGN_COLS} FROM {self.c.table('app_campaign')} "
            f"WHERE campaign_id = :cid LIMIT 1",
            {"cid": campaign_id},
        )
        return CampaignOut(**rows[0]) if rows else None

    def insert_campaign(self, values: dict[str, Any]) -> None:
        cols = [
            "campaign_id", "audience_id", "audience_version", "campaign_name", "channel",
            "offer_id", "message_title", "message_body", "deep_link", "scheduled_at",
            "status", "created_by", "approved_by", "created_at", "updated_at",
            "idempotency_key",
        ]
        placeholders = {
            "campaign_id": ":campaign_id", "audience_id": ":audience_id",
            "audience_version": ":audience_version", "campaign_name": ":campaign_name",
            "channel": ":channel", "offer_id": ":offer_id",
            "message_title": ":message_title", "message_body": ":message_body",
            "deep_link": ":deep_link",
            "scheduled_at": "CAST(:scheduled_at AS TIMESTAMP)",
            "status": ":status", "created_by": ":created_by",
            "approved_by": ":approved_by",
            "created_at": "CAST(:created_at AS TIMESTAMP)",
            "updated_at": "CAST(:updated_at AS TIMESTAMP)",
            "idempotency_key": ":idempotency_key",
        }
        col_sql = ", ".join(cols)
        val_sql = ", ".join(placeholders[c] for c in cols)
        self.db.execute(
            f"INSERT INTO {self.c.table('app_campaign')} ({col_sql}) VALUES ({val_sql})",
            values,
        )

    def update_campaign_fields(self, campaign_id: str, fields: dict[str, Any]) -> None:
        if not fields:
            return
        ts_fields = {"scheduled_at"}
        sets = []
        params: dict[str, Any] = {"cid": campaign_id}
        for k, v in fields.items():
            if k in ts_fields:
                sets.append(f"{k} = CAST(:{k} AS TIMESTAMP)")
            else:
                sets.append(f"{k} = :{k}")
            params[k] = v
        sets.append("updated_at = CAST(:updated_at AS TIMESTAMP)")
        params["updated_at"] = _now_iso()
        self.db.execute(
            f"UPDATE {self.c.table('app_campaign')} SET {', '.join(sets)} "
            f"WHERE campaign_id = :cid",
            params,
        )

    def set_status(
        self, campaign_id: str, status: str, approved_by: str | None = None
    ) -> None:
        params: dict[str, Any] = {
            "cid": campaign_id,
            "status": status,
            "updated_at": _now_iso(),
        }
        extra = ""
        if approved_by is not None:
            extra = ", approved_by = :approved_by"
            params["approved_by"] = approved_by
        self.db.execute(
            f"UPDATE {self.c.table('app_campaign')} SET status = :status, "
            f"updated_at = CAST(:updated_at AS TIMESTAMP){extra} "
            f"WHERE campaign_id = :cid",
            params,
        )

    def rotate_idempotency_key(self, campaign_id: str) -> str:
        key = new_id("IDEM")
        self.db.execute(
            f"UPDATE {self.c.table('app_campaign')} SET idempotency_key = :k, "
            f"updated_at = CAST(:u AS TIMESTAMP) WHERE campaign_id = :cid",
            {"k": key, "u": _now_iso(), "cid": campaign_id},
        )
        return key

    # --------------------------------------------------------------- approvals
    def add_approval(
        self, campaign_id: str, action: str, actor: str | None, comment: str | None
    ) -> None:
        self.db.execute(
            f"INSERT INTO {self.c.table('app_campaign_approval')} "
            f"(approval_id, campaign_id, action, actor, comment, created_at) "
            f"VALUES (:id, :cid, :action, :actor, :comment, CAST(:ts AS TIMESTAMP))",
            {
                "id": new_id("APR"),
                "cid": campaign_id,
                "action": action,
                "actor": actor,
                "comment": comment,
                "ts": _now_iso(),
            },
        )

    def list_approvals(self, campaign_id: str) -> list[ApprovalOut]:
        rows = self.db.execute(
            f"SELECT approval_id, campaign_id, action, actor, comment, "
            f"CAST(created_at AS STRING) AS created_at "
            f"FROM {self.c.table('app_campaign_approval')} WHERE campaign_id = :cid "
            f"ORDER BY created_at",
            {"cid": campaign_id},
        )
        return [ApprovalOut(**r) for r in rows]

    # -------------------------------------------------------------------- audit
    def audit(
        self,
        actor: str | None,
        action: str,
        resource_type: str,
        resource_id: str,
        metadata: dict | None = None,
    ) -> None:
        self.db.execute(
            f"INSERT INTO {self.c.table('app_audit_log')} "
            f"(audit_id, actor, action, resource_type, resource_id, metadata_json, created_at) "
            f"VALUES (:id, :actor, :action, :rt, :rid, :meta, CAST(:ts AS TIMESTAMP))",
            {
                "id": new_id("AUD"),
                "actor": actor,
                "action": action,
                "rt": resource_type,
                "rid": resource_id,
                "meta": json.dumps(metadata or {}),
                "ts": _now_iso(),
            },
        )

    def list_audit(self, campaign_id: str) -> list[AuditOut]:
        rows = self.db.execute(
            f"SELECT audit_id, actor, action, resource_type, resource_id, metadata_json, "
            f"CAST(created_at AS STRING) AS created_at FROM {self.c.table('app_audit_log')} "
            f"WHERE resource_id = :rid ORDER BY created_at",
            {"rid": campaign_id},
        )
        return [AuditOut(**r) for r in rows]

    def recent_audit(self, limit: int = 15) -> list[AuditOut]:
        rows = self.db.execute(
            f"SELECT audit_id, actor, action, resource_type, resource_id, metadata_json, "
            f"CAST(created_at AS STRING) AS created_at FROM {self.c.table('app_audit_log')} "
            f"ORDER BY created_at DESC LIMIT {int(limit)}"
        )
        return [AuditOut(**r) for r in rows]

    # -------------------------------------------------------------- consent
    def get_consent_map(self, customer_ids: Sequence[str]) -> dict[str, dict]:
        if not customer_ids:
            return {}
        rows = self.db.execute(
            f"SELECT customer_id, app_push_opt_in, sms_opt_in, email_opt_in, do_not_contact "
            f"FROM {self.c.table('app_channel_consent')}"
        )
        wanted = set(customer_ids)
        return {r["customer_id"]: r for r in rows if r["customer_id"] in wanted}

    # ------------------------------------------------------------ dispatch runs
    def find_completed_run_by_key(self, idempotency_key: str) -> DispatchRunOut | None:
        rows = self.db.execute(
            f"SELECT {self._RUN_COLS} FROM {self.c.table('app_dispatch_run')} "
            f"WHERE idempotency_key = :k AND status = 'COMPLETED' "
            f"ORDER BY started_at DESC LIMIT 1",
            {"k": idempotency_key},
        )
        return DispatchRunOut(**rows[0]) if rows else None

    _RUN_COLS = (
        "dispatch_run_id, campaign_id, CAST(started_at AS STRING) AS started_at, "
        "CAST(finished_at AS STRING) AS finished_at, status, requested_count, "
        "eligible_count, success_count, failure_count, skipped_count, error_message, "
        "idempotency_key"
    )

    def create_dispatch_run(
        self, campaign_id: str, idempotency_key: str | None, requested_count: int
    ) -> str:
        run_id = new_id("RUN")
        self.db.execute(
            f"INSERT INTO {self.c.table('app_dispatch_run')} "
            f"(dispatch_run_id, campaign_id, started_at, finished_at, status, "
            f"requested_count, eligible_count, success_count, failure_count, "
            f"skipped_count, error_message, idempotency_key) VALUES "
            f"(:id, :cid, CAST(:ts AS TIMESTAMP), NULL, 'RUNNING', :req, 0, 0, 0, 0, "
            f"NULL, :k)",
            {
                "id": run_id,
                "cid": campaign_id,
                "ts": _now_iso(),
                "req": requested_count,
                "k": idempotency_key,
            },
        )
        return run_id

    def finish_dispatch_run(
        self,
        run_id: str,
        status: str,
        *,
        eligible: int,
        success: int,
        failure: int,
        skipped: int,
        error_message: str | None = None,
    ) -> None:
        self.db.execute(
            f"UPDATE {self.c.table('app_dispatch_run')} SET status = :status, "
            f"finished_at = CAST(:ts AS TIMESTAMP), eligible_count = :el, "
            f"success_count = :su, failure_count = :fa, skipped_count = :sk, "
            f"error_message = :err WHERE dispatch_run_id = :id",
            {
                "status": status,
                "ts": _now_iso(),
                "el": eligible,
                "su": success,
                "fa": failure,
                "sk": skipped,
                "err": error_message,
                "id": run_id,
            },
        )

    def list_dispatch_runs(self, campaign_id: str) -> list[DispatchRunOut]:
        rows = self.db.execute(
            f"SELECT {self._RUN_COLS} FROM {self.c.table('app_dispatch_run')} "
            f"WHERE campaign_id = :cid ORDER BY started_at DESC",
            {"cid": campaign_id},
        )
        return [DispatchRunOut(**r) for r in rows]

    # ----------------------------------------------------------- delivery events
    def dispatched_customer_ids(self, campaign_id: str) -> set[str]:
        rows = self.db.execute(
            f"SELECT DISTINCT customer_id FROM {self.c.table('app_delivery_event')} "
            f"WHERE campaign_id = :cid AND event_type = 'SENT'",
            {"cid": campaign_id},
        )
        return {r["customer_id"] for r in rows if r["customer_id"]}

    def insert_delivery_events(self, rows: Sequence[dict[str, Any]]) -> None:
        """Batched multi-row insert. Values are synthetic/derived (safe to render)."""
        if not rows:
            return
        cols = [
            "delivery_event_id", "dispatch_run_id", "campaign_id", "customer_id",
            "channel", "event_type", "event_ts", "provider_message_id",
            "failure_reason", "created_at",
        ]
        batch = 500
        table = self.c.table("app_delivery_event")
        for start in range(0, len(rows), batch):
            chunk = rows[start : start + batch]
            tuples: list[list[Any]] = []
            for r in chunk:
                tuples.append(
                    [
                        r["delivery_event_id"], r["dispatch_run_id"], r["campaign_id"],
                        r["customer_id"], r["channel"], r["event_type"],
                        Ts(r["event_ts"]), r.get("provider_message_id"),
                        r.get("failure_reason"), Ts(r["created_at"]),
                    ]
                )
            values = bulk_insert_values(tuples)
            self.db.execute(
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES {values}"
            )

    def list_delivery_events(
        self, campaign_id: str, limit: int | None = None
    ) -> list[DeliveryEventOut]:
        lim = f"LIMIT {int(limit)}" if limit else ""
        rows = self.db.execute(
            f"SELECT delivery_event_id, dispatch_run_id, campaign_id, customer_id, channel, "
            f"event_type, CAST(event_ts AS STRING) AS event_ts, provider_message_id, "
            f"failure_reason FROM {self.c.table('app_delivery_event')} "
            f"WHERE campaign_id = :cid ORDER BY event_ts DESC {lim}",
            {"cid": campaign_id},
        )
        return [DeliveryEventOut(**r) for r in rows]

    def event_counts(self, campaign_id: str) -> dict[str, int]:
        rows = self.db.execute(
            f"SELECT event_type, COUNT(*) AS c FROM {self.c.table('app_delivery_event')} "
            f"WHERE campaign_id = :cid GROUP BY event_type",
            {"cid": campaign_id},
        )
        return {r["event_type"]: int(r["c"]) for r in rows}

    # -------------------------------------------------------------- dashboard
    def campaign_status_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            f"SELECT status, COUNT(*) AS c FROM {self.c.table('app_campaign')} "
            f"GROUP BY status"
        )
        return {r["status"]: int(r["c"]) for r in rows}

    def global_event_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            f"SELECT event_type, COUNT(*) AS c FROM {self.c.table('app_delivery_event')} "
            f"GROUP BY event_type"
        )
        return {r["event_type"]: int(r["c"]) for r in rows}

    def completed_dispatch_count(self) -> int:
        rows = self.db.execute(
            f"SELECT COUNT(*) AS c FROM {self.c.table('app_dispatch_run')} "
            f"WHERE status = 'COMPLETED'"
        )
        return int(rows[0]["c"]) if rows else 0


