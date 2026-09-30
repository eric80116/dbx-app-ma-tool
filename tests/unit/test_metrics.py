import pytest

from ma_app.backend.domain.metrics import compute_metrics

pytestmark = pytest.mark.unit


def test_rates_computed_from_counts():
    counts = {
        "REQUESTED": 100,
        "SENT": 90,
        "FAILED": 10,
        "DELIVERED": 80,
        "OPENED": 40,
        "CLICKED": 20,
        "REDEEMED": 8,
        "SKIPPED_NO_CONSENT": 5,
        "SKIPPED_INACTIVE": 5,
    }
    m = compute_metrics("CMP-1", counts)
    assert m.eligible == 100  # sent + failed
    assert m.skipped == 10
    assert m.failure_rate == 0.1  # 10 / 100
    assert m.open_rate == 0.5  # 40 / 80
    assert m.click_through_rate == 0.25  # 20 / 80
    assert m.redemption_rate == 0.1  # 8 / 80


def test_zero_denominator_is_zero():
    m = compute_metrics("CMP-2", {})
    assert m.open_rate == 0.0
    assert m.click_through_rate == 0.0
    assert m.redemption_rate == 0.0
    assert m.failure_rate == 0.0
