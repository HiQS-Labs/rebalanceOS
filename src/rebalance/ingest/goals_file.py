"""Shared read/write helpers for the operator's ``0. Goals.md`` file."""

from __future__ import annotations

import hashlib
import os
import re
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4
from rebalance.lib.time_ops import now_iso

CHECKBOX_RE = re.compile(r"^\s*-\s*\[(?P<mark>[ xX])\]\s*(?P<title>.*)$")
HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")

_FILE_LOCKS: dict[str, threading.Lock] = {}
_GLOBAL_LOCK = threading.Lock()


def _get_path_lock(path: Path) -> threading.Lock:
    resolved = str(path.expanduser().resolve())
    with _GLOBAL_LOCK:
        if resolved not in _FILE_LOCKS:
            _FILE_LOCKS[resolved] = threading.Lock()
        return _FILE_LOCKS[resolved]


class StaleRevisionError(Exception):
    """Raised when expected_revision does not match current file content hash."""

    def __init__(self, current_revision: str, expected_revision: str):
        super().__init__(
            f"Stale goals revision: expected {expected_revision}, current {current_revision}"
        )
        self.current_revision = current_revision
        self.expected_revision = expected_revision


class AmbiguousGoalError(Exception):
    """Raised when multiple open goals match title without an unambiguous revision/line index."""

    def __init__(self, title: str, matching_indexes: list[int]):
        super().__init__(
            f"Ambiguous goal title '{title}' matches lines {matching_indexes}"
        )
        self.title = title
        self.matching_indexes = matching_indexes


@dataclass
class RawSectionGroup:
    header: str | None
    header_line_index: int | None
    tasks: list[dict[str, Any]]


def compute_goals_revision(content: str) -> str:
    """Compute SHA-256 hash of goals file content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def parse_goals_content(content: str, limit: int | None = 3) -> list[dict[str, Any]]:
    """Parse unchecked checklist items from content string into ``{title, description, line_index}``."""
    items: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line_index, raw in enumerate(content.splitlines()):
        if not raw.strip():
            continue
        m = CHECKBOX_RE.match(raw)
        if m:
            if current is not None:
                items.append(current)
            is_done = m.group("mark").lower() == "x"
            if is_done:
                current = None
            else:
                current = {
                    "done": False,
                    "title": m.group("title").strip(),
                    "description": "",
                    "line_index": line_index,
                }
            continue
        if current is None:
            continue
        current["description"] = (current["description"] + " " + raw.strip()).strip()
    if current is not None:
        items.append(current)
    return items if limit is None else items[:limit]


def parse_sectioned_goals_content(content: str) -> list[RawSectionGroup]:
    """Parse open checklist items grouped by markdown section headers."""
    groups: list[RawSectionGroup] = []
    current_group = RawSectionGroup(header=None, header_line_index=None, tasks=[])
    current_task: dict[str, Any] | None = None

    for line_index, raw in enumerate(content.splitlines()):
        stripped = raw.strip()
        if not stripped:
            continue

        hm = HEADER_RE.match(raw)
        if hm:
            if current_task is not None:
                current_group.tasks.append(current_task)
                current_task = None
            if current_group.header is not None or current_group.tasks:
                groups.append(current_group)
            current_group = RawSectionGroup(
                header=hm.group(2).strip(),
                header_line_index=line_index,
                tasks=[],
            )
            continue

        cm = CHECKBOX_RE.match(raw)
        if cm:
            if current_task is not None:
                current_group.tasks.append(current_task)
                current_task = None
            is_done = cm.group("mark").lower() == "x"
            if not is_done:
                current_task = {
                    "done": False,
                    "title": cm.group("title").strip(),
                    "description": "",
                    "line_index": line_index,
                }
            continue

        if current_task is not None:
            current_task["description"] = (
                current_task["description"] + " " + stripped
            ).strip()

    if current_task is not None:
        current_group.tasks.append(current_task)
    if current_group.header is not None or current_group.tasks:
        groups.append(current_group)

    return groups


def parse_goals(path: Path, limit: int | None = 3) -> list[dict[str, Any]]:
    """Parse unchecked checklist items into ``{title, description, line_index}``.

    Format:
        - [ ] Title line
        Optional description spanning until blank line or next checkbox.
    """
    if not path.exists():
        return []
    return parse_goals_content(path.read_text(encoding="utf-8"), limit=limit)


def parse_sectioned_goals(path: Path) -> list[RawSectionGroup]:
    """Parse open checklist items grouped by markdown section headers."""
    if not path.exists():
        return []
    return parse_sectioned_goals_content(path.read_text(encoding="utf-8"))


def goal_file_exists(path: Path) -> bool:
    return path.is_file()


def _candidate_indexes(total: int, preferred: int | None) -> list[int]:
    indexes: list[int] = []
    if preferred is not None and 0 <= preferred < total:
        indexes.append(preferred)
    indexes.extend(i for i in range(total) if i not in indexes)
    return indexes


def _rewrite_open_goal_line(raw: str) -> str:
    ending = ""
    if raw.endswith("\r\n"):
        ending = "\r\n"
    elif raw.endswith("\n"):
        ending = "\n"
    body = raw[: -len(ending)] if ending else raw
    return body.replace("[ ]", "[x]", 1) + ending


def complete_goal_in_file(
    path: Path,
    title: str,
    *,
    line_index: int | None = None,
    expected_revision: str | None = None,
) -> dict[str, Any] | None:
    """Mark one unchecked checkbox line complete in place.

    Thread-safe, process-local lock serialized.
    If expected_revision is supplied, validates SHA-256 match first; raises
    StaleRevisionError if changed.
    If expected_revision is omitted, strictly checks for ambiguous duplicates first;
    raises AmbiguousGoalError if >1 open matches.
    Write is atomic via unique NamedTemporaryFile and os.replace.
    """
    if not path.exists():
        return None
    target = title.strip()
    if not target:
        return None

    lock = _get_path_lock(path)
    with lock:
        content = path.read_text(encoding="utf-8")
        current_rev = compute_goals_revision(content)

        if expected_revision is not None and current_rev != expected_revision:
            raise StaleRevisionError(
                current_revision=current_rev,
                expected_revision=expected_revision,
            )

        lines = content.splitlines(keepends=True)
        matching_open_indexes: list[int] = []
        for i, line in enumerate(lines):
            m = CHECKBOX_RE.match(line.rstrip("\r\n"))
            if m and m.group("mark").lower() != "x" and m.group("title").strip() == target:
                matching_open_indexes.append(i)

        if not matching_open_indexes:
            return None

        chosen_index: int | None = None
        if line_index is not None and line_index in matching_open_indexes:
            chosen_index = line_index
        elif len(matching_open_indexes) > 1:
            raise AmbiguousGoalError(target, matching_open_indexes)
        else:
            chosen_index = matching_open_indexes[0]

        raw = lines[chosen_index]
        updated = _rewrite_open_goal_line(raw)
        lines[chosen_index] = updated
        new_content = "".join(lines)
        new_rev = compute_goals_revision(new_content)

        parent = path.parent
        parent.mkdir(parents=True, exist_ok=True)
        tmp = tempfile.NamedTemporaryFile(
            dir=parent,
            prefix=".goals_",
            suffix=".tmp",
            delete=False,
            mode="w",
            encoding="utf-8",
        )
        try:
            tmp.write(new_content)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp.close()
            os.replace(tmp.name, str(path))
        except Exception:
            if os.path.exists(tmp.name):
                try:
                    os.unlink(tmp.name)
                except OSError:
                    pass
            raise

        return {
            "id": uuid4().hex,
            "title": target,
            "goals_path": str(path.expanduser().resolve()),
            "line_index": chosen_index,
            "before_line": raw,
            "after_line": updated,
            "completed_at": now_iso(),
            "goals_revision": new_rev,
        }


def goal_completion_still_applied(path: Path, entry: dict[str, Any]) -> bool:
    """Return True when the completion record still matches a checked line."""
    if not path.exists():
        return False
    title = str(entry.get("title") or "").strip()
    after_line = str(entry.get("after_line") or "")
    if not title:
        return False

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    line_index = entry.get("line_index")
    if isinstance(line_index, int) and 0 <= line_index < len(lines):
        raw = lines[line_index]
        m = CHECKBOX_RE.match(raw.rstrip("\n"))
        if m and m.group("mark").lower() == "x" and m.group("title").strip() == title:
            if not after_line or raw == after_line:
                return True

    for raw in lines:
        m = CHECKBOX_RE.match(raw.rstrip("\n"))
        if not m or m.group("mark").lower() != "x":
            continue
        if m.group("title").strip() != title:
            continue
        if not after_line or raw == after_line:
            return True
    return False


def undo_goal_completion_in_file(path: Path, entry: dict[str, Any]) -> bool:
    """Revert one completion record back to an unchecked checkbox."""
    if not path.exists():
        return False
    before_line = str(entry.get("before_line") or "")
    after_line = str(entry.get("after_line") or "")
    title = str(entry.get("title") or "").strip()
    if not before_line or not title:
        return False

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    candidate_indexes = _candidate_indexes(len(lines), entry.get("line_index"))

    for index in candidate_indexes:
        raw = lines[index]
        m = CHECKBOX_RE.match(raw.rstrip("\n"))
        if not m or m.group("mark").lower() != "x":
            continue
        if m.group("title").strip() != title:
            continue
        if after_line and raw != after_line and index == entry.get("line_index"):
            continue
        lines[index] = before_line
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text("".join(lines), encoding="utf-8")
        tmp.replace(path)
        return True
    return False
