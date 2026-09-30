"""Pydantic models and enums for the MA orchestration App.

Convention (APX 3-model pattern): `Entity` (internal), `EntityIn` (request),
`EntityOut` (response). Enums are string enums so they serialize cleanly to JSON
and to the generated TypeScript client.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from .. import __version__


class VersionOut(BaseModel):
    version: str

    @classmethod
    def from_metadata(cls):
        return cls(version=__version__)


# --------------------------------------------------------------------------- #
# Enums
# --------------------------------------------------------------------------- #
class Channel(str, Enum):
    APP_PUSH = "APP_PUSH"
    SMS = "SMS"
    COUPON = "COUPON"


class CampaignStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class ApprovalAction(str, Enum):
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class DeliveryEventType(str, Enum):
    REQUESTED = "REQUESTED"
    SKIPPED_NO_CONSENT = "SKIPPED_NO_CONSENT"
    SKIPPED_INACTIVE = "SKIPPED_INACTIVE"
    SKIPPED_INVALID_CONTACT = "SKIPPED_INVALID_CONTACT"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    OPENED = "OPENED"
    CLICKED = "CLICKED"
    REDEEMED = "REDEEMED"
    FAILED = "FAILED"


class DispatchStatus(str, Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# --------------------------------------------------------------------------- #
# Audience
# --------------------------------------------------------------------------- #
class AudienceSummary(BaseModel):
    audience_id: str
    audience_name: str
    audience_version: str
    source_type: str
    source_workspace: str
    source_table: str
    member_count: int
    description: str | None = None
    last_refreshed_at: str | None = None
    is_active: bool = True


class Distribution(BaseModel):
    label: str
    count: int


class AudienceDetail(AudienceSummary):
    account_status_distribution: list[Distribution] = Field(default_factory=list)
    preferred_channel_distribution: list[Distribution] = Field(default_factory=list)
    loyalty_distribution: list[Distribution] = Field(default_factory=list)


class AudienceMember(BaseModel):
    customer_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    country: str | None = None
    state_province: str | None = None
    metro_area: str | None = None
    loyalty_status: str | None = None
    account_status: str | None = None
    preferred_channel: str | None = None
    customer_segment: str | None = None


# --------------------------------------------------------------------------- #
# Offers
# --------------------------------------------------------------------------- #
class OfferOut(BaseModel):
    offer_id: str
    offer_name: str
    offer_type: str
    discount_value: float | None = None
    min_spend: float | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    eligible_channel: str | None = None
    active_flag: bool = True


# --------------------------------------------------------------------------- #
# Campaigns
# --------------------------------------------------------------------------- #
class CampaignIn(BaseModel):
    campaign_name: str = Field(min_length=1, max_length=200)
    audience_id: str
    audience_version: str | None = None
    channel: Channel
    offer_id: str | None = None
    message_title: str | None = None
    message_body: str | None = None
    deep_link: str | None = None
    scheduled_at: str | None = None  # ISO-8601 UTC


class CampaignPatch(BaseModel):
    campaign_name: str | None = None
    channel: Channel | None = None
    offer_id: str | None = None
    message_title: str | None = None
    message_body: str | None = None
    deep_link: str | None = None
    scheduled_at: str | None = None


class CampaignOut(BaseModel):
    campaign_id: str
    audience_id: str
    audience_version: str | None = None
    campaign_name: str
    channel: str
    offer_id: str | None = None
    message_title: str | None = None
    message_body: str | None = None
    deep_link: str | None = None
    scheduled_at: str | None = None
    status: str
    created_by: str | None = None
    approved_by: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    idempotency_key: str | None = None


# --------------------------------------------------------------------------- #
# Approvals / audit
# --------------------------------------------------------------------------- #
class ApprovalOut(BaseModel):
    approval_id: str
    campaign_id: str
    action: str
    actor: str | None = None
    comment: str | None = None
    created_at: str | None = None


class ApprovalActionIn(BaseModel):
    comment: str | None = None


class ScheduleIn(BaseModel):
    scheduled_at: str  # ISO-8601 UTC, e.g. "2026-10-15 14:30:00"


class AuditOut(BaseModel):
    audit_id: str
    actor: str | None = None
    action: str
    resource_type: str | None = None
    resource_id: str | None = None
    metadata_json: str | None = None
    created_at: str | None = None


# --------------------------------------------------------------------------- #
# Eligibility / preview
# --------------------------------------------------------------------------- #
class EligibilityPreview(BaseModel):
    audience_size: int
    eligible: int
    skipped_no_consent: int
    skipped_inactive: int
    skipped_invalid_contact: int
    already_dispatched: int


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
class DispatchRunOut(BaseModel):
    dispatch_run_id: str
    campaign_id: str
    started_at: str | None = None
    finished_at: str | None = None
    status: str
    requested_count: int = 0
    eligible_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    skipped_count: int = 0
    error_message: str | None = None
    idempotency_key: str | None = None


class DeliveryEventOut(BaseModel):
    delivery_event_id: str
    dispatch_run_id: str | None = None
    campaign_id: str
    customer_id: str | None = None
    channel: str | None = None
    event_type: str
    event_ts: str | None = None
    provider_message_id: str | None = None
    failure_reason: str | None = None


# --------------------------------------------------------------------------- #
# Metrics / dashboard
# --------------------------------------------------------------------------- #
class CampaignMetrics(BaseModel):
    campaign_id: str
    requested: int = 0
    eligible: int = 0
    skipped: int = 0
    sent: int = 0
    delivered: int = 0
    opened: int = 0
    clicked: int = 0
    redeemed: int = 0
    failed: int = 0
    failure_rate: float = 0.0
    open_rate: float = 0.0
    click_through_rate: float = 0.0
    redemption_rate: float = 0.0


class DashboardStats(BaseModel):
    total_audiences: int = 0
    total_campaigns: int = 0
    draft_campaigns: int = 0
    pending_approvals: int = 0
    scheduled_campaigns: int = 0
    completed_dispatches: int = 0
    total_delivered: int = 0
    open_rate: float = 0.0
    click_rate: float = 0.0
    redemption_rate: float = 0.0
    recent_activity: list[AuditOut] = Field(default_factory=list)


class SystemConfigOut(BaseModel):
    app_name: str
    target_catalog: str
    app_schema: str
    audience_source_mode: str
    audience_table: str
    warehouse_configured: bool
    reveal_pii_allowed: bool
    scheduler_enabled: bool = False
    demo_banner: str = "Synthetic data / mock activation only"


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: dict = Field(default_factory=dict)
