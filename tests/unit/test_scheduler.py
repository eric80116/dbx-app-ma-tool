from datetime import datetime

import pytest

from ma_app.backend.scheduler import to_quartz_oneshot, wrapper_name

pytestmark = pytest.mark.unit


def test_quartz_oneshot_from_iso_string():
    # "sec min hour day month ? year"
    assert to_quartz_oneshot("2026-10-15 14:30:00") == "0 30 14 15 10 ? 2026"


def test_quartz_oneshot_from_datetime():
    assert to_quartz_oneshot(datetime(2027, 1, 5, 9, 5, 0)) == "0 5 9 5 1 ? 2027"


def test_quartz_oneshot_strips_z_and_t():
    assert to_quartz_oneshot("2026-12-31T23:59:00Z") == "0 59 23 31 12 ? 2026"


def test_quartz_oneshot_year_boundary():
    assert to_quartz_oneshot("2026-01-01 00:00:00") == "0 0 0 1 1 ? 2026"


def test_wrapper_name():
    assert wrapper_name("CMP-abc") == "ma-app-dispatch-CMP-abc"
