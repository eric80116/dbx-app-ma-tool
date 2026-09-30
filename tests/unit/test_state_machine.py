import pytest

from ma_app.backend.domain import state_machine as sm
from ma_app.backend.domain.state_machine import InvalidTransition
from ma_app.backend.models import CampaignStatus as S

pytestmark = pytest.mark.unit


def test_every_allowed_transition_is_permitted():
    for current, targets in sm.ALLOWED.items():
        for target in targets:
            assert sm.can_transition(current, target)
            sm.assert_transition(current, target)  # must not raise


def test_invalid_transitions_raise():
    assert not sm.can_transition(S.DRAFT, S.APPROVED)
    with pytest.raises(InvalidTransition):
        sm.assert_transition(S.DRAFT, S.APPROVED)
    with pytest.raises(InvalidTransition):
        sm.assert_transition(S.COMPLETED, S.RUNNING)


def test_can_dispatch_only_for_approved_or_scheduled():
    assert sm.can_dispatch(S.APPROVED)
    assert sm.can_dispatch(S.SCHEDULED)
    for bad in (S.DRAFT, S.PENDING_APPROVAL, S.RUNNING, S.COMPLETED, S.FAILED, S.CANCELLED):
        assert not sm.can_dispatch(bad)


def test_rejection_path_returns_to_draft():
    assert sm.can_transition(S.PENDING_APPROVAL, S.DRAFT)


def test_terminal_states_have_no_transitions():
    for terminal in (S.COMPLETED, S.FAILED, S.CANCELLED):
        assert sm.ALLOWED[terminal] == set()
