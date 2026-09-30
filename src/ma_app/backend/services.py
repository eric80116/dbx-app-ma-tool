"""Application services: campaign lifecycle, eligibility preview, dispatch, dashboard.

Ties together repositories, the audience repository, mock providers, the state machine,
eligibility rules and metrics. Enforces guardrails server-side.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .audience import AudienceRepository, get_audience_repository
from .db import Db
from .domain import eligibility as elig
from .domain import state_machine as sm
from .domain.metrics import compute_metrics
from .models import (
    CampaignMetrics,
    CampaignOut,
    CampaignStatus,
    Channel,
    DashboardStats,
    DispatchRunOut,
    EligibilityPreview,
)
from .providers import EligibleMember, get_provider
from .repositories import AppRepository, new_id


class CampaignError(Exception):
    def __init__(self, error_code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.error_code = error_code
        self.message = message
        self.details = details or {}


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class CampaignService:
    def __init__(self, db: Db, scheduler=None):
        self.db = db
        self.repo = AppRepository(db)
        self.audiences: AudienceRepository = get_audience_repository(db)
        self._scheduler = scheduler  # injectable for tests; else built lazily

    @property
    def scheduler(self):
        if self._scheduler is None:
            from .scheduler import Scheduler

            self._scheduler = Scheduler(self.db.ws, self.db.config)
        return self._scheduler

    def _cancel_schedule(self, campaign_id: str) -> None:
        """Best-effort removal of any one-time wrapper job (never fatal)."""
        try:
            self.scheduler.cancel(campaign_id)
        except Exception as exc:  # noqa: BLE001
            from .scheduler import logger as _log

            _log.warning(f"schedule cleanup skipped for {campaign_id}: {exc}")

    # ------------------------------------------------------------- eligibility
    def _member_contexts(self, campaign: CampaignOut) -> list[elig.MemberContext]:
        members = self.audiences.get_members(
            campaign.audience_id, campaign.audience_version
        )
        consent = self.repo.get_consent_map([m.customer_id for m in members])
        dispatched = self.repo.dispatched_customer_ids(campaign.campaign_id)
        contexts: list[elig.MemberContext] = []
        for m in members:
            c = consent.get(m.customer_id, {})
            contexts.append(
                elig.MemberContext(
                    customer_id=m.customer_id,
                    account_status=m.account_status,
                    email=m.email,
                    phone=m.phone,
                    app_push_opt_in=bool(c.get("app_push_opt_in", False)),
                    sms_opt_in=bool(c.get("sms_opt_in", False)),
                    email_opt_in=bool(c.get("email_opt_in", False)),
                    do_not_contact=bool(c.get("do_not_contact", False)),
                    already_dispatched=m.customer_id in dispatched,
                )
            )
        return contexts

    def _offer_valid(self, campaign: CampaignOut) -> bool:
        if campaign.channel != Channel.COUPON.value:
            return True
        if not campaign.offer_id:
            return False
        return self.repo.offer_valid_on(campaign.offer_id, campaign.scheduled_at)

    def preview(self, campaign: CampaignOut) -> EligibilityPreview:
        contexts = self._member_contexts(campaign)
        offer_valid = self._offer_valid(campaign)
        buckets = {
            elig.ELIGIBLE: 0,
            elig.SKIPPED_NO_CONSENT: 0,
            elig.SKIPPED_INACTIVE: 0,
            elig.SKIPPED_INVALID_CONTACT: 0,
            elig.ALREADY_DISPATCHED: 0,
        }
        for ctx in contexts:
            result = elig.classify(campaign.channel, ctx, offer_valid=offer_valid)
            buckets[result] = buckets.get(result, 0) + 1
        return EligibilityPreview(
            audience_size=len(contexts),
            eligible=buckets[elig.ELIGIBLE],
            skipped_no_consent=buckets[elig.SKIPPED_NO_CONSENT],
            skipped_inactive=buckets[elig.SKIPPED_INACTIVE],
            skipped_invalid_contact=buckets[elig.SKIPPED_INVALID_CONTACT],
            already_dispatched=buckets[elig.ALREADY_DISPATCHED],
        )

    # ---------------------------------------------------------------- dispatch
    def dispatch(
        self, campaign: CampaignOut, actor: str | None
    ) -> DispatchRunOut:
        # Idempotency: a completed run for this key returns the original result.
        if campaign.idempotency_key:
            existing = self.repo.find_completed_run_by_key(campaign.idempotency_key)
            if existing is not None:
                return existing

        if not sm.can_dispatch(campaign.status):
            raise CampaignError(
                "INVALID_CAMPAIGN_STATE",
                f"Only approved/scheduled campaigns can be dispatched "
                f"(status={campaign.status}).",
                {"status": campaign.status},
            )

        contexts = self._member_contexts(campaign)
        offer_valid = self._offer_valid(campaign)
        member_by_id = {
            m.customer_id: m
            for m in self.audiences.get_members(
                campaign.audience_id, campaign.audience_version
            )
        }

        eligible: list[EligibleMember] = []
        skip_events: list[dict] = []
        base = datetime.now(timezone.utc)
        run_id = self.repo.create_dispatch_run(
            campaign.campaign_id, campaign.idempotency_key, len(contexts)
        )

        for ctx in contexts:
            result = elig.classify(campaign.channel, ctx, offer_valid=offer_valid)
            if result == elig.ELIGIBLE:
                m = member_by_id[ctx.customer_id]
                eligible.append(
                    EligibleMember(
                        customer_id=m.customer_id, email=m.email, phone=m.phone
                    )
                )
            elif result == elig.ALREADY_DISPATCHED:
                continue
            else:
                event_type = (
                    result
                    if result
                    in {
                        elig.SKIPPED_NO_CONSENT,
                        elig.SKIPPED_INACTIVE,
                        elig.SKIPPED_INVALID_CONTACT,
                    }
                    else elig.SKIPPED_NO_CONSENT
                )
                skip_events.append(
                    self._event_row(
                        run_id, campaign, ctx.customer_id, event_type, base, 0
                    )
                )

        # Update campaign -> RUNNING (audited).
        self._transition(campaign, CampaignStatus.RUNNING, actor, note="dispatch")

        try:
            provider = get_provider(campaign.channel)
            provider.validate(campaign.model_dump())
            result = provider.send(campaign.model_dump(), eligible)

            events: list[dict] = list(skip_events)
            for member in eligible:
                # REQUESTED marks the attempted send.
                events.append(
                    self._event_row(
                        run_id, campaign, member.customer_id, "REQUESTED", base, 0
                    )
                )
            for outcome in result.outcomes:
                for ev in outcome.events:
                    events.append(
                        self._event_row(
                            run_id,
                            campaign,
                            outcome.customer_id,
                            ev.event_type,
                            base,
                            ev.ts_offset_seconds,
                            provider_message_id=ev.provider_message_id,
                            failure_reason=ev.failure_reason,
                        )
                    )

            self.repo.insert_delivery_events(events)
            self.repo.finish_dispatch_run(
                run_id,
                "COMPLETED",
                eligible=len(eligible),
                success=result.success_count,
                failure=result.failure_count,
                skipped=len(skip_events),
            )
            self._transition(campaign, CampaignStatus.COMPLETED, actor, note="dispatch complete")
            self.repo.audit(
                actor,
                "DISPATCH",
                "campaign",
                campaign.campaign_id,
                {
                    "run_id": run_id,
                    "eligible": len(eligible),
                    "success": result.success_count,
                    "failure": result.failure_count,
                    "skipped": len(skip_events),
                },
            )
            # Remove any spent one-time wrapper job (reconcile is the backstop).
            self._cancel_schedule(campaign.campaign_id)
        except Exception as exc:  # noqa: BLE001 - persist failure then re-raise
            self.repo.finish_dispatch_run(
                run_id,
                "FAILED",
                eligible=len(eligible),
                success=0,
                failure=0,
                skipped=len(skip_events),
                error_message=str(exc)[:900],
            )
            self.repo.set_status(campaign.campaign_id, CampaignStatus.FAILED.value)
            self.repo.audit(
                actor, "DISPATCH_FAILED", "campaign", campaign.campaign_id,
                {"run_id": run_id, "error": str(exc)[:400]},
            )
            raise

        run = self._get_run(run_id)
        assert run is not None
        return run

    def _get_run(self, run_id: str) -> DispatchRunOut | None:
        rows = self.repo.db.execute(
            f"SELECT {self.repo._RUN_COLS} FROM {self.repo.c.table('app_dispatch_run')} "
            f"WHERE dispatch_run_id = :id LIMIT 1",
            {"id": run_id},
        )
        return DispatchRunOut(**rows[0]) if rows else None

    def _event_row(
        self,
        run_id: str,
        campaign: CampaignOut,
        customer_id: str,
        event_type: str,
        base: datetime,
        offset: int,
        provider_message_id: str | None = None,
        failure_reason: str | None = None,
    ) -> dict:
        ts = _iso(base + timedelta(seconds=offset))
        return {
            "delivery_event_id": new_id("EVT"),
            "dispatch_run_id": run_id,
            "campaign_id": campaign.campaign_id,
            "customer_id": customer_id,
            "channel": campaign.channel,
            "event_type": event_type,
            "event_ts": ts,
            "provider_message_id": provider_message_id,
            "failure_reason": failure_reason,
            "created_at": _iso(base),
        }

    # ------------------------------------------------------------ transitions
    def _transition(
        self,
        campaign: CampaignOut,
        target: CampaignStatus,
        actor: str | None,
        *,
        approved_by: str | None = None,
        note: str | None = None,
    ) -> None:
        sm.assert_transition(campaign.status, target)
        self.repo.set_status(campaign.campaign_id, target.value, approved_by=approved_by)
        campaign.status = target.value
        self.repo.audit(
            actor,
            f"STATUS_{target.value}",
            "campaign",
            campaign.campaign_id,
            {"note": note} if note else {},
        )

    def metrics(self, campaign_id: str) -> CampaignMetrics:
        counts = self.repo.event_counts(campaign_id)
        return compute_metrics(campaign_id, counts)

    # ------------------------------------------------------------ lifecycle
    def create(self, data, actor: str | None) -> CampaignOut:
        from .models import CampaignIn

        assert isinstance(data, CampaignIn)
        # Resolve audience + version (fail clearly if the audience is unknown).
        detail = self.audiences.get_audience(data.audience_id, data.audience_version)
        campaign_id = new_id("CMP")
        now = _iso(datetime.now(timezone.utc))
        idem = new_id("IDEM")
        values = {
            "campaign_id": campaign_id,
            "audience_id": data.audience_id,
            "audience_version": data.audience_version or detail.audience_version,
            "campaign_name": data.campaign_name,
            "channel": data.channel.value,
            "offer_id": data.offer_id,
            "message_title": data.message_title,
            "message_body": data.message_body,
            "deep_link": data.deep_link,
            "scheduled_at": data.scheduled_at,
            "status": CampaignStatus.DRAFT.value,
            "created_by": actor,
            "approved_by": None,
            "created_at": now,
            "updated_at": now,
            "idempotency_key": idem,
        }
        self.repo.insert_campaign(values)
        self.repo.audit(actor, "CREATE", "campaign", campaign_id, {"name": data.campaign_name})
        created = self.repo.get_campaign(campaign_id)
        assert created is not None
        return created

    def update(self, campaign: CampaignOut, patch, actor: str | None) -> CampaignOut:
        if campaign.status != CampaignStatus.DRAFT.value:
            raise CampaignError(
                "INVALID_CAMPAIGN_STATE",
                "Only DRAFT campaigns can be edited.",
                {"status": campaign.status},
            )
        fields = {k: v for k, v in patch.model_dump(exclude_unset=True).items() if v is not None}
        if "channel" in fields and hasattr(fields["channel"], "value"):
            fields["channel"] = fields["channel"].value
        self.repo.update_campaign_fields(campaign.campaign_id, fields)
        # A new campaign version gets a fresh idempotency key.
        self.repo.rotate_idempotency_key(campaign.campaign_id)
        self.repo.audit(actor, "EDIT", "campaign", campaign.campaign_id, fields)
        updated = self.repo.get_campaign(campaign.campaign_id)
        assert updated is not None
        return updated

    def submit(self, campaign: CampaignOut, actor: str | None) -> CampaignOut:
        self._transition(campaign, CampaignStatus.PENDING_APPROVAL, actor, note="submit")
        self.repo.add_approval(campaign.campaign_id, "SUBMITTED", actor, None)
        return self._reload(campaign.campaign_id)

    def approve(self, campaign: CampaignOut, actor: str | None, comment: str | None) -> CampaignOut:
        self._transition(
            campaign, CampaignStatus.APPROVED, actor, approved_by=actor, note="approve"
        )
        self.repo.add_approval(campaign.campaign_id, "APPROVED", actor, comment)
        return self._reload(campaign.campaign_id)

    def reject(self, campaign: CampaignOut, actor: str | None, comment: str | None) -> CampaignOut:
        # Rejection returns the campaign to DRAFT.
        self._transition(campaign, CampaignStatus.DRAFT, actor, note="reject")
        self.repo.add_approval(campaign.campaign_id, "REJECTED", actor, comment)
        return self._reload(campaign.campaign_id)

    def cancel(self, campaign: CampaignOut, actor: str | None, comment: str | None) -> CampaignOut:
        was_scheduled = campaign.status == CampaignStatus.SCHEDULED.value
        self._transition(campaign, CampaignStatus.CANCELLED, actor, note="cancel")
        self.repo.add_approval(campaign.campaign_id, "CANCELLED", actor, comment)
        if was_scheduled:
            self._cancel_schedule(campaign.campaign_id)
        return self._reload(campaign.campaign_id)

    def schedule(
        self, campaign: CampaignOut, scheduled_at: str, actor: str | None
    ) -> CampaignOut:
        """APPROVED -> SCHEDULED, and arm a one-time job to dispatch at scheduled_at."""
        from .scheduler import SchedulerError

        if not scheduled_at:
            raise CampaignError("VALIDATION_ERROR", "scheduled_at is required.")
        # Set the scheduled time first so the wrapper + record agree.
        self.repo.update_campaign_fields(campaign.campaign_id, {"scheduled_at": scheduled_at})
        campaign.scheduled_at = scheduled_at
        try:
            job_id = self.scheduler.schedule(campaign.campaign_id, scheduled_at)
        except SchedulerError as exc:
            raise CampaignError("SCHEDULER_UNAVAILABLE", str(exc))
        self._transition(campaign, CampaignStatus.SCHEDULED, actor, note="schedule")
        self.repo.audit(
            actor, "SCHEDULE", "campaign", campaign.campaign_id,
            {"scheduled_at": scheduled_at, "job_id": job_id},
        )
        return self._reload(campaign.campaign_id)

    def _reload(self, campaign_id: str) -> CampaignOut:
        c = self.repo.get_campaign(campaign_id)
        assert c is not None
        return c


class DashboardService:
    def __init__(self, db: Db):
        self.repo = AppRepository(db)
        self.audiences = get_audience_repository(db)

    def stats(self) -> DashboardStats:
        status_counts = self.repo.campaign_status_counts()
        events = self.repo.global_event_counts()
        delivered = events.get("DELIVERED", 0)
        opened = events.get("OPENED", 0)
        clicked = events.get("CLICKED", 0)
        redeemed = events.get("REDEEMED", 0)

        def rate(n: int, d: int) -> float:
            return round(n / d, 4) if d else 0.0

        total_campaigns = sum(status_counts.values())
        return DashboardStats(
            total_audiences=len(self.audiences.list_audiences()),
            total_campaigns=total_campaigns,
            draft_campaigns=status_counts.get("DRAFT", 0),
            pending_approvals=status_counts.get("PENDING_APPROVAL", 0),
            scheduled_campaigns=status_counts.get("SCHEDULED", 0),
            completed_dispatches=self.repo.completed_dispatch_count(),
            total_delivered=delivered,
            open_rate=rate(opened, delivered),
            click_rate=rate(clicked, delivered),
            redemption_rate=rate(redeemed, delivered),
            recent_activity=self.repo.recent_audit(12),
        )
