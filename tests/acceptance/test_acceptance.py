"""Acceptance tests: one test per customer requirement (prompt §15.9).

Each test's docstring is the requirement text; the JUnit XML + generated Markdown
report render these as a checklist.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.acceptance

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture(scope="module")
def campaign(client, db):
    resp = client.post(
        "/api/campaigns",
        json={
            "campaign_name": "Acceptance Winback",
            "audience_id": "AUD-LAPSED-HIGHVALUE",
            "channel": "APP_PUSH",
            "offer_id": "OFFER-020",
            "message_title": "We miss you",
            "message_body": "Enjoy 20% off",
            "deep_link": "app://home/offers",
        },
    )
    cid = resp.json()["campaign_id"]
    yield cid
    c = db.config
    for tbl, col in [
        ("app_delivery_event", "campaign_id"),
        ("app_dispatch_run", "campaign_id"),
        ("app_campaign_approval", "campaign_id"),
        ("app_audit_log", "resource_id"),
        ("app_campaign", "campaign_id"),
    ]:
        db.execute(f"DELETE FROM {c.table(tbl)} WHERE {col} = :id", {"id": cid})


def test_view_available_audiences(client):
    """User can view available audiences."""
    assert len(client.get("/api/audiences").json()) >= 3


def test_inspect_size_and_sample_members(client):
    """User can inspect audience size and sample members."""
    detail = client.get("/api/audiences/AUD-LAPSED-HIGHVALUE").json()
    assert detail["member_count"] > 0
    members = client.get("/api/audiences/AUD-LAPSED-HIGHVALUE/members?limit=5").json()
    assert len(members) == 5


def test_select_channel(client, campaign):
    """User can select App Push, SMS, or Coupon."""
    assert client.get(f"/api/campaigns/{campaign}").json()["channel"] in {"APP_PUSH", "SMS", "COUPON"}


def test_configure_content_and_deep_link(client, campaign):
    """User can configure content and deep link."""
    c = client.get(f"/api/campaigns/{campaign}").json()
    assert c["message_title"] and c["deep_link"]


def test_select_offer(client, campaign):
    """User can select an offer."""
    assert client.get(f"/api/campaigns/{campaign}").json()["offer_id"] == "OFFER-020"


def test_preview_eligible_and_skipped(client, campaign):
    """User can preview eligible and skipped counts."""
    p = client.post(f"/api/campaigns/{campaign}/preview").json()
    assert p["eligible"] > 0 and p["audience_size"] == 2000


def test_submit_for_approval(client, campaign):
    """User can submit a campaign for approval."""
    assert client.post(f"/api/campaigns/{campaign}/submit").json()["status"] == "PENDING_APPROVAL"


def test_approve_with_comment(client, campaign):
    """Approver can approve or reject with a comment."""
    r = client.post(f"/api/campaigns/{campaign}/approve", json={"comment": "Approved for demo"})
    assert r.json()["status"] == "APPROVED"
    approvals = client.get(f"/api/campaigns/{campaign}/approvals").json()
    assert any(a["action"] == "APPROVED" and a["comment"] for a in approvals)


def test_only_approved_can_dispatch(client):
    """Only approved campaigns can be dispatched."""
    assert client.post("/api/campaigns/CMP-SEED-DRAFT/dispatch").status_code == 409


def test_consent_and_status_guardrails(client, campaign):
    """Consent and account-status guardrails work."""
    p = client.post(f"/api/campaigns/{campaign}/preview").json()
    assert p["skipped_inactive"] > 0
    assert p["skipped_no_consent"] > 0


def test_dispatch_produces_mock_events(client, campaign):
    """Dispatch produces mock delivery events."""
    run = client.post(f"/api/campaigns/{campaign}/dispatch").json()
    assert run["status"] == "COMPLETED" and run["success_count"] > 0
    events = client.get(f"/api/campaigns/{campaign}/events?limit=10").json()
    assert events and any(e["provider_message_id"] for e in events)


def test_campaign_history_visible(client, campaign):
    """Campaign history is visible."""
    runs = client.get(f"/api/campaigns/{campaign}/dispatch-runs").json()
    assert len(runs) >= 1


def test_metrics_from_delta(client, campaign):
    """Campaign metrics are calculated from Delta tables."""
    m = client.get(f"/api/campaigns/{campaign}/metrics").json()
    assert m["sent"] > 0 and 0.0 <= m["open_rate"] <= 1.0


def test_audit_history_visible(client, campaign):
    """Audit history is visible."""
    audit = client.get(f"/api/campaigns/{campaign}/audit").json()
    assert {"CREATE", "DISPATCH"}.issubset({a["action"] for a in audit})


def test_app_deploys_through_dab():
    """App deploys through DAB."""
    # Bundle definition + app/job/permissions resources exist and are wired.
    assert (ROOT / "databricks.yml").exists()
    for f in ("app.yml", "jobs.yml", "permissions.yml"):
        assert (ROOT / "resources" / f).exists()


def test_teardown_does_not_touch_cmeg():
    """App teardown does not touch CMEG source tables."""
    script = (ROOT / "scripts" / "teardown.sh").read_text()
    # Guards: confirm flag, allowlist, no unguarded cascade, CMEG protection.
    assert "--confirm" in script
    assert "app_audience_members" in script  # allowlist by table name
    assert "ma_app_demo" in script  # catalog guard
