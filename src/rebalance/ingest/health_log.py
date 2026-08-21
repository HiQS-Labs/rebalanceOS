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
import logging
import os
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

# ...but ONE absence is not proof of a vanish. `run_doctor` genuinely returns a
# SUBSET in normal operation — the schema and project checks are gated on the
# database existing (doctor.py, `if db_path:`), so losing the database drops
# several checks at once. A single-run rule would log every one of them as
# vanished and then, when the database came back, log every one again as a fresh
# failure: flapping instead of reporting. Requiring the absence to REPEAT means a
# transient bad run stays quiet while a genuine disappearance is still reported,
# one run later.
_ABSENCES_BEFORE_VANISHED = 2

logger = logging.getLogger(__name__)


def _state_path() -> Path:
    """Sidecar holding the last-seen state per check.

    Shares the auth log's directory so the ``REBALANCE_AUTH_LOG_DIR`` seam moves
    both together; a test that redirects the log must not leave this behind
    pointing at the real one.
    """
    return auth_log._log_dir() / "health_state.json"


def _load_state() -> tuple[dict[str, str], dict[str, int]]:
    """Return ``(last state per check, consecutive-absence counts)``.

    Accepts the original flat ``{name: state}`` shape as well, so a sidecar
    written before the absence counter existed is read rather than discarded —
    discarding it would re-report every failing check once on upgrade.
    """
    path = _state_path()
    if not path.exists():
        return {}, {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # A corrupt sidecar must not stop the log. Treating it as empty
        # re-reports current state once, which is noisy but honest; refusing to
        # log would be the quiet failure. Say so out loud — a sidecar that is
        # corrupt EVERY run is a flood, and the log alone would not explain it.
        logger.warning("health_log: unreadable state file %s — treating as empty", path)
        return {}, {}
    if not isinstance(data, dict):
        return {}, {}
    if "checks" in data or "absent" in data:
        checks = data.get("checks") or {}
        absent = data.get("absent") or {}
        return (
            {str(k): str(v) for k, v in checks.items()},
            {str(k): int(v) for k, v in absent.items() if str(v).lstrip("-").isdigit()},
        )
    return {str(k): str(v) for k, v in data.items()}, {}


def _save_state(checks: Mapping[str, str], absent: Mapping[str, int]) -> bool:
    """Persist state ATOMICALLY. Returns whether it landed.

    Atomic because two processes can run this concurrently (the hourly job and a
    manual invocation), and a half-written sidecar reads as corrupt — which sends
    the next run down the re-report-everything path. Write-then-replace makes the
    interleaving cost a duplicate event at worst, never a corrupt file.

    A persistent write failure is the flooding case: state never advances, so
    every run re-reports every failing check. It cannot be prevented without
    somewhere to write, so it is at least made LOUD.
    """
    payload = {"checks": dict(checks), "absent": {k: v for k, v in absent.items() if v}}
    path = _state_path()
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        os.replace(tmp, path)
        return True
    except OSError as exc:
        logger.warning(
            "health_log: could not persist state to %s (%s) — the next run will re-report "
            "every non-ok check, and will keep doing so until this write succeeds",
            path,
            exc,
        )
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        return False


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
    previous, absent = _load_state()
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

    if not current:
        # Zero usable checks is a FAILED RUN, not a world in which everything
        # recovered. Sweeping here would log every known check as vanished, and
        # persisting the empty result would erase the state so the next healthy
        # run re-reported every failure from scratch. Keep the previous state
        # untouched and say nothing.
        logger.warning("health_log: no usable checks in this run — state left unchanged")
        return transitions

    still_absent: dict[str, int] = {}
    for name, was in previous.items():
        if name in current or was == "ok":
            continue
        streak = absent.get(name, 0) + 1
        if streak < _ABSENCES_BEFORE_VANISHED:
            # Not yet proof. Carry the check's last state forward so a reappearance
            # next run is a no-op rather than a fresh failure.
            still_absent[name] = streak
            current[name] = was
            continue
        auth_log.log_event(
            SOURCE,
            _VANISHED_EVENT,
            {"check": name, "from": was, "to": "unseen", "absent_runs": streak},
        )
        transitions.append((name, was, "unseen"))

    _save_state(current, still_absent)
    return transitions
