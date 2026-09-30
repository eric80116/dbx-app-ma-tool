"""Mock App Push provider — never calls FCM/APNs."""

from __future__ import annotations

from ._base import BaseMockProvider


class MockPushProvider(BaseMockProvider):
    channel = "APP_PUSH"
    code = "PUSH"
    p_send_success = 0.96
    p_delivered = 0.93
    p_opened = 0.42
    p_clicked = 0.28
