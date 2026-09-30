"""Shared deterministic funnel logic for mock providers."""

from __future__ import annotations

import random

from .interface import (
    DispatchResult,
    EligibleMember,
    MemberEvent,
    MemberOutcome,
    SEED,
)


class BaseMockProvider:
    """Deterministic mock funnel.

    Given the same campaign + members, always produces the same outcomes because the
    RNG is seeded from the campaign id and the member index. Message ids are
    sequential and channel-tagged, e.g. ``MOCK-PUSH-000001``.
    """

    channel: str = "MOCK"
    code: str = "MOCK"

    # Funnel probabilities (per stage, conditional on the previous stage).
    p_send_success = 0.95
    p_delivered = 0.92
    p_opened = 0.45
    p_clicked = 0.30
    p_redeemed = 0.0  # only coupons redeem

    def validate(self, campaign: dict):
        from .interface import ValidationResult

        errors: list[str] = []
        if not campaign.get("message_title") and self.channel != "COUPON":
            errors.append("message_title is required")
        return ValidationResult(ok=not errors, errors=errors)

    def send(
        self, campaign: dict, members: list[EligibleMember]
    ) -> DispatchResult:
        campaign_id = str(campaign.get("campaign_id", "unknown"))
        seed = SEED ^ (hash(campaign_id) & 0xFFFFFFFF)
        rng = random.Random(seed)
        outcomes: list[MemberOutcome] = []

        for idx, member in enumerate(members, start=1):
            msg_id = f"MOCK-{self.code}-{idx:06d}"
            events: list[MemberEvent] = []
            if rng.random() > self.p_send_success:
                events.append(
                    MemberEvent(
                        event_type="FAILED",
                        provider_message_id=msg_id,
                        failure_reason="mock_provider_transient_error",
                        ts_offset_seconds=0,
                    )
                )
                outcomes.append(MemberOutcome(customer_id=member.customer_id, events=events))
                continue

            events.append(
                MemberEvent(event_type="SENT", provider_message_id=msg_id, ts_offset_seconds=0)
            )
            if rng.random() <= self.p_delivered:
                events.append(
                    MemberEvent(event_type="DELIVERED", provider_message_id=msg_id, ts_offset_seconds=30)
                )
                if self.p_redeemed > 0:
                    # Coupon funnel: delivered -> redeemed
                    if rng.random() <= self.p_redeemed:
                        events.append(
                            MemberEvent(event_type="REDEEMED", provider_message_id=msg_id, ts_offset_seconds=3600)
                        )
                else:
                    # Messaging funnel: delivered -> opened -> clicked
                    if rng.random() <= self.p_opened:
                        events.append(
                            MemberEvent(event_type="OPENED", provider_message_id=msg_id, ts_offset_seconds=120)
                        )
                        if rng.random() <= self.p_clicked:
                            events.append(
                                MemberEvent(event_type="CLICKED", provider_message_id=msg_id, ts_offset_seconds=180)
                            )
            outcomes.append(MemberOutcome(customer_id=member.customer_id, events=events))

        return DispatchResult(outcomes=outcomes)
