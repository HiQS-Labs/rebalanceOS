"""Structural near-duplicate canary (GH-150 C2): catches the re-typed-function class.

R1-R3 (check_read_layer.py) catch new SQL and new LLM clients. They do not catch what
F5/F6 actually were: whole functions re-typed into a second file — ``get_token`` /
``_get_token``, ``enrich_pr_status`` twice, ``upsert_block`` / ``upsert_marked_block``.
This checker fingerprints every substantial top-level function and flags any
fingerprint shared by functions in DIFFERENT files.

Fingerprint: parse with ``ast``, drop docstrings, replace every identifier
(``Name``, argument, attribute) and every constant with a placeholder, then hash the
dumped node-type structure. That makes the fingerprint invariant to renames and
literal swaps — a copy with different names still matches — while a genuinely
different function does not.

Ratchet contract (same as GH-136 / check_read_layer): findings are compared against an
exact baseline (``near_duplicates_baseline.json``); a NEW shared fingerprint fails, and
a baseline pair that no longer matches also fails until ``--update-baseline`` records
the deletion — so removing e.g. the cc_cloud_jobs POC shrinks the baseline visibly.

Known limit (stated in the GH-150 plan): this catches copies and light edits, not a
from-scratch rewrite of the same idea. That gap is covered by the consumer-catalog
canary — a rewrite still has to file a catalog row declaring what it reads and what it
replaces.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

# Substantial functions only: below this node count, structural similarity is noise.
MIN_NODES = 25
# utils/py is the standalone releases-ledger app (stdlib-only by design), utils/pdda
# is the checker suite itself, 3-eyes is stood down (AGENTS.md).
ROOTS = ("src/rebalance", "utils", "scripts")
PRUNED_DIRS = {"tests", "__pycache__", "3-eyes"}
PRUNED_PREFIXES = ("utils/pdda/", "utils/py/")
SELF_EXEMPT = "utils/pdda/check_near_duplicates.py"
BASELINE_PATH = Path(__file__).with_name("near_duplicates_baseline.json")


class _Normalize(ast.NodeTransformer):
    """Replace identifiers and constants so renames do not defeat the fingerprint."""

    def visit_Name(self, node: ast.Name) -> ast.Name:
        self.generic_visit(node)
        node.id = "n"
        return node

    def visit_arg(self, node: ast.arg) -> ast.arg:
        self.generic_visit(node)
        node.arg = "a"
        return node

    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        self.generic_visit(node)
        node.attr = "x"
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        node.value = None
        return node

    def _drop_docstring(self, node: ast.AST) -> ast.AST:
        if (
            node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body = node.body[1:]
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        self.generic_visit(node)
        node.name = "fn"  # the def NAME is an identifier too — renames must not defeat the hash
        return self._drop_docstring(node)  # type: ignore[arg-type]

    visit_AsyncFunctionDef = visit_FunctionDef


def fingerprint(node: ast.FunctionDef) -> str:
    normalized = _Normalize().visit(node)
    ast.fix_missing_locations(normalized)
    dumped = ast.dump(normalized, annotate_fields=False, include_attributes=False)
    return hashlib.sha256(dumped.encode("utf-8")).hexdigest()[:16]


def scan_functions(root: Path) -> dict[str, list[str]]:
    """``fingerprint -> ["path:function", ...]`` for substantial top-level functions."""
    by_fp: dict[str, list[str]] = {}
    for top in ROOTS:
        top_dir = root / top
        if not top_dir.is_dir():
            continue
        for path in sorted(top_dir.rglob("*.py")):
            rel = path.relative_to(root).as_posix()
            if rel == SELF_EXEMPT or rel.startswith(PRUNED_PREFIXES):
                continue
            if any(part in PRUNED_DIRS for part in path.relative_to(root).parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
            except (OSError, SyntaxError):
                continue
            for node in tree.body:  # top-level only: methods belong to their class's design
                if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and len(list(ast.walk(node))) >= MIN_NODES:
                    # Record the name BEFORE fingerprinting — fingerprint() normalizes
                    # the node in place (including its name), and setdefault evaluates
                    # its key argument first, so node.name must be captured up front.
                    fn_name = node.name
                    by_fp.setdefault(fingerprint(node), []).append(f"{rel}:{fn_name}")
    return by_fp


def findings_from(by_fp: dict[str, list[str]]) -> list[str]:
    """One finding per fingerprint shared across different files, sorted for stability."""
    out: list[str] = []
    for members in by_fp.values():
        if len(members) < 2:
            continue
        if len({m.rsplit(":", 1)[0] for m in members}) < 2:
            continue  # same file (e.g. genuine overloads) — not cross-file sprawl
        out.append(" ~ ".join(sorted(members)))
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if "--update-baseline" in argv:
        actual = findings_from(scan_functions(Path.cwd()))
        BASELINE_PATH.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"baseline updated: {len(actual)} cross-file duplicate pair(s)")
        return 0

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    actual = findings_from(scan_functions(Path.cwd()))
    problems: list[str] = []
    for item in actual:
        if item not in baseline:
            problems.append(f"{item}: NEW structural near-duplicate — reuse the existing function (GH-150)")
    for item in baseline:
        if item not in actual:
            problems.append(f"{item}: stale baseline — duplicate resolved; re-run with --update-baseline")
    for line in problems:
        print(line)
    if not problems:
        print(f"near-duplicate canary: clean ({len(baseline)} baseline pair(s) matched exactly)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
