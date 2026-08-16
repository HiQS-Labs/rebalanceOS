"""One-way bridge from rebalance into the standalone 3-Eyes supervisor.

GH-5 Phase 6. This adapter already existed as ``web.py:_three_eyes_health_scan``
with working tests; it moved here so ``doctor.py`` can reuse it without
importing ``web.py`` (which would drag FastAPI into the CLI's import path).
``web.py`` now delegates to this module.

**The dependency direction is deliberately one-way.** 3-Eyes runs from its own
launchd shim under a limited ``PYTHONPATH`` and is designed to degrade
gracefully when the repo venv is absent — that is the condition it exists to
survive. So rebalance reaches into 3-Eyes here; 3-Eyes never imports
``rebalance``. In particular 3-Eyes keeps its own package-relative
``ROOT.parent.parent`` root resolver rather than adopting ``rebalance.paths``.

Failure model — the reason this module exists rather than a bare call:

``scan()`` does **not** raise when it cannot probe launchd. It returns a
structured report with ``launchctl_available: False`` and a ``probe_error``
string, and every row's ``health`` set to ``"unknown"``. A caller that only
guards against exceptions will read that report as "0 failing" and report
everything fine. Both failure shapes are therefore made explicit here:

- 3-Eyes not active on this machine  -> ``None`` (nothing to report)
- import/scan blew up                -> :class:`ThreeEyesUnavailable`
- probed but launchctl unreadable    -> report with ``launchctl_available``
  False; callers must check it, and :func:`probe_unavailable_reason` is the
  supported way to do so.
"""

from __future__ import annotations

from pathlib import Path

_THREE_EYES_DIR = Path(__file__).resolve().parents[2] / "utils" / "3-eyes"


class ThreeEyesUnavailable(RuntimeError):
    """3-Eyes could not be imported or its scan raised.

    Distinct from "3-Eyes is inactive here" (``None``) and from "3-Eyes ran but
    could not read launchd" (a report with ``launchctl_available`` False).
    """


def health_scan() -> dict | None:
    """Return ``three_eyes.health.scan()`` when 3-Eyes is ACTIVE here, else None.

    Raises :class:`ThreeEyesUnavailable` if the import or the scan itself fails.
    Callers that must not propagate (a web endpoint, a doctor check) catch it
    explicitly — the point is that they *choose* to, rather than a bare except
    silently turning a broken supervisor into a clean bill of health.
    """
    import sys

    directory = str(_THREE_EYES_DIR)
    if directory not in sys.path:
        sys.path.insert(0, directory)
    try:
        from three_eyes import config as te_config, health as te_health
    except Exception as exc:  # noqa: BLE001 — any import failure is "unavailable"
        raise ThreeEyesUnavailable(f"3-Eyes import failed: {exc}") from exc

    try:
        if not te_config.three_eyes_active():
            return None
        return te_health.scan()
    except Exception as exc:  # noqa: BLE001 — a broken probe must not read as healthy
        raise ThreeEyesUnavailable(f"3-Eyes scan failed: {exc}") from exc


def probe_unavailable_reason(report: dict) -> str:
    """Return why 3-Eyes could not read launchd, or "" when it could.

    ``scan()`` represents an unreadable ``launchctl`` as a structured result, not
    an exception. Without this check a caller sees ``failing == 0`` and reports
    the fleet healthy when in fact nothing was observed at all — the exact
    misread 3-Eyes' own ``"unknown"`` state was introduced to prevent.
    """
    if report.get("launchctl_available", True):
        return ""
    return str(report.get("probe_error") or "launchctl could not be read")
