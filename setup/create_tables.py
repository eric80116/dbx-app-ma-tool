"""Create the App-owned catalog/schema and Delta tables.

Idempotent (CREATE ... IF NOT EXISTS). Only ever writes to the configured App schema
(`<target_catalog>.<app_schema>`); never touches any CMEG source object.
"""

from __future__ import annotations

from ma_app.backend.db import Db

# Ordered DDL. {t} is substituted with the fully-qualified table name.
TABLES: dict[str, str] = {
    "app_audience_catalog": """
        audience_id STRING, audience_name STRING, audience_version STRING,
        source_type STRING, source_workspace STRING, source_table STRING,
        member_count INT, description STRING, created_at TIMESTAMP,
        last_refreshed_at TIMESTAMP, is_active BOOLEAN
    """,
    "app_audience_members": """
        customer_id STRING, household_id STRING, first_name STRING, last_name STRING,
        email STRING, phone STRING, country STRING, state_province STRING,
        metro_area STRING, loyalty_status STRING, loyalty_join_date DATE,
        account_status STRING, preferred_channel STRING, customer_segment STRING,
        date_created DATE, last_updated TIMESTAMP,
        audience_id STRING, audience_version STRING, source_type STRING,
        loaded_at TIMESTAMP
    """,
    "app_channel_consent": """
        customer_id STRING, app_push_opt_in BOOLEAN, sms_opt_in BOOLEAN,
        email_opt_in BOOLEAN, do_not_contact BOOLEAN, consent_updated_at TIMESTAMP,
        consent_source STRING
    """,
    "app_offer_catalog": """
        offer_id STRING, offer_name STRING, offer_type STRING,
        discount_value DECIMAL(18,2), min_spend DECIMAL(18,2), valid_from DATE,
        valid_to DATE, eligible_channel STRING, active_flag BOOLEAN,
        created_at TIMESTAMP
    """,
    "app_campaign": """
        campaign_id STRING, audience_id STRING, audience_version STRING,
        campaign_name STRING, channel STRING, offer_id STRING, message_title STRING,
        message_body STRING, deep_link STRING, scheduled_at TIMESTAMP, status STRING,
        created_by STRING, approved_by STRING, created_at TIMESTAMP,
        updated_at TIMESTAMP, idempotency_key STRING
    """,
    "app_campaign_approval": """
        approval_id STRING, campaign_id STRING, action STRING, actor STRING,
        comment STRING, created_at TIMESTAMP
    """,
    "app_dispatch_run": """
        dispatch_run_id STRING, campaign_id STRING, started_at TIMESTAMP,
        finished_at TIMESTAMP, status STRING, requested_count INT, eligible_count INT,
        success_count INT, failure_count INT, skipped_count INT, error_message STRING,
        idempotency_key STRING
    """,
    "app_delivery_event": """
        delivery_event_id STRING, dispatch_run_id STRING, campaign_id STRING,
        customer_id STRING, channel STRING, event_type STRING, event_ts TIMESTAMP,
        provider_message_id STRING, failure_reason STRING, created_at TIMESTAMP
    """,
    "app_audit_log": """
        audit_id STRING, actor STRING, action STRING, resource_type STRING,
        resource_id STRING, metadata_json STRING, created_at TIMESTAMP
    """,
}


def create_all(db: Db) -> list[str]:
    c = db.config
    created: list[str] = []
    db.execute(f"CREATE CATALOG IF NOT EXISTS {c.target_catalog}")
    db.execute(f"CREATE SCHEMA IF NOT EXISTS {c.schema_fqn}")
    for name, cols in TABLES.items():
        fqn = c.table(name)
        db.execute(
            f"CREATE TABLE IF NOT EXISTS {fqn} ({cols.strip()}) USING DELTA "
            f"TBLPROPERTIES ('app'='ma_orchestration_demo', 'data'='synthetic')"
        )
        created.append(fqn)
    return created


def main() -> None:
    from _bootstrap import get_db  # type: ignore

    db = get_db()
    created = create_all(db)
    print(f"Created/verified {len(created)} tables in {db.config.schema_fqn}:")
    for t in created:
        print(f"  - {t}")


if __name__ == "__main__":
    main()
