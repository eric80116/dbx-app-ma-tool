"""Scheduling integration tests (live warehouse, but NO live Databricks jobs).

Uses a fake Scheduler injected into CampaignService so we exercise the real state
transition + audit + Delta writes without creating actual jobs.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


class _FakeScheduler:
    def __init__(self):
        self.scheduled: list[tuple[str, str]] = []
        self.cancelled: list[str] = []

    def schedule(self, campaign_id, scheduled_at):
        self.scheduled.append((campaign_id, scheduled_at))
        return 999999

    def cancel(self, campaign_id):
        self.cancelled.append(campaign_id)
        return True


@pytest.fixture
def approved_campaign(client, db):
    resp = client.post(
        "/api/campaigns",
        json={
            "campaign_name": "Sched IT",
            "audience_id": "AUD-PUSH-ENGAGED",
            "channel": "APP_PUSH",
            "message_title": "hi",
        },
    )
    cid = resp.json()["campaign_id"]
    client.post(f"/api/campaigns/{cid}/submit")
    client.post(f"/api/campaigns/{cid}/approve", json={"comment": None})
    yield cid
    c = db.config
    for tbl, col in [
        ("app_campaign_approval", "campaign_id"),
        ("app_audit_log", "resource_id"),
        ("app_campaign", "campaign_id"),
    ]:
        db.execute(f"DELETE FROM {c.table(tbl)} WHERE {col} = :id", {"id": cid})


def test_schedule_transitions_to_scheduled_and_arms_job(db, approved_campaign):
    from ma_app.backend.services import CampaignService

    fake = _FakeScheduler()
    svc = CampaignService(db, scheduler=fake)
    campaign = svc.repo.get_campaign(approved_campaign)
    assert campaign is not None
    assert campaign.status == "APPROVED"

    out = svc.schedule(campaign, "2026-10-15 14:30:00", actor="tester")
    assert out.status == "SCHEDULED"
    assert out.scheduled_at is not None
    assert fake.scheduled == [(approved_campaign, "2026-10-15 14:30:00")]

    # A SCHEDULE audit record was written.
    audit = svc.repo.list_audit(approved_campaign)
    assert any(a.action == "SCHEDULE" for a in audit)


def test_cancel_scheduled_removes_job(db, approved_campaign):
    from ma_app.backend.services import CampaignService

    fake = _FakeScheduler()
    svc = CampaignService(db, scheduler=fake)
    campaign = svc.repo.get_campaign(approved_campaign)
    assert campaign is not None
    svc.schedule(campaign, "2026-10-15 14:30:00", actor="tester")

    scheduled = svc.repo.get_campaign(approved_campaign)
    assert scheduled is not None
    svc.cancel(scheduled, actor="tester", comment=None)
    assert approved_campaign in fake.cancelled
    final = svc.repo.get_campaign(approved_campaign)
    assert final is not None and final.status == "CANCELLED"
