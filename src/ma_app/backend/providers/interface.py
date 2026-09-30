"""Activation provider boundary (mock only for the demo).

Providers NEVER call an external API. They produce deterministic per-member delivery
outcomes (using a fixed seed) that the dispatch service persists to
`app_delivery_event`. A real FCM/SMS/coupon provider can implement the same interface
without changing the campaign/dispatch service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

# Fixed seed for deterministic mock behaviour (per prompt).
SEED = 42


@dataclass
class EligibleMember:
    customer_id: str
    email: str | None = None
    phone: str | None = None


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)


@dataclass
class MemberEvent:
    event_type: str
    provider_message_id: str | None = None
    failure_reason: str | None = None
    ts_offset_seconds: int = 0


@dataclass
class MemberOutcome:
    customer_id: str
    events: list[MemberEvent] = field(default_factory=list)

    @property
    def succeeded(self) -> bool:
        return any(e.event_type == "SENT" for e in self.events)


@dataclass
class DispatchResult:
    outcomes: list[MemberOutcome] = field(default_factory=list)

    @property
    def success_count(self) -> int:
        return sum(1 for o in self.outcomes if o.succeeded)

    @property
    def failure_count(self) -> int:
        return sum(1 for o in self.outcomes if not o.succeeded)


class ActivationProvider(Protocol):
    channel: str

    def validate(self, campaign: dict) -> ValidationResult: ...

    def send(
        self, campaign: dict, members: list[EligibleMember]
    ) -> DispatchResult: ...
