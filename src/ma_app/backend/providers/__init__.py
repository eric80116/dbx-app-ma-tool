"""Mock activation providers."""

from __future__ import annotations

from .interface import (
    ActivationProvider,
    DispatchResult,
    EligibleMember,
    MemberEvent,
    MemberOutcome,
    ValidationResult,
)
from .mock_coupon import MockCouponProvider
from .mock_push import MockPushProvider
from .mock_sms import MockSmsProvider

__all__ = [
    "ActivationProvider",
    "DispatchResult",
    "EligibleMember",
    "MemberEvent",
    "MemberOutcome",
    "ValidationResult",
    "MockPushProvider",
    "MockSmsProvider",
    "MockCouponProvider",
    "get_provider",
]

_PROVIDERS: dict[str, type] = {
    "APP_PUSH": MockPushProvider,
    "SMS": MockSmsProvider,
    "COUPON": MockCouponProvider,
}


def get_provider(channel: str) -> ActivationProvider:
    cls = _PROVIDERS.get(channel)
    if cls is None:
        raise ValueError(f"No provider registered for channel '{channel}'")
    return cls()
