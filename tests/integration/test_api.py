"""API integration tests over the real FastAPI app + live warehouse."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def created_campaign(client, db):
    """Create a throwaway campaign; clean up its rows afterwards."""
    resp = client.post(
        "/api/campaigns",
        json={
            "campaign_name": "IT winback",
            "audience_id": "AUD-LAPSED-HIGHVALUE",
            "channel": "APP_PUSH",
            "offer_id": "OFFER-020",
            "message_title": "We miss you",
            "message_body": "20% off",
            "deep_link": "app://home",
        },
    )
    assert resp.status_code == 200, resp.text
    cid = resp.json()["campaign_id"]
    yield cid
    # Cleanup App-owned rows for this campaign only.
    c = db.config
    for tbl, col in [
        ("app_delivery_event", "campaign_id"),
        ("app_dispatch_run", "campaign_id"),
        ("app_campaign_approval", "campaign_id"),
        ("app_audit_log", "resource_id"),
        ("app_campaign", "campaign_id"),
    ]:
        db.execute(f"DELETE FROM {c.table(tbl)} WHERE {col} = :id", {"id": cid})


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_system_config(client):
    r = client.get("/api/system/config")
    assert r.status_code == 200
    body = r.json()
    assert body["audience_source_mode"] == "local_snapshot"
    assert body["warehouse_configured"] is True
    assert "Synthetic data" in body["demo_banner"]


def test_list_audiences(client):
    r = client.get("/api/audiences")
    assert r.status_code == 200
    audiences = r.json()
    assert len(audiences) >= 3
    assert all(a["source_type"] == "SYNTHETIC_SNAPSHOT" for a in audiences)


def test_members_masked_by_default_and_revealed(client):
    masked = client.get("/api/audiences/AUD-LAPSED-HIGHVALUE/members?limit=5").json()
    assert masked, "expected members"
    assert any(m["email"] and "***" in m["email"] for m in masked)

    revealed = client.get(
        "/api/audiences/AUD-LAPSED-HIGHVALUE/members?limit=5&reveal=true"
    ).json()
    assert any(m["email"] and "@example.com" in m["email"] and "***" not in m["email"] for m in revealed)


def test_missing_audience_404(client):
    assert client.get("/api/audiences/NOPE").status_code == 404


def test_list_offers(client):
    offers = client.get("/api/offers").json()
    assert any(o["offer_id"] == "OFFER-020" for o in offers)


def test_full_lifecycle_and_metrics(client, created_campaign):
    cid = created_campaign
    prev = client.post(f"/api/campaigns/{cid}/preview").json()
    assert prev["audience_size"] == 2000
    assert prev["eligible"] > 0
    assert prev["skipped_inactive"] > 0  # consent/status guardrail visible

    assert client.post(f"/api/campaigns/{cid}/submit").json()["status"] == "PENDING_APPROVAL"
    assert client.post(f"/api/campaigns/{cid}/approve", json={"comment": "ok"}).json()["status"] == "APPROVED"

    run = client.post(f"/api/campaigns/{cid}/dispatch").json()
    assert run["status"] == "COMPLETED"
    assert run["success_count"] > 0
    assert run["eligible_count"] == prev["eligible"]

    metrics = client.get(f"/api/campaigns/{cid}/metrics").json()
    assert metrics["sent"] == run["success_count"]
    assert 0.0 <= metrics["open_rate"] <= 1.0

    audit = client.get(f"/api/campaigns/{cid}/audit").json()
    actions = {a["action"] for a in audit}
    assert "CREATE" in actions and "DISPATCH" in actions


def test_dispatch_draft_returns_409(client):
    r = client.post("/api/campaigns/CMP-SEED-DRAFT/dispatch")
    assert r.status_code == 409
    assert r.json()["error_code"] == "INVALID_CAMPAIGN_STATE"


def test_idempotent_redispatch_returns_same_run(client, created_campaign):
    cid = created_campaign
    # created_campaign already dispatched in the lifecycle test (module scope);
    # a repeat returns the original completed run rather than creating a new one.
    first = client.get(f"/api/campaigns/{cid}/dispatch-runs").json()
    completed = [r for r in first if r["status"] == "COMPLETED"]
    assert completed, "expected a completed run from the lifecycle test"
    again = client.post(f"/api/campaigns/{cid}/dispatch").json()
    assert again["dispatch_run_id"] == completed[0]["dispatch_run_id"]


def test_missing_campaign_404(client):
    assert client.get("/api/campaigns/NOPE").status_code == 404
