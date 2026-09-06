"""Property coverage for resilient local timezone resolution (GH-160)."""

from __future__ import annotations

import os
from unittest.mock import patch
from zoneinfo import ZoneInfo

from hypothesis import given, strategies as st

from rebalance.lib.time_ops import local_tz


@given(st.text().filter(lambda value: "\0" not in value))
def test_local_tz_never_raises_for_arbitrary_environment_value(value: str) -> None:
    """An operator override is untrusted input, including malformed paths."""
    with patch.dict(os.environ, {"REBALANCE_TZ": value}, clear=False):
        assert isinstance(local_tz(), ZoneInfo)


def test_local_tz_falls_back_to_utc_for_absolute_or_traversal_paths() -> None:
    for value in ("/UTC", "../.."):
        with patch.dict(os.environ, {"REBALANCE_TZ": value}, clear=False):
            assert local_tz().key == "UTC"


def test_local_tz_preserves_a_valid_explicit_override() -> None:
    with patch.dict(os.environ, {"REBALANCE_TZ": "UTC"}, clear=False):
        assert local_tz().key == "UTC"
