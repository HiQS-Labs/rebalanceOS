"""Regression coverage for the notices / warnings / errors panel buckets (GH-153).

The "collector attention needed" panel used to render every non-OK check as a
flat count. These pin the three-bucket taxonomy: severity drives the verdict,
notices are muted and never escalate, and the header text counts each bucket.
"""

from datetime import datetime, timezone

from rebalance.doctor import FAIL, NOTICE, OK, WARN, Check
from rebalance.health import _bucket_label, compute_health_status

NOW = datetime(2026, 7, 18, 18, 0, tzinfo=timezone.utc)
STATUS: dict = {"sources": {}}


def _h(checks):
    return compute_health_status(checks, STATUS, NOW)


def test_severity_drives_the_three_buckets() -> None:
    h = _h(
        [
            Check("database", FAIL, "missing"),  # → severity ERROR (auto-upgrade)
            Check("sleuth", WARN, "no env file"),  # → WARNING
            Check("launchd:pulse-server", OK, "running", severity=NOTICE),
        ]
    )
    assert [c.name for c in h.errors] == ["database"]
    assert [c.name for c in h.warnings] == ["sleuth"]
    assert [c.name for c in h.notices] == ["launchd:pulse-server"]


def test_error_drives_fail_verdict() -> None:
    assert _h([Check("database", FAIL, "missing")]).verdict == FAIL


def test_only_warnings_is_warn_verdict() -> None:
    assert _h([Check("sleuth", WARN, "x")]).verdict == WARN


def test_notices_do_not_escalate_the_verdict() -> None:
    """An OK system with only notices stays OK — notices are muted."""
    h = _h([Check("scheduler:obsidian-rollover", WARN, "not loaded", severity=NOTICE)])
    assert h.verdict == OK
    assert [c.name for c in h.notices] == ["scheduler:obsidian-rollover"]
    assert h.warnings == []


def test_bucket_text_summarizes_every_nonempty_bucket() -> None:
    """The COMPLETE summary — notices included. This is what the copy button
    pastes into an issue, where leaving a bucket out would be misleading."""
    h = _h(
        [
            Check("database", FAIL, "missing"),
            Check("sleuth", WARN, "x"),
            Check("launchd:pulse-server", OK, "running", severity=NOTICE),
        ]
    )
    assert h.bucket_text == "1 error · 1 warning · 1 notice"


def test_the_headline_counts_only_what_is_actionable() -> None:
    """The counterpart (GH-100). `status_text` used to serve both roles by
    switching on whether notices existed; one property cannot, so it was split
    into `problem_text` (headline) and `bucket_text` (complete) and removed."""
    h = _h([Check("a", WARN, "x"), Check("b", WARN, "y")])
    assert h.problem_text == "2 warnings"


def test_the_headline_excludes_notices_but_the_summary_keeps_them() -> None:
    h = _h(
        [
            Check("database", FAIL, "missing"),
            Check("launchd:pulse-server", OK, "running", severity=NOTICE),
        ]
    )
    assert h.problem_text == "1 error"
    assert h.bucket_text == "1 error · 1 notice"


def test_problem_text_is_healthy_when_nothing_is_actionable() -> None:
    """Notices alone must not make the headline look like a problem."""
    h = _h([Check("launchd:pulse-server", OK, "running", severity=NOTICE)])
    assert h.problem_text == "healthy"


def test_bucket_label_pluralizes() -> None:
    assert _bucket_label(1, "error") == "1 error"
    assert _bucket_label(3, "notice") == "3 notices"
