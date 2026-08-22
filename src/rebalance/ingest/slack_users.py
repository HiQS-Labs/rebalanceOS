"""
Slack user lookup — single source of truth for friendly-name rendering.

Reads and maintains ``temp/slack_users.json`` (gitignored) and exposes
two helpers:

  - ``load_user_map()`` — returns the {user_id: friendly_name} dict
  - ``resolve_slack_user()`` — resolves a cache miss from an export payload
    or the optional Slack ``users.info`` API, then writes it through to cache
  - ``format_slack_mentions(text)`` — rewrites ``<@U…>`` mentions in
    arbitrary text using the lookup, with sensible fallbacks

The file shape:

    {
      "_README": "...",
      "users": {
        "U01EXAMPLE1": "Alice",
        "U02EXAMPLE2": "Bob"
      }
    }

Edits are picked up automatically — the loader keys its cache off the
file's mtime, so a running dashboard or background pulse job will reflect
new entries on the next read without a restart.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from threading import Lock
from typing import Any, Mapping
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SLACK_USERS_PATH = Path(__file__).parent.parent.parent.parent / "temp" / "slack_users.json"

# Slack mention forms we know about:
#   <@U12345678>           — plain user mention
#   <@U12345678|alice>     — user mention with display name fallback
#   <@W12345678>           — Slack Connect / external workspace user
# We deliberately do NOT match <#C…> (channel) or <!subteam^…> (groups)
# — those are different surface forms and not the user's request.
_MENTION_RE = re.compile(r"<@([UW][A-Z0-9]+)(?:\|([^>]+))?>")

# Sleuth reminders posted by the Sleuth bot follow a stable shape:
#
#   <@U…>, <@U…> - please follow up on <https://…>
#   <@U…> — please follow up on <https://…>
#
# The mention list is just bookkeeping (the dashboard already filters to
# reminders assigned to the operator), so the actually useful content is
# whatever follows "please follow up on". We strip the prefix to claw back
# screen real estate. If the pattern doesn't match — e.g. a manual
# reminder with custom phrasing — we leave the message untouched.
_SLEUTH_PREFIX_RE = re.compile(
    r"^@[^,:\-–—]+(?:\s*,\s*@[^,:\-–—]+)*\s*[-–—:]\s*please\s+follow\s+up\s+on\s+",
    flags=re.IGNORECASE,
)

# Slack wraps URLs in angle brackets, optionally with a "|label" suffix.
# Examples: <https://example.com>, <https://example.com|click here>.
# We unwrap so the link reads naturally in a terminal cell, preferring
# the label when present (Slack does the same).
_SLACK_LINK_RE = re.compile(r"<((?:https?|mailto):[^|>]+)(?:\|([^>]+))?>")

_cache_lock = Lock()
_cache: dict[str, Any] = {"path": None, "mtime": None, "users": {}}

_CACHE_README = (
    "Slack user names resolved automatically from export payloads or the "
    "optional Slack users.info API. Manual entries are also supported."
)


def get_slack_users_path() -> Path:
    """Return the canonical lookup-file path (used by setup and docs)."""
    return SLACK_USERS_PATH


def load_user_map() -> dict[str, str]:
    """Return the current {user_id: friendly_name} mapping.

    Cached against the file's mtime so callers can hammer this on every
    UI tick without an inflated read cost; an external editor save will
    invalidate the cache on the next call.
    """
    path = SLACK_USERS_PATH
    if not path.exists():
        return {}
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return {}

    with _cache_lock:
        if _cache["path"] == path and _cache["mtime"] == mtime:
            return dict(_cache["users"])

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # Bad JSON shouldn't kill the dashboard — fall back to empty
            # and let the next save fix it.
            _cache["path"] = path
            _cache["mtime"] = mtime
            _cache["users"] = {}
            return {}

        users_block = raw.get("users") if isinstance(raw, dict) else None
        users: dict[str, str] = {}
        if isinstance(users_block, dict):
            for k, v in users_block.items():
                if isinstance(k, str) and isinstance(v, str) and k and v:
                    users[k] = v
        _cache["path"] = path
        _cache["mtime"] = mtime
        _cache["users"] = users
        return dict(users)


def _write_user_map(users: Mapping[str, str]) -> None:
    """Atomically persist a map and synchronise the in-process cache.

    The cache lock covers the read-modify-write merge, so concurrent cache
    misses cannot overwrite one another. ``os.replace`` ensures readers see
    either the prior complete JSON document or the new complete document.
    """
    path = SLACK_USERS_PATH
    with _cache_lock:
        # A second resolver may have populated the in-process map between this
        # caller's earlier ``load_user_map`` and its eventual write.
        merged_users = dict(_cache["users"]) if _cache["path"] == path else {}
        merged_users.update(users)
        payload = {"_README": _CACHE_README, "users": dict(sorted(merged_users.items()))}
        temp_name: str | None = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temp_name = handle.name
                handle.write(json.dumps(payload, indent=2) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
            mtime = path.stat().st_mtime
        except OSError:
            # Name rendering is an optional enhancement. A read-only temp dir
            # must not prevent its caller from showing the resolved name.
            if temp_name:
                try:
                    Path(temp_name).unlink(missing_ok=True)
                except OSError:
                    pass
            return
        _cache["path"] = path
        _cache["mtime"] = mtime
        _cache["users"] = merged_users


def _name_from_payload(payload: Mapping[str, Any] | None) -> str | None:
    """Extract the best friendly name from a Slack export/API user payload."""
    if not isinstance(payload, Mapping):
        return None

    candidates: list[Mapping[str, Any]] = [payload]
    for key in ("user_profile", "profile", "user"):
        nested = payload.get(key)
        if isinstance(nested, Mapping):
            candidates.append(nested)
            profile = nested.get("profile")
            if isinstance(profile, Mapping):
                candidates.append(profile)

    for candidate in candidates:
        for key in ("display_name", "real_name", "name", "username"):
            value = candidate.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def _fetch_slack_user(user_id: str, token: str) -> str | None:
    """Resolve *user_id* with Slack's users.info endpoint, failing softly."""
    url = "https://slack.com/api/users.info?" + urlencode({"user": user_id})
    request = Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urlopen(request, timeout=10) as response:  # noqa: S310 - fixed Slack API host
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError, UnicodeDecodeError):
        return None

    if not isinstance(body, Mapping) or body.get("ok") is not True:
        return None
    user = body.get("user")
    return _name_from_payload(user if isinstance(user, Mapping) else None)


def resolve_slack_user(
    user_id: str,
    *,
    payload: Mapping[str, Any] | None = None,
    inline_name: str | None = None,
) -> str | None:
    """Resolve a Slack user and write any newly discovered name through to cache.

    Resolution order is cache, name embedded in the source export payload,
    inline mention name, then Slack Web API (only when configured).  The cache
    is deliberately consulted first so routine pulse rendering makes neither
    filesystem writes nor network requests after the initial resolution.
    """
    if not isinstance(user_id, str) or not user_id:
        return None

    users = load_user_map()
    cached = users.get(user_id)
    if cached:
        return cached

    name = _name_from_payload(payload)
    if not name and isinstance(inline_name, str) and inline_name.strip():
        name = inline_name.strip()
    if not name:
        from .config import get_slack_bot_token  # noqa: PLC0415

        token = get_slack_bot_token()
        if token:
            name = _fetch_slack_user(user_id, token)
    if not name:
        return None

    users[user_id] = name
    _write_user_map(users)
    return name


def format_slack_mentions(text: str | None) -> str:
    """Rewrite Slack mention markup in *text* using the lookup file.

    Resolution order per mention:
      1. Friendly name from ``slack_users.json``
      2. Inline display name (the ``|name`` fallback in the mention markup)
      3. The raw user id, prefixed with ``@``
    """
    if not text:
        return text or ""

    def _sub(match: re.Match[str]) -> str:
        uid = match.group(1)
        inline = match.group(2)
        name = resolve_slack_user(uid, inline_name=inline) or inline or uid
        return f"@{name}"

    return _MENTION_RE.sub(_sub, text)


def unwrap_slack_links(text: str | None) -> str:
    """Replace Slack ``<URL>`` / ``<URL|label>`` markup with plain text."""
    if not text:
        return text or ""

    def _sub(match: re.Match[str]) -> str:
        url = match.group(1)
        label = match.group(2)
        return label if label else url

    return _SLACK_LINK_RE.sub(_sub, text)


def compact_sleuth_reminder(text: str | None) -> str:
    """Compact a raw Sleuth reminder for surfaces with limited width.

    Sleuth-bot reminders have a stable multi-line shape:

        @mentions - please follow up on <URL|this>:
        ><quoted Slack message>

        Key task(s):
        • <bullet derived from the source message>

    The header line is pure boilerplate (the dashboard already filters to
    reminders assigned to the operator), and the URL label is usually the
    uninformative word "this". The actually useful content is on the
    quoted line that follows the header, or — failing that — the first
    bullet in the "Key task(s)" block.

    Pipeline:
      1. ``format_slack_mentions`` — rewrite ``<@UXXX>`` → friendly names.
      2. If the text matches the Sleuth header pattern, drop the header
         and prefer the quoted body line; fall back to the first bullet,
         then to the first non-empty body line, then to the single-line
         post-strip text (covers reminders with no body).
      3. ``unwrap_slack_links`` on whatever we settled on, so
         ``<URL|label>`` reads as plain text (Slack's behaviour: prefer
         the label).

    If the header pattern doesn't match — e.g. a manually-typed reminder
    with custom phrasing — we return the message with mentions + links
    rewritten and the body otherwise untouched, so we never silently
    swallow unfamiliar content.
    """
    if not text:
        return text or ""
    rewritten = format_slack_mentions(text)

    if not _SLEUTH_PREFIX_RE.match(rewritten):
        return unwrap_slack_links(rewritten)

    lines = rewritten.splitlines()
    body = lines[1:] if len(lines) > 1 else []

    # Prefer the quoted source line ("> ...") — it's the most concise
    # restatement of the original Slack message that triggered the reminder.
    for line in body:
        stripped = line.lstrip()
        if stripped.startswith(">"):
            return unwrap_slack_links(stripped.lstrip(">").strip())

    # Fall back to the first "Key task(s)" bullet.
    for line in body:
        stripped = line.lstrip()
        if stripped[:1] in ("•", "-", "*"):
            return unwrap_slack_links(stripped[1:].lstrip())

    # Fall back to the first non-empty body line.
    for line in body:
        if line.strip():
            return unwrap_slack_links(line.strip())

    # No body — strip the header inline and unwrap whatever's left
    # (handles single-line reminders like
    # "@Noel - please follow up on <https://example.com>").
    return unwrap_slack_links(_SLEUTH_PREFIX_RE.sub("", rewritten)).strip()
