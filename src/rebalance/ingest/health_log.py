"""Health-check state CHANGES, recorded into the unified system log (GH-101).

Why this exists
---------------
The System Log page reads one file, and until now only two families wrote to it:
auth flows and launchd job events. That is why its "All" filter showed only Auth
and Jobs — not a filter bug, an input gap. The page had been renamed from
Authorization Log to System Log without its pipeline being widened to match.

Health checks were the conspicuous absence. The errors and warnings on the
dashboard header came from ``HealthStatus``, an in-memory structure that touched
no log, so the errors you saw on the header and the errors you saw on the System
Log page were unrelated sets from unrelated pipelines, and neither page could
show you the other's problems.

Transitions, not samples
------------------------
This records a check ONLY when its state changes. That is a durability
constraint, not a stylistic one:

``auth_log`` is an append-only JSONL file with **no rotation**, and ``_read_file``
parses the WHOLE file on every read before the caller slices off the last N rows.
Cost therefore grows with total history, not with what is displayed. Writing every
check on every run — roughly 20 checks, hourly — would add ~175k lines a year and
make each dashboard load parse all of them. Writing only transitions keeps volume
proportional to how often things actually break, which is the same order as the
auth events already in the file, and keeps the format usable for years.

It is also the more useful record. "What changed, and when" is a log a person can
read. "What was sampled, 20 rows at a time, forever" is not.

The same shape already exists in this repo: ``scripts/pulse_warning_watch.py``
fingerprints the page and writes only when the fingerprint moves.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping

# Imported as a MODULE, not as `from … import _log_dir`. A direct name import
# binds the function at import time and silently defeats the
# REBALANCE_AUTH_LOG_DIR seam: `log_event` would honour a redirected directory
# while the state sidecar kept writing to the real one. Under test that leaks
# state between cases (and pollutes the developer's actual log); in production it
# would split the two halves of this module across two directories.
from rebalance.ingest import auth_log

SOURCE = "health"

# Emitted event names, keyed by the state a check moved INTO. These are the
# strings the System Log renders a badge for, so adding a state here means
# adding a badge in web.py._EVENT_BADGE.
#
# The keys are doctor's OWN status vocabulary — `error` / `warning` / `ok`, NOT
# `fail` / `warn`. The constants are named FAIL and WARN but their VALUES are
# "error" and "warning", which is an easy and expensive thing to get wrong: keyed
# on the constant names, this module silently logged recoveries and nothing else.
# `test_state_vocabulary_matches_doctor` asserts these against the real constants
# so the guess cannot come back.
_EVENT_FOR_STATE = {
    "error": "check_failed",
    "warning": "check_degraded",
    "ok": "check_recovered",
}

# A check that stops being evaluated while it was NOT ok is a loss of visibility,
# not a recovery. Saying nothing would let a failing check disappear quietly —
# the silent-success shape this project keeps getting bitten by.
_VANISHED_EVENT = "check_vanished"


def _state_path() -> Path:
    """Sidecar holding the last-seen state per check.

    Shares the auth log's directory so the ``REBALANCE_AUTH_LOG_DIR`` seam moves
    both together; a test that redirects the log must not leave this behind
    pointing at the real one.
    """
    return auth_log._log_dir() / "health_state.json"


def _load_state() -> dict[str, str]:
    path = _state_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # A corrupt sidecar must not stop the log. Treating it as empty
        # re-reports current state once, which is noisy but honest; refusing to
        # log would be the quiet failure.
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


def _save_state(state: Mapping[str, str]) -> None:
    try:
        _state_path().write_text(json.dumps(dict(state), indent=2, sort_keys=True), encoding="utf-8")
    except OSError:
        pass  # never let bookkeeping break the caller


def _field(check: Any, key: str) -> str:
    """Read one field from either a doctor ``Check`` or the reporter's dict shape.

    Both callers exist: ``health_issue_reporter`` already holds dicts, and
    ``doctor`` holds ``Check`` objects. Converting at one of the call sites would
    be tidier than accepting both, but it would put the shape knowledge in the
    caller rather than here, where the vocabulary already lives.
    """
    value = check.get(key, "") if isinstance(check, Mapping) else getattr(check, key, "")
    return str(value or "")


def _normalize(check: Any) -> tuple[str, str, str, str]:
    return (
        _field(check, "name"),
        _field(check, "status").lower(),
        _field(check, "detail"),
        _field(check, "hint"),
    )


def log_health_transitions(checks: Iterable[Any]) -> list[tuple[str, str, str]]:
    """Append one system-log event per check whose state CHANGED since last call.

    Returns the transitions as ``(name, previous_state, new_state)`` so callers
    can report what they wrote. Unchanged checks produce nothing at all — see the
    module docstring for why that is load-bearing rather than an optimisation.
    """
    previous = _load_state()
    current: dict[str, str] = {}
    transitions: list[tuple[str, str, str]] = []

    for check in checks:
        name, status, detail, hint = _normalize(check)
        if not name or status not in _EVENT_FOR_STATE:
            continue
        current[name] = status
        was = previous.get(name)
        if was == status:
            continue
        # A first sighting that is already ok is not news — it is the baseline.
        # A first sighting that is failing IS news, so it is not filtered here.
        if was is None and status == "ok":
            continue
        auth_log.log_event(
            SOURCE,
            _EVENT_FOR_STATE[status],
            {
                "check": name,
                "from": was or "unseen",
                "to": status,
                "detail": detail,
                **({"hint": hint} if hint else {}),
            },
        )
        transitions.append((name, was or "unseen", status))

    for name, was in previous.items():
        if name in current or was == "ok":
            continue
        auth_log.log_event(SOURCE, _VANISHED_EVENT, {"check": name, "from": was, "to": "unseen"})
        transitions.append((name, was, "unseen"))

    _save_state(current)
    return transitions
