"""Per-customer eligibility & compliance rules (pure functions).

These are enforced server-side before any dispatch. The SQL that counts eligibility
for previews lives in the campaign service, but the *decision* for a single member is
here so it is unit-testable and shared by preview and dispatch.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..models import Channel

# Skip reason tokens (map to DeliveryEventType values where applicable).
ELIGIBLE = "ELIGIBLE"
SKIPPED_NO_CONSENT = "SKIPPED_NO_CONSENT"
SKIPPED_INACTIVE = "SKIPPED_INACTIVE"
SKIPPED_INVALID_CONTACT = "SKIPPED_INVALID_CONTACT"
ALREADY_DISPATCHED = "ALREADY_DISPATCHED"

_PHONE_RE = re.compile(r"\d")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class MemberContext:
    """Everything needed to decide one member's eligibility for one channel."""

    customer_id: str
    account_status: str | None
    email: str | None
    phone: str | None
    app_push_opt_in: bool
    sms_opt_in: bool
    email_opt_in: bool
    do_not_contact: bool
    already_dispatched: bool = False


def _has_dialable_phone(phone: str | None) -> bool:
    # Demo phones are intentionally non-dialable; we only require *some* digits and
    # a plausible length so the "invalid contact" skip is demonstrable.
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return len(digits) >= 7


def _has_valid_email(email: str | None) -> bool:
    return bool(email and _EMAIL_RE.match(email))


def classify(channel: Channel | str, ctx: MemberContext, *, offer_valid: bool = True) -> str:
    """Return ELIGIBLE or a skip-reason token for one member on one channel."""
    ch = Channel(channel)

    if ctx.already_dispatched:
        return ALREADY_DISPATCHED

    # Global guardrails.
    if ctx.do_not_contact:
        return SKIPPED_NO_CONSENT
    if (ctx.account_status or "").lower() != "active":
        return SKIPPED_INACTIVE

    if ch == Channel.APP_PUSH:
        if not ctx.app_push_opt_in:
            return SKIPPED_NO_CONSENT
        return ELIGIBLE

    if ch == Channel.SMS:
        if not ctx.sms_opt_in:
            return SKIPPED_NO_CONSENT
        if not _has_dialable_phone(ctx.phone):
            return SKIPPED_INVALID_CONTACT
        return ELIGIBLE

    if ch == Channel.COUPON:
        # Coupon requires an active, contactable customer and a valid offer.
        if not offer_valid:
            return SKIPPED_NO_CONSENT
        return ELIGIBLE

    return SKIPPED_NO_CONSENT
