"""Reconciled collector-health verdict — one source of truth for the dashboards.

`doctor.run_doctor()` produces raw per-check results. This module reconciles
them against recent collector activity and collapses them into a single
`HealthStatus`, so every surface (web pulse, TUI, …) renders a *consistent*
verdict instead of three independently-computed pills that can contradict each
other.

Two reconciliations, both "a recent success is evidence the problem cleared":

* **Credential checks** (`vault` / `calendar` / `gmail` / `sleuth`): a WARN is
  suppressed when that source synced within its stale window.
* **Auth checks** (`auth:github` / `auth:gmail` / `auth:calendar`, emitted by
  ``doctor._check_auth_failures`` from the unified auth log): a WARN is
  suppressed when the *underlying collector* synced recently — independent
  evidence the credential works now, even if no success event was logged after
  the failure. This is what lets a deauth warning self-clear on recovery for
  every install, not just one machine.

Suppression windows are derived from ``doctor.py``'s collector-freshness
registry (``freshness_warn_hours``), so each source's staleness threshold is
written down exactly once (GH-5 Phase O3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from rebalance.doctor import (
    ERROR,
    FAIL,
    NOTICE,
    OK,
    WARN,
    WARNING,
    Check,
    freshness_warn_hours,
)

# Credential-check name → suppression window (hours), derived from the doctor
# freshness registry's warn_days for the same source. Vault is the one check
# with no freshness registry entry, so it keeps an explicit 2-day default.
CREDENTIAL_SUPPRESSION_HOURS: dict[str, int] = {
    "vault": 48,  # no freshness check; 2d safe default
    "calendar": freshness_warn_hours("calendar data"),
    "gmail": freshness_warn_hours("email data"),
    "sleuth": freshness_warn_hours("sleuth data"),
}

# auth:* check name → (freshness status key, window hours). A recent successful
# sync of the underlying collector clears a stale auth WARN.
AUTH_RECOVERY: dict[str, tuple[str, int]] = {
    "auth:github": ("github data", freshness_warn_hours("github data")),
    "auth:gmail": ("gmail", freshness_warn_hours("email data")),
    "auth:calendar": ("calendar", freshness_warn_hours("calendar data")),
}


def _parse_iso(raw: Any) -> datetime | None:
    from rebalance.lib.time_ops import _parse_iso as common_parse_iso

    return common_parse_iso(raw, force_utc=True)


def status_timestamp(status: dict[str, Any], key: str) -> str | None:
    """Most-recent successful-activity timestamp for a check/source *key*.

    Reads the index-status snapshot's ``sources`` block. Keys match the doctor
    check names that participate in suppression.
    """
    sources = status.get("sources") or {}
    semantic = status.get("semantic_index") or {}
    mapping = {
        "vault": (sources.get("vault") or {}).get("last_ingested_at"),
        "github data": (sources.get("github") or {}).get("activity_last_scanned_at")
        or (sources.get("github") or {}).get("documents_last_fetched_at"),
        "calendar": (sources.get("calendar") or {}).get("last_fetched_at"),
        "sleuth": (sources.get("sleuth") or {}).get("last_synced_at"),
        "gmail": (sources.get("email") or {}).get("last_synced_at"),
        "semantic": semantic.get("last_embedded_at"),
    }
    return mapping.get(key)


def source_recently_succeeded(status: dict[str, Any], key: str, now: datetime, *, within_hours: int = 48) -> bool:
    dt = _parse_iso(status_timestamp(status, key))
    if dt is None:
        return False
    return (now - dt).total_seconds() <= within_hours * 3600


def _is_suppressed(name: str, status: dict[str, Any], now: datetime) -> bool:
    if name in CREDENTIAL_SUPPRESSION_HOURS:
        return source_recently_succeeded(status, name, now, within_hours=CREDENTIAL_SUPPRESSION_HOURS[name])
    if name in AUTH_RECOVERY:
        fresh_key, hours = AUTH_RECOVERY[name]
        return source_recently_succeeded(status, fresh_key, now, within_hours=hours)
    return False


def _is_attention(check: Check) -> bool:
    """A check the reconciler even considers: FAIL/WARN status, or an explicit
    notice (an OK check the operator still wants rendered, muted)."""
    return check.status in {FAIL, WARN} or check.severity == NOTICE


def visible_problem_checks(checks: list[Check], status: dict[str, Any], now: datetime) -> list[Check]:
    """Attention checks plus explicit notices, minus recovered WARNs."""
    visible: list[Check] = []
    for check in checks:
        if not _is_attention(check):
            continue
        recovered_auth = check.name.startswith("auth:")
        if (
            check.status == WARN
            and (check.severity == WARNING or recovered_auth)
            and _is_suppressed(check.name, status, now)
        ):
            continue
        visible.append(check)
    return visible


def ordered_problem_checks(checks: list[Check], status: dict[str, Any], now: datetime) -> list[Check]:
    """Visible checks, worst-first by explicit severity; launchd noise last."""

    def priority(check: Check) -> tuple[int, int, str]:
        severity = {ERROR: 0, WARNING: 1, NOTICE: 2}[check.severity]
        launchd = 1 if check.name.startswith("launchd:") else 0
        return (severity, launchd, check.name)

    return sorted(visible_problem_checks(checks, status, now), key=priority)


def _matches_notice(name: str, patterns: list[str]) -> bool:
    """True if *name* contains any notice pattern (case-insensitive substring)."""
    low = name.lower()
    return any(p.lower() in low for p in patterns if p)


@dataclass
class HealthStatus:
    """The one verdict every dashboard surface renders from.

    ``problems`` contains error/warning checks and drives the verdict.
    ``notices`` contains explicit notice-severity checks plus WARNs the operator
    has marked as intentional. Surfaces render that list muted and collapsed;
    it never escalates the verdict.
    """

    verdict: str  # OK | WARN | FAIL
    problems: list[Check]
    notices: list[Check] = field(default_factory=list)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.problems if c.severity == ERROR]

    @property
    def errors(self) -> list[Check]:
        return self.failures

    @property
    def warnings(self) -> list[Check]:
        return [c for c in self.problems if c.severity == WARNING]

    @property
    def count(self) -> int:
        return len(self.problems)

    @property
    def status_text(self) -> str:
        # Keep the compact legacy label when there are no notices. Once the
        # collapsed notice tier is present, expose the complete bucket summary.
        if self.notices:
            return self.bucket_text
        if self.errors:
            return _bucket_label(len(self.errors), "error")
        if self.warnings:
            return _bucket_label(len(self.warnings), "warning")
        return "healthy"

    @property
    def problem_text(self) -> str:
        """Actionable summary — errors and warnings ONLY (GH-100).

        ``status_text`` folds notices into the count, which is right for a
        complete panel summary and wrong for a headline: notices are checks the
        operator has already marked intentional, so counting them next to a real
        error tells them 21 things need attention when one does. Header surfaces
        render THIS; the notices tier carries its own count where it lives.

        Returns ``"healthy"`` when nothing is actionable, so a caller can render
        one element in every state instead of branching into a second widget.
        """
        buckets = ((len(self.errors), "error"), (len(self.warnings), "warning"))
        parts = [_bucket_label(count, name) for count, name in buckets if count]
        return " · ".join(parts) if parts else "healthy"

    @property
    def bucket_text(self) -> str:
        """Complete panel summary, omitting empty buckets."""
        buckets = (
            (len(self.errors), "error"),
            (len(self.warnings), "warning"),
            (len(self.notices), "notice"),
        )
        return " · ".join(_bucket_label(count, name) for count, name in buckets if count)


def _bucket_label(count: int, name: str) -> str:
    return f"{count} {name}{'' if count == 1 else 's'}"


def compute_health_status(
    checks: list[Check],
    status: dict[str, Any],
    now: datetime,
    *,
    notice_patterns: list[str] | None = None,
) -> HealthStatus:
    """Reconcile *checks* against recent activity into a single verdict.

    *notice_patterns* (defaults to ``config.get_health_notice_patterns()``)
    demote matching warning-severity checks to ``notices``. Explicit notice
    severity needs no per-device configuration. Error severity is never
    demoted, even where the legacy status remains WARN for CLI compatibility.
    """
    if notice_patterns is None:
        try:
            from rebalance.ingest.config import get_health_notice_patterns

            notice_patterns = get_health_notice_patterns()
        except Exception:  # noqa: BLE001 — never let config break the verdict
            notice_patterns = []

    visible = ordered_problem_checks(checks, status, now)
    problems: list[Check] = []
    notices: list[Check] = []
    for check in visible:
        configured_notice = (
            check.severity == WARNING and check.status == WARN and _matches_notice(check.name, notice_patterns)
        )
        if check.severity == NOTICE or configured_notice:
            notices.append(check)
        else:
            problems.append(check)

    if any(c.severity == ERROR for c in problems):
        verdict = FAIL
    elif any(c.severity == WARNING for c in problems):
        verdict = WARN
    else:
        verdict = OK
    return HealthStatus(verdict=verdict, problems=problems, notices=notices)


def check_dispositions(checks: list[Check], health: HealthStatus) -> list[tuple[Check, str]]:
    """Classify every raw check against a computed ``HealthStatus``.

    This is what makes a binary verdict diagnosable: raw checks alone cannot
    say *why* something was hidden or demoted, because that decision lives in
    the reconciler. Dispositions:

    * ``problem`` — visible; drives the verdict.
    * ``notice`` — visible but muted; never escalates the verdict.
    * ``suppressed`` — a recovered WARN the reconciler hid (that source synced
      successfully within its stale window).
    * ``ok`` — nothing to reconcile.

    *health* must have been computed from this same ``checks`` list —
    membership is by object identity, since ``Check`` is an unfrozen dataclass
    and two distinct checks may compare equal.
    """
    problem_ids = {id(c) for c in health.problems}
    notice_ids = {id(c) for c in health.notices}
    out: list[tuple[Check, str]] = []
    for check in checks:
        if id(check) in problem_ids:
            disposition = "problem"
        elif id(check) in notice_ids:
            disposition = "notice"
        elif _is_attention(check):
            disposition = "suppressed"
        else:
            disposition = "ok"
        out.append((check, disposition))
    return out
