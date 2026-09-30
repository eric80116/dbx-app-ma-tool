"""Mock SMS provider — never calls a real SMS gateway."""

from __future__ import annotations

from ._base import BaseMockProvider


class MockSmsProvider(BaseMockProvider):
    channel = "SMS"
    code = "SMS"
    p_send_success = 0.94
    p_delivered = 0.90
    p_opened = 0.55  # SMS "opened" ~ read
    p_clicked = 0.22
