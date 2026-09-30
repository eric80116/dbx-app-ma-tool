"""Campaign lifecycle, preview, dispatch, metrics, audit endpoints."""

from __future__ import annotations

from fastapi import HTTPException

from ..core import Dependencies, create_router
from ..db import DbDependency
from ..models import (
    ApprovalActionIn,
    ApprovalOut,
    AuditOut,
    CampaignIn,
    CampaignMetrics,
    CampaignOut,
    CampaignPatch,
    DeliveryEventOut,
    DispatchRunOut,
    EligibilityPreview,
    ScheduleIn,
)
from ..repositories import AppRepository
from ..services import CampaignService
from ._common import actor_from

router = create_router()


def _require_campaign(db, campaign_id: str) -> CampaignOut:
    campaign = AppRepository(db).get_campaign(campaign_id)
    if campaign is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "CAMPAIGN_NOT_FOUND",
                "message": f"Campaign '{campaign_id}' not found.",
                "details": {},
            },
        )
    return campaign


@router.get("/campaigns", response_model=list[CampaignOut], operation_id="listCampaigns")
def list_campaigns(db: DbDependency):
    return AppRepository(db).list_campaigns()


@router.post("/campaigns", response_model=CampaignOut, operation_id="createCampaign")
def create_campaign(body: CampaignIn, db: DbDependency, headers: Dependencies.Headers):
    return CampaignService(db).create(body, actor_from(headers))


@router.get("/campaigns/{campaign_id}", response_model=CampaignOut, operation_id="getCampaign")
def get_campaign(campaign_id: str, db: DbDependency):
    return _require_campaign(db, campaign_id)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignOut, operation_id="updateCampaign")
def update_campaign(
    campaign_id: str, body: CampaignPatch, db: DbDependency, headers: Dependencies.Headers
):
    campaign = _require_campaign(db, campaign_id)
    return CampaignService(db).update(campaign, body, actor_from(headers))


@router.post("/campaigns/{campaign_id}/submit", response_model=CampaignOut, operation_id="submitCampaign")
def submit_campaign(campaign_id: str, db: DbDependency, headers: Dependencies.Headers):
    campaign = _require_campaign(db, campaign_id)
    return CampaignService(db).submit(campaign, actor_from(headers))


@router.post("/campaigns/{campaign_id}/approve", response_model=CampaignOut, operation_id="approveCampaign")
def approve_campaign(
    campaign_id: str, db: DbDependency, headers: Dependencies.Headers, body: ApprovalActionIn | None = None
):
    campaign = _require_campaign(db, campaign_id)
    comment = body.comment if body else None
    return CampaignService(db).approve(campaign, actor_from(headers), comment)


@router.post("/campaigns/{campaign_id}/reject", response_model=CampaignOut, operation_id="rejectCampaign")
def reject_campaign(
    campaign_id: str, db: DbDependency, headers: Dependencies.Headers, body: ApprovalActionIn | None = None
):
    campaign = _require_campaign(db, campaign_id)
    comment = body.comment if body else None
    return CampaignService(db).reject(campaign, actor_from(headers), comment)


@router.post("/campaigns/{campaign_id}/cancel", response_model=CampaignOut, operation_id="cancelCampaign")
def cancel_campaign(
    campaign_id: str, db: DbDependency, headers: Dependencies.Headers, body: ApprovalActionIn | None = None
):
    campaign = _require_campaign(db, campaign_id)
    comment = body.comment if body else None
    return CampaignService(db).cancel(campaign, actor_from(headers), comment)


@router.post("/campaigns/{campaign_id}/schedule", response_model=CampaignOut, operation_id="scheduleCampaign")
def schedule_campaign(
    campaign_id: str, body: ScheduleIn, db: DbDependency, headers: Dependencies.Headers
):
    campaign = _require_campaign(db, campaign_id)
    return CampaignService(db).schedule(campaign, body.scheduled_at, actor_from(headers))


@router.post("/campaigns/{campaign_id}/preview", response_model=EligibilityPreview, operation_id="previewCampaign")
def preview_campaign(campaign_id: str, db: DbDependency):
    campaign = _require_campaign(db, campaign_id)
    return CampaignService(db).preview(campaign)


@router.post("/campaigns/{campaign_id}/dispatch", response_model=DispatchRunOut, operation_id="dispatchCampaign")
def dispatch_campaign(campaign_id: str, db: DbDependency, headers: Dependencies.Headers):
    campaign = _require_campaign(db, campaign_id)
    return CampaignService(db).dispatch(campaign, actor_from(headers))


@router.get("/campaigns/{campaign_id}/metrics", response_model=CampaignMetrics, operation_id="getCampaignMetrics")
def campaign_metrics(campaign_id: str, db: DbDependency):
    _require_campaign(db, campaign_id)
    return CampaignService(db).metrics(campaign_id)


@router.get("/campaigns/{campaign_id}/audit", response_model=list[AuditOut], operation_id="getCampaignAudit")
def campaign_audit(campaign_id: str, db: DbDependency):
    _require_campaign(db, campaign_id)
    return AppRepository(db).list_audit(campaign_id)


@router.get("/campaigns/{campaign_id}/approvals", response_model=list[ApprovalOut], operation_id="getCampaignApprovals")
def campaign_approvals(campaign_id: str, db: DbDependency):
    _require_campaign(db, campaign_id)
    return AppRepository(db).list_approvals(campaign_id)


@router.get("/campaigns/{campaign_id}/dispatch-runs", response_model=list[DispatchRunOut], operation_id="getCampaignDispatchRuns")
def campaign_dispatch_runs(campaign_id: str, db: DbDependency):
    _require_campaign(db, campaign_id)
    return AppRepository(db).list_dispatch_runs(campaign_id)


@router.get("/campaigns/{campaign_id}/events", response_model=list[DeliveryEventOut], operation_id="getCampaignEvents")
def campaign_events(campaign_id: str, db: DbDependency, limit: int = 500):
    _require_campaign(db, campaign_id)
    return AppRepository(db).list_delivery_events(campaign_id, limit=limit)
