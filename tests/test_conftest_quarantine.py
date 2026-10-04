"""GH-312: the GH-178 quarantine carries a UTC expiry with return-to-gate behavior.

P13: a quarantine without an expiry is a quarantine forever. These tests pin the
conftest helper — marker withheld at/after expiry, present before, and the reason
line carrying all three P13 elements. The full-suite integration evidence is the
XFAIL lines themselves (they still appear while the quarantine is active).
"""

from datetime import datetime, timedelta

import conftest


def _expiry() -> datetime:
    return datetime.fromisoformat(conftest.GH178_QUARANTINE_EXPIRES_UTC.replace("Z", "+00:00"))


def test_quarantine_active_before_expiry():
    assert conftest.gh178_quarantine_expired(_expiry() - timedelta(seconds=1)) is False


def test_quarantine_boundary_exact_is_expired():
    # now == expiry means expired: a marker that survives its own expiry instant
    # is how quarantines silently become permanent.
    assert conftest.gh178_quarantine_expired(_expiry()) is True


def test_quarantine_expired_after_expiry():
    assert conftest.gh178_quarantine_expired(_expiry() + timedelta(days=1)) is True


def test_quarantine_reason_carries_p13_elements():
    reason = conftest.gh178_quarantine_reason()
    assert "owner: noel" in reason
    assert "issue: #178" in reason
    assert conftest.GH178_QUARANTINE_EXPIRES_UTC in reason
