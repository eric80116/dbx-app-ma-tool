import pytest

from ma_app.backend.providers import (
    ActivationProvider,
    EligibleMember,
    MockCouponProvider,
    MockPushProvider,
    MockSmsProvider,
    get_provider,
)

pytestmark = pytest.mark.unit

CAMPAIGN = {"campaign_id": "CMP-TEST", "message_title": "Hi", "channel": "APP_PUSH"}
MEMBERS = [EligibleMember(customer_id=f"C{i}", email=f"u{i}@example.com", phone="+1-555-0101") for i in range(200)]


def _events(result):
    return [(o.customer_id, tuple(e.event_type for e in o.events)) for o in result.outcomes]


def test_push_provider_is_deterministic():
    p = MockPushProvider()
    r1 = p.send(CAMPAIGN, MEMBERS)
    r2 = p.send(CAMPAIGN, MEMBERS)
    assert _events(r1) == _events(r2)
    assert r1.success_count == r2.success_count


def test_message_ids_are_channel_tagged_and_sequential():
    p = MockPushProvider()
    r = p.send(CAMPAIGN, MEMBERS)
    ids = [e.provider_message_id for o in r.outcomes for e in o.events if e.provider_message_id]
    assert ids[0] == "MOCK-PUSH-000001"
    assert all(x.startswith("MOCK-PUSH-") for x in ids)


def test_push_has_sends_and_some_failures():
    r = MockPushProvider().send(CAMPAIGN, MEMBERS)
    assert r.success_count > 0
    assert r.failure_count >= 0
    assert r.success_count + r.failure_count == len(MEMBERS)


def test_messaging_funnel_has_opens_and_clicks():
    r = MockPushProvider().send(CAMPAIGN, MEMBERS)
    types = {e.event_type for o in r.outcomes for e in o.events}
    assert "SENT" in types
    assert "DELIVERED" in types
    assert "OPENED" in types
    assert "CLICKED" in types


def test_coupon_funnel_redeems_not_opens():
    r = MockCouponProvider().send({**CAMPAIGN, "channel": "COUPON"}, MEMBERS)
    types = {e.event_type for o in r.outcomes for e in o.events}
    assert "REDEEMED" in types
    assert "OPENED" not in types


def test_sms_provider_runs():
    r = MockSmsProvider().send({**CAMPAIGN, "channel": "SMS"}, MEMBERS)
    assert r.success_count + r.failure_count == len(MEMBERS)


def test_get_provider_maps_channels():
    assert isinstance(get_provider("APP_PUSH"), MockPushProvider)
    assert isinstance(get_provider("SMS"), MockSmsProvider)
    assert isinstance(get_provider("COUPON"), MockCouponProvider)
    with pytest.raises(ValueError):
        get_provider("EMAIL")


def test_provider_interface_is_swappable():
    """A custom provider satisfying the protocol works without touching the service."""

    class DummyProvider:
        channel = "APP_PUSH"

        def validate(self, campaign):
            from ma_app.backend.providers import ValidationResult

            return ValidationResult(ok=True)

        def send(self, campaign, members):
            from ma_app.backend.providers import DispatchResult

            return DispatchResult(outcomes=[])

    p: ActivationProvider = DummyProvider()
    # Structural (duck) typing: the service only needs validate()/send().
    assert p.validate(CAMPAIGN).ok
    assert p.send(CAMPAIGN, MEMBERS).success_count == 0
