"""Campaign state machine.

Only these transitions are allowed. Every accepted transition must be recorded by the
caller in `app_campaign_approval` and/or `app_audit_log`.
"""

from __future__ import annotations

from ..models import CampaignStatus as S

ALLOWED: dict[S, set[S]] = {
    # A rejection sends a PENDING_APPROVAL campaign back to DRAFT (REJECTED is an
    # approval *action*, not a campaign status).
    S.DRAFT: {S.PENDING_APPROVAL, S.CANCELLED},
    S.PENDING_APPROVAL: {S.APPROVED, S.DRAFT, S.CANCELLED},
    S.APPROVED: {S.SCHEDULED, S.RUNNING, S.CANCELLED},
    S.SCHEDULED: {S.RUNNING, S.CANCELLED},
    S.RUNNING: {S.COMPLETED, S.FAILED},
    S.COMPLETED: set(),
    S.FAILED: set(),
    S.CANCELLED: set(),
}


class InvalidTransition(Exception):
    def __init__(self, current: str, target: str):
        super().__init__(f"Illegal campaign transition {current} -> {target}")
        self.current = current
        self.target = target


def can_transition(current: S | str, target: S | str) -> bool:
    cur = S(current)
    tgt = S(target)
    return tgt in ALLOWED.get(cur, set())


def assert_transition(current: S | str, target: S | str) -> None:
    if not can_transition(current, target):
        raise InvalidTransition(str(S(current).value), str(S(target).value))


def can_dispatch(current: S | str) -> bool:
    """Only APPROVED or SCHEDULED campaigns may be dispatched."""
    return S(current) in {S.APPROVED, S.SCHEDULED}
