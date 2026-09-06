"""Banned-import and SQLite gateway exact-baseline ratchets.

One file, two checks (GH-126's "choose one owner" rule forbids a second validator):

1. Import ratchet (GH-126, blocking via ``--check``): direct
   ``subprocess``/``datetime`` imports under ``src/rebalance/ingest`` outside
   ``rebalance.lib``. The exact baseline is keyed by relative path, import family,
   and occurrence count; line numbers remain diagnostic only. A same-line
   ``# CANONICAL-PATH-OK: <reason>`` pragma exempts a reviewed import.
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
SQLITE_PRAGMA_RE = re.compile(r"#\s*GATEWAY-OK:\s*(.*)$")
SQLITE_ROOTS = ("src", "utils", "HiQS")
SQLITE_GATEWAY_DIRS = ("src/rebalance/ingest/db", "HiQS/hiqs")
SQLITE_SELF_EXEMPT = ("utils/pdda/check_banned_imports.py",)
SQLITE_PRUNED_DIRS = {"tests", "__pycache__"}
SQLITE_BASELINE_PATH = Path(__file__).with_name("sqlite_connect_baseline.json")

BANNED_IMPORT_ROOT = "src/rebalance/ingest"
BANNED_IMPORT_FAMILIES = ("datetime", "subprocess")
BANNED_IMPORT_PRAGMA_RE = re.compile(r"#\s*CANONICAL-PATH-OK:\s*(.*)$")
BANNED_IMPORT_BASELINE_PATH = Path(__file__).with_name("banned_imports_baseline.json")


def _read_python(path: Path, *, ratchet: str) -> tuple[str, ast.AST]:
    """Read and parse a Python source file, failing closed for a ratchet scan."""
    try:
        content = path.read_text(encoding="utf-8")
        return content, ast.parse(content, filename=str(path))
    except (OSError, UnicodeError, SyntaxError, ValueError) as exc:
        raise SystemExit(f"{ratchet}: cannot parse {path}: {exc}") from exc


def scan_banned_imports(root: Path) -> dict[str, dict[str, int]]:
    """Count direct datetime/subprocess imports by path and family.

    The relative path + family + count shape deliberately excludes line numbers, so
    moving a debt site does not alter the baseline. Read and AST failures are
    failures, rather than silently making the recorded debt look smaller.
    """
    counts: dict[str, dict[str, int]] = {}
    scan_root = root / BANNED_IMPORT_ROOT
    if not scan_root.exists():
        return counts

    for dirpath, dirnames, filenames in os.walk(scan_root):
        dirnames[:] = [d for d in dirnames if d not in SQLITE_PRUNED_DIRS and not d.startswith(".")]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            file_path = Path(dirpath) / name
            rel = file_path.relative_to(root).as_posix()
            if rel.startswith("src/rebalance/lib/"):
                continue
            content, tree = _read_python(file_path, ratchet="banned-import ratchet")
            lines = content.splitlines()
            per_family: dict[str, int] = {}
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                line = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                pragma = BANNED_IMPORT_PRAGMA_RE.search(line)
                if pragma and pragma.group(1).strip():
                    continue
                if isinstance(node, ast.Import):
                    families = (alias.name for alias in node.names)
                else:
                    families = (node.module,)
                for family in families:
                    if family in BANNED_IMPORT_FAMILIES:
                        per_family[family] = per_family.get(family, 0) + 1
            if per_family:
                counts[rel] = dict(sorted(per_family.items()))
    return dict(sorted(counts.items()))


def find_banned_import_errors(root: Path) -> list[str]:
    """Return diagnostic warnings for the legacy no-argument command."""
    errors: list[str] = []
    scan_root = root / BANNED_IMPORT_ROOT
    if not scan_root.exists():
        return errors

    for dirpath, dirnames, filenames in os.walk(scan_root):
        dirnames[:] = [d for d in dirnames if d not in SQLITE_PRUNED_DIRS and not d.startswith(".")]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            file_path = Path(dirpath) / name
            rel = file_path.relative_to(root).as_posix()
            if rel.startswith("src/rebalance/lib/"):
                continue
            content, tree = _read_python(file_path, ratchet="banned-import ratchet")
            lines = content.splitlines()
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                line = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                pragma = BANNED_IMPORT_PRAGMA_RE.search(line)
                if pragma and pragma.group(1).strip():
                    continue
                if isinstance(node, ast.Import):
                    families = (alias.name for alias in node.names)
                    message = "Banned import '{family}'. Use rebalance.lib instead."
                else:
                    families = (node.module,)
                    message = "Banned import from '{family}'. Use rebalance.lib instead."
                for family in families:
                    if family in BANNED_IMPORT_FAMILIES:
                        errors.append(f"{rel}:{node.lineno}: {message.format(family=family)}")
    return errors


def scan_sqlite_calls(root: Path) -> dict[str, int]:
    """Count direct SQLite connection call sites per file under the scanned roots.

    Tests directories, hidden/build directories, the two gateway directories, and this
    checker itself are exempt. A same-line ``# GATEWAY-OK: <reason>`` pragma exempts a
    reviewed call site; a pragma with an empty reason still counts (fail closed, per
    the pragma contract #126 specifies). Raises ``SystemExit`` on unreadable files
    rather than returning a silently incomplete result.
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
                found = 0
                for line in content.splitlines():
                    if not SQLITE_CALL_RE.search(line):
                        continue
                    pragma = SQLITE_PRAGMA_RE.search(line)
                    if pragma and pragma.group(1).strip():
                        continue
                    found += 1
                if found:
                    counts[rel] = found
    return counts


def load_baseline(path: Path = SQLITE_BASELINE_PATH) -> dict[str, int]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_banned_imports_baseline(path: Path = BANNED_IMPORT_BASELINE_PATH) -> dict[str, dict[str, int]]:
    """Load the path + import-family exact baseline, failing closed if malformed."""
    try:
        baseline = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SystemExit(f"banned-import ratchet: cannot load baseline {path}: {exc}") from exc
    if not isinstance(baseline, dict) or any(
        not isinstance(rel, str)
        or not isinstance(families, dict)
        or not families
        or any(
            family not in BANNED_IMPORT_FAMILIES or type(count) is not int or count < 1
            for family, count in families.items()
        )
        for rel, families in baseline.items()
    ):
        raise SystemExit(f"banned-import ratchet: invalid baseline shape in {path}")
    return baseline


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


def compare_banned_imports_to_baseline(
    actual: dict[str, dict[str, int]], baseline: dict[str, dict[str, int]]
) -> list[str]:
    """Return exact-baseline violations for every path/import-family identity."""
    findings: list[str] = []
    for rel in sorted(set(actual) | set(baseline)):
        actual_families = actual.get(rel, {})
        baseline_families = baseline.get(rel, {})
        for family in sorted(set(actual_families) | set(baseline_families)):
            actual_count = actual_families.get(family, 0)
            baseline_count = baseline_families.get(family, 0)
            label = f"{family} import"
            if not baseline_count:
                findings.append(
                    f"{rel}:1: NEW {label} debt ({actual_count} site(s)) — use rebalance.lib or add a reasoned CANONICAL-PATH-OK pragma"
                )
            elif not actual_count:
                findings.append(
                    f"{rel}:1: stale baseline — {label} debt is now clean; re-run with --update-baseline and review the diff"
                )
            elif actual_count > baseline_count:
                findings.append(
                    f"{rel}:1: {label} debt grew {baseline_count} -> {actual_count} — use rebalance.lib or add a reasoned CANONICAL-PATH-OK pragma"
                )
            elif actual_count < baseline_count:
                findings.append(
                    f"{rel}:1: stale baseline — {label} debt shrank {baseline_count} -> {actual_count}; re-run with --update-baseline and review the diff"
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if "--update-baseline" in argv:
        root = Path.cwd()
        sqlite_actual = scan_sqlite_calls(root)
        imports_actual = scan_banned_imports(root)
        SQLITE_BASELINE_PATH.write_text(json.dumps(sqlite_actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        BANNED_IMPORT_BASELINE_PATH.write_text(
            json.dumps(imports_actual, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(f"sqlite baseline updated: {len(sqlite_actual)} file(s), {sum(sqlite_actual.values())} site(s)")
        print(
            "banned-import baseline updated: "
            f"{len(imports_actual)} file(s), {sum(sum(families.values()) for families in imports_actual.values())} site(s)"
        )
        return 0

    if "--check" in argv:
        root = Path.cwd()
        sqlite_baseline = load_baseline()
        imports_baseline = load_banned_imports_baseline()
        findings = compare_to_baseline(scan_sqlite_calls(root), sqlite_baseline)
        findings.extend(compare_banned_imports_to_baseline(scan_banned_imports(root), imports_baseline))
        for line in findings:
            print(line)
        if not findings:
            print(f"sqlite gateway ratchet: clean ({len(sqlite_baseline)} baseline file(s) matched exactly)")
            print(f"banned-import ratchet: clean ({len(imports_baseline)} baseline file(s) matched exactly)")
        return 1 if findings else 0

    # Legacy default: import-ban warnings under src/rebalance/ingest. Output and
    # exit code are unchanged from before the ratchet existed.
    for error in find_banned_import_errors(Path.cwd()):
        print(error)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
