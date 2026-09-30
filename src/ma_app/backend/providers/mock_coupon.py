"""Mock Coupon provider — never calls a real coupon/CMS system."""

from __future__ import annotations

from ._base import BaseMockProvider


class MockCouponProvider(BaseMockProvider):
    channel = "COUPON"
    code = "CPN"
    p_send_success = 0.97
    p_delivered = 0.95
    p_opened = 0.0
    p_clicked = 0.0
    p_redeemed = 0.21  # delivered -> redeemed
