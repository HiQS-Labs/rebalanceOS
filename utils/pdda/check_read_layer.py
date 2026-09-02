"""Read-layer sprawl ratchets (GH-150): SQL emitters, LLM clients, day windows.

Three ratchets of the exact GH-136 ``check_banned_imports.py`` contract: scan the
tree, compare to an exact per-file baseline (``read_layer_baseline.json``), fail on
growth AND on shrink — a file that got clean must tighten the baseline via
``--update-baseline`` so the win is recorded and cannot silently regress. A same-line
``# READ-LAYER-OK: <reason>`` pragma exempts a site and puts the justification in the
diff; a pragma with an empty reason still counts (fail closed, per #126's pragma
contract). Finding identity is relative path + occurrence count; line numbers are
diagnostic only.

The ratchets freeze TODAY's sprawl at its measured count so it cannot grow while the
0.75.0 fe1 shared read layer (``db/queries.py``) is built; each surface migration
tightens R1 by one file, F2's client deletions tighten R2, and the time-helper
consolidation tightens R3. Targets per the GH-150 audit:

  R1  SQL emitters  — ``FROM``/``JOIN`` over the four github activity tables
                      outside ``src/rebalance/ingest/db/`` (the storage layer's
                      own home). Target after fe1: zero read surfaces; ingest
                      writers keep their single-writer tables via pragma.
  R2  LLM clients   — LLM endpoint literals outside the two canonical clients:
                      ``querier.py`` (Gemini synthesis primitive) and
                      ``claude_cloud.py`` (the Claude Cloud sessions SOURCE — an
                      approved collector, not a synthesis client). Measured at
                      freeze time: THREE extra Gemini implementations beyond
                      querier (note_builder, health_issue_reporter, repair) plus
                      the cc_cloud_jobs POC's Anthropic fetch — the audit
                      originally counted one of these.
  R3  day windows   — reimplementations of day-bounds/window derivation (the F3
                      family): ``def ...day_bounds/day_window`` helpers, the
                      verbatim ``timedelta(days=since_days)).strftime("%Y-%m-%d")``
                      rolling cutoff, and the naive ``datetime.now().astimezone()``
                      idiom the digest's own design notes call out as DST-blind.

Bare ``.astimezone()`` and ``date.today()`` are deliberately NOT ratcheted: both
have far too many legitimate uses for a per-file count to be meaningful signal.
The three patterns above are the audit's actual findings.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

ROOTS = ("src", "utils", "scripts")
PRUNED_DIRS = {"tests", "__pycache__", "3-eyes"}
PRUNED_PREFIXES = ("utils/pdda/",)  # the checkers themselves
SQL_GATEWAY_PREFIXES = ("src/rebalance/ingest/db/",)
GEMINI_CANONICAL = "src/rebalance/ingest/querier.py"
ANTHROPIC_CANONICAL = "src/rebalance/ingest/claude_cloud.py"
SELF_EXEMPT = "utils/pdda/check_read_layer.py"
PRAGMA_RE = re.compile(r"#\s*READ-LAYER-OK:\s*(.*)$")
BASELINE_PATH = Path(__file__).with_name("read_layer_baseline.json")

# R1: direct SQL over the four github ACTIVITY tables outside the db/ storage layer.
# (comments/repo_meta are deliberately out of scope — they pull in ingest writers
# whose single-writer table access is legitimate, drowning the signal.)
R1_SQL_RE = re.compile(r"\b(?:FROM|JOIN)\s+github_(?:activity|commits|direct_commits|items)\b")
# R2: LLM endpoint host literals. Anything matching these outside the two canonical
# clients is a synthesis/LLM HTTP implementation that must reach querier instead.
R2_GEMINI_RE = re.compile(r"generativelanguage\.googleapis\.com")
R2_ANTHROPIC_RE = re.compile(r"api\.anthropic\.com")
# R3: the F3 day-window family.
R3_DEF_BOUNDS_RE = re.compile(r"\bdef\s+_?\w*day_(?:bounds|window)\s*\(")
R3_SINCE_CUTOFF_RE = re.compile(r'timedelta\(days=since_days\)\)\.strftime\("%Y-%m-%d"\)')
R3_NAIVE_NOW_RE = re.compile(r"datetime\.now\(\)\.astimezone\(\)")


def _iter_files(root: Path):
    for top in ROOTS:
        top_dir = root / top
        if not top_dir.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(top_dir):
            dirnames[:] = [d for d in dirnames if d not in PRUNED_DIRS and not d.startswith(".")]
            for name in filenames:
                if not name.endswith(".py"):
                    continue
                file_path = Path(dirpath) / name
                rel = file_path.relative_to(root).as_posix()
                if rel == SELF_EXEMPT or rel.startswith(PRUNED_PREFIXES):
                    continue
                yield rel, file_path


def _count_pattern(content: str, pattern: re.Pattern[str]) -> int:
    found = 0
    for line in content.splitlines():
        if not pattern.search(line):
            continue
        pragma = PRAGMA_RE.search(line)
        if pragma and pragma.group(1).strip():
            continue
        found += 1
    return found


def _scan(root: Path, patterns: list[re.Pattern[str]], exempt: tuple[str, ...] = ()) -> dict[str, int]:
    counts: dict[str, int] = {}
    for rel, file_path in _iter_files(root):
        if rel in exempt or any(rel.startswith(prefix) for prefix in exempt):
            continue
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise SystemExit(f"read-layer ratchet: cannot read {rel}: {exc}") from exc
        found = sum(_count_pattern(content, p) for p in patterns)
        if found:
            counts[rel] = found
    return counts


def scan_all(root: Path) -> dict[str, dict[str, int]]:
    return {
        "sql_emitters": _scan(
            root,
            [R1_SQL_RE],
            # The db/ package is the storage layer — its own SQL is the destination
            # fe1 routes everything through, not sprawl (same shape as the GH-136
            # gateway exemption).
            exempt=SQL_GATEWAY_PREFIXES,
        ),
        "llm_clients": _scan(
            root,
            [R2_GEMINI_RE, R2_ANTHROPIC_RE],
            exempt=(GEMINI_CANONICAL, ANTHROPIC_CANONICAL),
        ),
        "day_windows": _scan(root, [R3_DEF_BOUNDS_RE, R3_SINCE_CUTOFF_RE, R3_NAIVE_NOW_RE]),
    }


def compare_to_baseline(actual: dict[str, dict[str, int]], baseline: dict[str, dict[str, int]]) -> list[str]:
    """Ratchet findings for all three sections: growth and stale-shrink both block."""
    labels = {"sql_emitters": "R1", "llm_clients": "R2", "day_windows": "R3"}
    findings: list[str] = []
    for section, tag in labels.items():
        sec_actual = actual.get(section, {})
        sec_base = baseline.get(section, {})
        for rel in sorted(sec_actual):
            if rel not in sec_base:
                findings.append(
                    f"{rel}:1: [{tag}] NEW {section} site ({sec_actual[rel]}) — route through the shared "
                    f"primitive or add a '# READ-LAYER-OK: reason' pragma (GH-150)"
                )
            elif sec_actual[rel] > sec_base[rel]:
                findings.append(f"{rel}:1: [{tag}] {section} sites grew {sec_base[rel]} -> {sec_actual[rel]} (GH-150)")
        for rel in sorted(sec_base):
            if rel not in sec_actual:
                findings.append(
                    f"{rel}:1: [{tag}] stale baseline — file is now clean; re-run with --update-baseline "
                    f"and review the diff"
                )
            elif sec_base[rel] > sec_actual[rel]:
                findings.append(
                    f"{rel}:1: [{tag}] stale baseline — sites shrank {sec_base[rel]} -> {sec_actual[rel]}; "
                    f"re-run with --update-baseline and review the diff"
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    if "--update-baseline" in argv:
        actual = scan_all(Path.cwd())
        BASELINE_PATH.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        total = sum(sum(v.values()) for v in actual.values())
        print(f"baseline updated: {total} site(s) across {sum(len(v) for v in actual.values())} file(s)")
        return 0

    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    findings = compare_to_baseline(scan_all(Path.cwd()), baseline)
    for line in findings:
        print(line)
    if not findings:
        total = sum(sum(v.values()) for v in baseline.values())
        print(f"read-layer ratchet: clean ({total} baseline site(s) matched exactly)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
