import dataclasses

import pytest

from ma_app.backend.domain import eligibility as elig
from ma_app.backend.domain.eligibility import MemberContext
from ma_app.backend.models import Channel

pytestmark = pytest.mark.unit

_BASE = MemberContext(
    customer_id="C1",
    account_status="Active",
    email="u@example.com",
    phone="+1-555-0101",
    app_push_opt_in=True,
    sms_opt_in=True,
    email_opt_in=True,
    do_not_contact=False,
    already_dispatched=False,
)


def ctx(**kw):
    return dataclasses.replace(_BASE, **kw)


def test_active_opted_in_is_eligible_push():
    assert elig.classify(Channel.APP_PUSH, ctx()) == elig.ELIGIBLE


def test_inactive_account_skipped():
    assert elig.classify(Channel.APP_PUSH, ctx(account_status="Inactive")) == elig.SKIPPED_INACTIVE
    assert elig.classify(Channel.APP_PUSH, ctx(account_status="Suspended")) == elig.SKIPPED_INACTIVE


def test_do_not_contact_skipped():
    assert elig.classify(Channel.APP_PUSH, ctx(do_not_contact=True)) == elig.SKIPPED_NO_CONSENT


def test_push_opt_out_skipped_for_push():
    assert elig.classify(Channel.APP_PUSH, ctx(app_push_opt_in=False)) == elig.SKIPPED_NO_CONSENT


def test_sms_opt_out_skipped_for_sms():
    assert elig.classify(Channel.SMS, ctx(sms_opt_in=False)) == elig.SKIPPED_NO_CONSENT


def test_sms_invalid_phone_skipped():
    assert elig.classify(Channel.SMS, ctx(phone=None)) == elig.SKIPPED_INVALID_CONTACT
    assert elig.classify(Channel.SMS, ctx(phone="123")) == elig.SKIPPED_INVALID_CONTACT


def test_sms_valid_is_eligible():
    assert elig.classify(Channel.SMS, ctx()) == elig.ELIGIBLE


def test_coupon_requires_valid_offer():
    assert elig.classify(Channel.COUPON, ctx(), offer_valid=True) == elig.ELIGIBLE
    assert elig.classify(Channel.COUPON, ctx(), offer_valid=False) == elig.SKIPPED_NO_CONSENT


def test_already_dispatched_short_circuits():
    assert elig.classify(Channel.APP_PUSH, ctx(already_dispatched=True)) == elig.ALREADY_DISPATCHED
    # even an ineligible member reports ALREADY_DISPATCHED first
    assert (
        elig.classify(Channel.APP_PUSH, ctx(already_dispatched=True, account_status="Inactive"))
        == elig.ALREADY_DISPATCHED
    )
