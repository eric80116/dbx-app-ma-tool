"""Data-contract tests against the live App schema."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

REQUIRED_TABLES = [
    "app_audience_catalog",
    "app_audience_members",
    "app_channel_consent",
    "app_offer_catalog",
    "app_campaign",
    "app_campaign_approval",
    "app_dispatch_run",
    "app_delivery_event",
    "app_audit_log",
]


def test_required_tables_exist(db):
    rows = db.execute(
        f"SHOW TABLES IN {db.config.schema_fqn}"
    )
    names = {r["tableName"] for r in rows}
    for t in REQUIRED_TABLES:
        assert t in names, f"missing table {t}"


def test_audience_members_have_required_columns(db):
    rows = db.execute(f"DESCRIBE TABLE {db.config.table('app_audience_members')}")
    cols = {r["col_name"] for r in rows}
    for required in [
        "customer_id", "email", "phone", "account_status", "preferred_channel",
        "customer_segment", "audience_id", "audience_version", "source_type",
    ]:
        assert required in cols


def test_seeded_data_marked_synthetic(db):
    rows = db.execute(
        f"SELECT COUNT(*) AS c FROM {db.config.table('app_audience_members')} "
        f"WHERE source_type <> 'SYNTHETIC_SNAPSHOT'"
    )
    assert int(rows[0]["c"]) == 0


def test_catalog_member_count_matches_members(db):
    cat = db.execute(
        f"SELECT audience_id, member_count FROM {db.config.table('app_audience_catalog')}"
    )
    for row in cat:
        actual = db.execute(
            f"SELECT COUNT(*) AS c FROM {db.config.table('app_audience_members')} "
            f"WHERE audience_id = :aid",
            {"aid": row["audience_id"]},
        )
        assert int(actual[0]["c"]) == int(row["member_count"]), row["audience_id"]


def test_customer_id_unique_within_audience(db):
    dupes = db.execute(
        f"SELECT audience_id, audience_version, customer_id, COUNT(*) AS c "
        f"FROM {db.config.table('app_audience_members')} "
        f"GROUP BY audience_id, audience_version, customer_id HAVING COUNT(*) > 1 LIMIT 5"
    )
    assert dupes == []


def test_consent_covers_every_distinct_customer(db):
    rows = db.execute(
        f"SELECT COUNT(*) AS c FROM ("
        f"  SELECT DISTINCT customer_id FROM {db.config.table('app_audience_members')} m "
        f"  LEFT ANTI JOIN {db.config.table('app_channel_consent')} c USING (customer_id)"
        f")"
    )
    assert int(rows[0]["c"]) == 0


def test_app_tables_only_in_configured_schema(db):
    """The App owns tables only under <target_catalog>.<app_schema> — never CMEG."""
    c = db.config
    rows = db.execute(f"SHOW TABLES IN {c.schema_fqn}")
    for r in rows:
        assert r.get("database", c.app_schema) in (c.app_schema, None)
    # And the configured schema is the App-owned one, not a CMEG catalog.
    assert "cmeg" not in c.target_catalog.lower()
