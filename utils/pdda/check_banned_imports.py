"""Banned-import linter and SQLite gateway ratchet.

One file, two checks (GH-126's "choose one owner" rule forbids a second validator):

1. Import bans (legacy, warn-only): direct ``subprocess``/``datetime`` imports under
   ``src/rebalance/ingest`` outside ``rebalance.lib``. Printed by the default run and
   consumed by ``pdda.sh banned-imports``; not yet a gate.
2. SQLite gateway ratchet (GH-136, blocking via ``--check``): no file outside the two
   gateway directories may call ``sqlite3.connect``. The two gateways are separate
   stores by design — ``src/rebalance/ingest/db/`` (rebalance's own DB, resolved from
   ``REBALANCE_DB``) and ``HiQS/hiqs/`` (the clean-room rebuild's app-data store) — so
   they are not to be converged, only bypassing code is to be routed. ``--check``
   compares the tree against an exact per-file baseline and fails on additions (new
   debt) and on shrinks (a stale baseline that must be tightened deliberately).
   Finding identity is relative path + occurrence count; line numbers are diagnostic
   only, matching the ratchet contract #126 specifies.
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

SQLITE_CALL_RE = re.compile(r"sqlite3\.connect\s*\(")
SQLITE_ROOTS = ("src", "utils", "HiQS")
SQLITE_GATEWAY_DIRS = ("src/rebalance/ingest/db", "HiQS/hiqs")
SQLITE_SELF_EXEMPT = ("utils/pdda/check_banned_imports.py",)
SQLITE_PRUNED_DIRS = {"tests", "__pycache__"}
BASELINE_PATH = Path(__file__).with_name("sqlite_connect_baseline.json")


def check_file(path: Path) -> list[str]:
    errors = []
    try:
        content = path.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(path))
    except Exception:
        return []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in ("subprocess", "datetime") and "src/rebalance/lib" not in str(path):
                    errors.append(f"{path}:{node.lineno}: Banned import '{alias.name}'. Use rebalance.lib instead.")
        elif isinstance(node, ast.ImportFrom):
            if node.module in ("subprocess", "datetime") and "src/rebalance/lib" not in str(path):
                errors.append(f"{path}:{node.lineno}: Banned import from '{node.module}'. Use rebalance.lib instead.")
    return errors


def scan_sqlite_calls(root: Path) -> dict[str, int]:
    """Count direct SQLite connection call sites per file under the scanned roots.

    Tests directories, hidden/build directories, the two gateway directories, and this
    checker itself are exempt. Raises ``SystemExit`` on unreadable files rather than
    returning a silently incomplete result (fail closed).
    """
    counts: dict[str, int] = {}
    for top in SQLITE_ROOTS:
        for dirpath, dirnames, filenames in os.walk(root / top):
            dirnames[:] = [d for d in dirnames if d not in SQLITE_PRUNED_DIRS and not d.startswith(".")]
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                file_path = Path(dirpath) / name
                rel = file_path.relative_to(root).as_posix()
                if rel in SQLITE_SELF_EXEMPT:
                    continue
                if any(rel.startswith(gateway + "/") for gateway in SQLITE_GATEWAY_DIRS):
                    continue
                try:
                    content = file_path.read_text(encoding="utf-8")
                except OSError as exc:
                    raise SystemExit(f"sqlite gateway ratchet: cannot read {rel}: {exc}") from exc
                found = len(SQLITE_CALL_RE.findall(content))
                if found:
                    counts[rel] = found
    return counts


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, int]:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_to_baseline(actual: dict[str, int], baseline: dict[str, int]) -> list[str]:
    """Return ratchet findings: new debt and stale baseline entries both block.

    Each finding is ``path:1: message`` so downstream tooling that parses
    ``file:lineno: message`` (``pdda.sh``) can consume it unchanged.
    """
    findings: list[str] = []
    for rel in sorted(actual):
        if rel not in baseline:
            findings.append(
                f"{rel}:1: NEW sqlite3.connect bypass ({actual[rel]} site(s)) — route through a gateway (GH-136)"
            )
        elif actual[rel] > baseline[rel]:
            findings.append(
                f"{rel}:1: sqlite3.connect sites grew {baseline[rel]} -> {actual[rel]} — route through a gateway (GH-136)"
            )
    for rel in sorted(baseline):
        if rel not in actual:
            findings.append(
                f"{rel}:1: stale baseline — file is now clean; re-run with --update-baseline and review the diff"
            )
        elif baseline[rel] > actual[rel]:
            findings.append(
                f"{rel}:1: stale baseline — sites shrank {baseline[rel]} -> {actual[rel]}; re-run with --update-baseline and review the diff"
            )
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if "--update-baseline" in argv:
        actual = scan_sqlite_calls(Path.cwd())
        BASELINE_PATH.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"baseline updated: {len(actual)} file(s), {sum(actual.values())} site(s)")
        return 0

    if "--check" in argv:
        baseline = load_baseline()
        findings = compare_to_baseline(scan_sqlite_calls(Path.cwd()), baseline)
        for line in findings:
            print(line)
        if not findings:
            print(f"sqlite gateway ratchet: clean ({len(baseline)} baseline file(s) matched exactly)")
        return 1 if findings else 0

    # Legacy default: import-ban warnings under src/rebalance/ingest. Output and
    # exit code are unchanged from before the ratchet existed.
    root_dir = Path("src/rebalance/ingest")
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".py"):
                path = Path(root) / file
                errors = check_file(path)
                for err in errors:
                    print(err)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
