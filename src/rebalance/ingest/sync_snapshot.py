"""Device snapshot exporter for the multi-device sync plane (Issue #39).

Writes machine-readable JSON snapshots of calendar and email state to a
subfolder within the existing pulse repo so non-ingesting devices can
consume fresh derived data without needing Google credentials.

Directory layout (under {pulse_target_path}/{sync_subdir}/):
    calendar/
        <device_id>.json       per-device full snapshot (90-day window)
        latest.json            pointer to the freshest device snapshot
    email/
        <device_id>.json       per-device snapshot (newest N messages)
        latest.json            pointer to the freshest device snapshot

Snapshot format (schema_version=1):
    {
      "schema_version": 1,
      "source": "calendar" | "email",
      "device_id": "<hostname-slug>",
      "generated_at": "<iso8601-utc>",
      "window_days": 90,          # calendar only
      "limit": 1000,              # email only
      "row_count": <int>,
      "rows": [ ... ]             # see column lists below
    }

latest.json format:
    {
      "device_id": "<hostname-slug>",
      "generated_at": "<iso8601-utc>",
      "snapshot_file": "<device_id>.json"
    }
"""

from __future__ import annotations

import json
import socket
from datetime import timedelta
from pathlib import Path
from typing import Any

from rebalance.ingest.calendar_config import OPERATOR_CALENDAR_ID
from rebalance.ingest.db import db_connection
from rebalance.ingest.db.schema import ensure_calendar_schema, ensure_email_schema
from rebalance.lib.git_ops import (
    GitPublishLockBusy,
    git_publish_lock,
    publish_git_paths,
    run_git,
)
from rebalance.lib.time_ops import now_iso, now_utc, parse_utc_iso

SCHEMA_VERSION = 1
DEFAULT_CALENDAR_WINDOW_DAYS = 90
DEFAULT_EMAIL_LIMIT = 1000


def get_device_id() -> str:
    """Return a stable, filesystem-safe identifier for this machine.

    Derived from the hostname: lowercased, spaces and dots replaced with
    hyphens, non-alphanumeric characters (except hyphens) stripped.
    Falls back to ``"unknown-device"`` if hostname is unavailable.
    """
    try:
        raw = socket.gethostname()
    except Exception:  # noqa: BLE001
        return "unknown-device"
    slug = raw.lower().replace(" ", "-").replace(".", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")
    return slug or "unknown-device"


# ---------------------------------------------------------------------------
# Calendar snapshot
# ---------------------------------------------------------------------------

# `person` (added in migration 0005) is intentionally NOT exported — a teammate
# identity label stays local. The export is also primary-only (see the WHERE
# clause in export_calendar_snapshot), and `person` is NULL on primary rows
# anyway. Do not add it here without a deliberate privacy review.
_CALENDAR_COLUMNS = (
    "id",
    "summary",
    "start_time",
    "end_time",
    "location",
    "attendees_json",
    "calendar_id",
    "status",
    "description",
    "fetched_at",
)


def export_calendar_snapshot(
    database_path: Path,
    sync_dir: Path,
    *,
    window_days: int = DEFAULT_CALENDAR_WINDOW_DAYS,
    device_id: str | None = None,
) -> Path:
    """Export calendar_events to ``sync_dir/calendar/<device_id>.json``.

    Returns the path of the written snapshot file.
    Raises FileNotFoundError if database_path does not exist.
    """
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")

    dev_id = device_id or get_device_id()
    generated_at = now_iso()
    since = (now_utc() - timedelta(days=window_days)).isoformat()

    with db_connection(database_path, ensure_calendar_schema) as conn:
        # Default deny (P2 decision #3): only the operator's own calendar
        # (OPERATOR_CALENDAR_ID) is ever exported to the pulse repo. Teammate
        # calendars (calendar_id != OPERATOR_CALENDAR_ID) stay local to the
        # dashboard SQLite.
        # NOTE (0.40.1, F1): scope unified from a hardcoded 'primary' literal to
        # the OPERATOR_CALENDAR_ID constant (single source of truth). The bound
        # value is still FIXED (not caller-supplied) and 'primary' is reserved at
        # config load (finding D), so the no-widening guarantee is preserved.
        # REVERT PATH: inline the literal 'primary' here again.
        rows = conn.execute(
            f"""
            SELECT {", ".join(_CALENDAR_COLUMNS)}
            FROM calendar_events
            WHERE calendar_id = ? AND start_time >= ?
            ORDER BY start_time DESC
            """,
            (OPERATOR_CALENDAR_ID, since),
        ).fetchall()

    row_dicts = [dict(zip(_CALENDAR_COLUMNS, row)) for row in rows]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source": "calendar",
        "device_id": dev_id,
        "generated_at": generated_at,
        "window_days": window_days,
        "row_count": len(row_dicts),
        "rows": row_dicts,
    }

    out_path = _write_snapshot(sync_dir, "calendar", dev_id, payload)
    _update_latest_pointer(sync_dir / "calendar", dev_id, generated_at)
    return out_path


# ---------------------------------------------------------------------------
# Email snapshot
# ---------------------------------------------------------------------------

_EMAIL_COLUMNS = (
    "message_id",
    "thread_id",
    "from_address",
    "from_name",
    "subject",
    "snippet",
    "received_at",
    "labels_json",
    "synced_at",
)


def export_email_snapshot(
    database_path: Path,
    sync_dir: Path,
    *,
    limit: int = DEFAULT_EMAIL_LIMIT,
    device_id: str | None = None,
) -> Path:
    """Export email_messages to ``sync_dir/email/<device_id>.json``.

    Returns the path of the written snapshot file.
    Raises FileNotFoundError if database_path does not exist.
    """
    if not database_path.exists():
        raise FileNotFoundError(f"Database not found: {database_path}")

    dev_id = device_id or get_device_id()
    generated_at = now_iso()

    with db_connection(database_path, ensure_email_schema) as conn:
        rows = conn.execute(
            f"""
            SELECT {", ".join(_EMAIL_COLUMNS)}
            FROM email_messages
            ORDER BY received_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    row_dicts = [dict(zip(_EMAIL_COLUMNS, row)) for row in rows]
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "source": "email",
        "device_id": dev_id,
        "generated_at": generated_at,
        "limit": limit,
        "row_count": len(row_dicts),
        "rows": row_dicts,
    }

    out_path = _write_snapshot(sync_dir, "email", dev_id, payload)
    _update_latest_pointer(sync_dir / "email", dev_id, generated_at)
    return out_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _write_snapshot(
    sync_dir: Path,
    source: str,
    device_id: str,
    payload: dict[str, Any],
) -> Path:
    """Write ``sync_dir/<source>/<device_id>.json`` atomically."""
    dest = sync_dir / source / f"{device_id}.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(dest)
    return dest


def _update_latest_pointer(source_dir: Path, device_id: str, generated_at: str) -> None:
    """Update ``source_dir/latest.json`` if this device's snapshot is the freshest."""
    latest_path = source_dir / "latest.json"
    if latest_path.exists():
        try:
            current = json.loads(latest_path.read_text(encoding="utf-8"))
            current_stamp = parse_utc_iso(current.get("generated_at"))
            stamp = parse_utc_iso(generated_at)
            if current_stamp is None or stamp is None:
                raise ValueError("invalid latest pointer timestamp")
            if (current_stamp, current["device_id"]) >= (stamp, device_id):
                return
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid latest pointer") from exc

    pointer = {
        "device_id": device_id,
        "generated_at": generated_at,
        "snapshot_file": f"{device_id}.json",
    }
    tmp = latest_path.with_suffix(".tmp")
    tmp.write_text(json.dumps(pointer, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(latest_path)


def commit_and_push_sync(
    target_repo: Path,
    sync_subdir: str,
    *,
    device_id: str,
    generated_at: str,
    lock_acquired: bool = False,
) -> dict[str, Any]:
    """Publish only this device's payloads and the generated latest pointers."""
    if not lock_acquired:
        try:
            with git_publish_lock(target_repo):
                return commit_and_push_sync(
                    target_repo,
                    sync_subdir,
                    device_id=device_id,
                    generated_at=generated_at,
                    lock_acquired=True,
                )
        except GitPublishLockBusy as exc:
            return {"committed": False, "pushed": False, "deferred": True, "git_error": str(exc)}

    paths = [
        f"{sync_subdir}/{source}/{name}.json"
        for source in ("calendar", "email")
        for name in (device_id, "latest")
        if (target_repo / sync_subdir / source / f"{name}.json").exists()
    ]
    if not paths:
        return {"committed": False, "pushed": False, "reason": "no changes to sync"}
    return publish_git_paths(
        target_repo,
        paths,
        f"sync: {device_id} {generated_at}",
        resolve_conflicts=lambda: _resolve_pointer_conflicts(target_repo, sync_subdir),
    )


def _resolve_pointer_conflicts(target_repo: Path, sync_subdir: str) -> bool:
    """Resolve only generated pointers; malformed device evidence fails closed."""
    result = run_git(target_repo, "diff", "--name-only", "--diff-filter=U", "-z")
    conflicts = set(result.stdout.rstrip("\0").split("\0")) - {""}
    allowed = {f"{sync_subdir}/{source}/latest.json" for source in ("calendar", "email")}
    if result.returncode or not conflicts or not conflicts <= allowed:
        return False
    pointers = {}
    for relative in conflicts:
        directory = (target_repo / relative).parent
        candidates = []
        files = list(directory.glob("*.json"))
        if len(files) > 1000:
            raise ValueError("snapshot candidate limit exceeded")
        for path in files:
            if path.name == "latest.json":
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or path.is_symlink():
                raise ValueError(f"invalid snapshot evidence: {path.name}")
            stamp = parse_utc_iso(payload.get("generated_at"))
            device = payload.get("device_id")
            if (
                stamp is None
                or not device
                or path.name != f"{device}.json"
                or payload.get("source") != directory.name
                or payload.get("schema_version") != SCHEMA_VERSION
            ):
                raise ValueError(f"invalid snapshot evidence: {path.name}")
            candidates.append((stamp, device, payload["generated_at"]))
        if not candidates:
            return False
        _, device, generated_at = max(candidates)
        pointers[relative] = {"device_id": device, "generated_at": generated_at, "snapshot_file": f"{device}.json"}
    for relative, pointer in pointers.items():
        (target_repo / relative).write_text(json.dumps(pointer, indent=2), encoding="utf-8")
    return run_git(target_repo, "add", "--", *sorted(conflicts)).returncode == 0


def read_latest_snapshot(sync_dir: Path, source: str) -> dict[str, Any] | None:
    """Return the parsed contents of the freshest device snapshot, or None.

    Reads ``sync_dir/<source>/latest.json`` to find the device file, then
    loads and returns it. Returns None if no snapshots exist yet.
    """
    latest_path = sync_dir / source / "latest.json"
    if not latest_path.exists():
        return None
    try:
        pointer = json.loads(latest_path.read_text(encoding="utf-8"))
        snapshot_path = sync_dir / source / pointer["snapshot_file"]
        if not snapshot_path.exists():
            return None
        return json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
