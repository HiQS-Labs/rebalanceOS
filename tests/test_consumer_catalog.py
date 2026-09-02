"""GH-150 C1: the consumer-catalog canary.

Every surface that reads the activity signal — script entrypoint, scheduled-job
script, MCP tool — must have a row in ARCHITECTURE.md's "Source → Consumer fanout"
table. A new report script with no row fails with `uncataloged consumer`, which is
the review-visible place where "own SQL" / "own Gemini client" / "replaces X" must
be declared. The ratchets in utils/pdda/check_read_layer.py catch new SQL and new
LLM clients mechanically; this test catches the script that imports everything
correctly and was never needed at all.

Column rules enforced here (target-state semantics, baseline-linked today):
  * LLM primitive is `querier`, `none`, or `own (R2-baseline: <path>)` — a private
    client may only exist by naming the ratchet baseline that shrinks when it dies.
  * An Input path containing "own SQL" must name its `R1-baseline:` file the same way.
  * Replaces is `—` or the name of an existing Surface in the table.
When fe1's shared read layer (db/queries.py) exists, new rows must read it and the
baseline references become violations — the catalog and the ratchets tighten together.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCH_PATH = REPO_ROOT / "ARCHITECTURE.md"
SECTION_HEADER = "### Source → Consumer fanout"
# "utils/3-eyes" (no trailing slash) also catches utils/3-eyes-session-log.py — the
# stood-down sentinel's session logger is not a consumer surface (AGENTS.md defers it).
ENTRYPOINT_PRUNE_PREFIXES = ("utils/pdda/", "utils/3-eyes", "utils/py/", "scripts/lib/")
MCP_TOOLS_DIR = REPO_ROOT / "src/rebalance/mcp/tools"


def _catalog_rows() -> list[dict[str, str]]:
    text = ARCH_PATH.read_text(encoding="utf-8")
    start = text.index(SECTION_HEADER)
    end = text.index("\n### ", start + len(SECTION_HEADER))
    section = text[start:end]
    rows = []
    for line in section.splitlines():
        if not line.startswith("|") or line.startswith("|---") or set(line.strip()) <= {"|", "-", " "}:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[0] not in ("Surface",):
            rows.append(
                {
                    "surface": cells[0],
                    "entrypoints": cells[1],
                    "cadence": cells[2],
                    "input": cells[3],
                    "llm": cells[4],
                    "channel": cells[5],
                    "replaces": cells[6],
                }
            )
    assert rows, "consumer catalog table missing or unparseable"
    return rows


def _row_entry_paths(row: dict[str, str]) -> set[str]:
    return {m.group(0) for m in re.finditer(r"[\w./-]+\.(?:py|sh)", row["entrypoints"])}


def _script_entrypoints() -> set[str]:
    out: set[str] = set()
    for base in ("utils", "scripts"):
        for path in (REPO_ROOT / base).rglob("*.py"):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if rel.startswith(ENTRYPOINT_PRUNE_PREFIXES):
                continue
            if any(part in {"3-eyes", "__pycache__", "pdda"} for part in path.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, SyntaxError):
                continue
            if any(
                isinstance(n, ast.If)
                and isinstance(n.test, ast.Compare)
                and isinstance(n.test.left, ast.Name)
                and n.test.left.id == "__name__"
                for n in ast.walk(tree)
            ):
                out.add(rel)
    return out


def _mcp_tools() -> set[str]:
    """Module paths that expose at least one @mcp.tool() (grouped-row granularity)."""
    modules: set[str] = set()
    for path in sorted(MCP_TOOLS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for dec in node.decorator_list:
                target = dec.func if isinstance(dec, ast.Call) else dec
                if isinstance(target, ast.Attribute) and target.attr == "tool":
                    modules.add(path.relative_to(REPO_ROOT).as_posix())
    return modules


def _scheduler_job_scripts() -> set[str]:
    """Repo-relative script paths named in SCHEDULER.md's policy table."""
    text = (REPO_ROOT / "SCHEDULER.md").read_text(encoding="utf-8")
    out: set[str] = set()
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Job"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                break
            for m in re.finditer(r"[\w./-]+\.(?:py|sh)", line):
                rel = m.group(0)
                if (REPO_ROOT / rel).exists() and not rel.startswith(("scripts/lib/",)):
                    out.add(rel)
    return out


def test_consumer_catalog_covers_every_entrypoint() -> None:
    catalog_paths = {p for row in _catalog_rows() for p in _row_entry_paths(row)}
    missing = sorted(_script_entrypoints() - catalog_paths)
    assert not missing, (
        f"uncataloged consumer: {missing} — add a row to ARCHITECTURE.md {SECTION_HEADER} or delete the script"
    )


def test_consumer_catalog_covers_every_mcp_tool_module() -> None:
    catalog_paths = {p for row in _catalog_rows() for p in _row_entry_paths(row)}
    missing = sorted(_mcp_tools() - catalog_paths)
    assert not missing, (
        f"uncataloged MCP tool module: {missing} — add a row (tool granularity: one row or a grouped row naming the module)"
    )


def test_consumer_catalog_covers_every_scheduled_job_script() -> None:
    catalog_paths = {p for row in _catalog_rows() for p in _row_entry_paths(row)}
    missing = sorted(_scheduler_job_scripts() - catalog_paths)
    assert not missing, f"uncataloged scheduled job script: {missing} — add a row or repoint the job"


def test_catalog_column_rules() -> None:
    rows = _catalog_rows()
    surfaces = {row["surface"] for row in rows}
    llm_ok = re.compile(r"^(querier|none|own \(R2-baseline: [\w./-]+\.(?:py|sh)\))$")
    problems: list[str] = []
    for row in rows:
        if not llm_ok.match(row["llm"]):
            problems.append(
                f"{row['surface']}: LLM primitive must be querier, none, or own (R2-baseline: <path>) — got {row['llm']!r}"
            )
        if "own SQL" in row["input"] and "R1-baseline:" not in row["input"]:
            problems.append(f"{row['surface']}: Input path claims 'own SQL' without naming its R1-baseline file")
        if not row["input"].strip():
            problems.append(f"{row['surface']}: Input path is empty")
        if row["replaces"] != "—" and row["replaces"] not in surfaces:
            problems.append(f"{row['surface']}: Replaces names unknown surface {row['replaces']!r}")
    assert not problems, ";\n".join(problems)


def test_catalog_replaces_cycle_is_acyclic() -> None:
    """A replacement chain that loops (A replaces B replaces A) is a catalog bug."""
    rows = {row["surface"]: row["replaces"] for row in _catalog_rows()}
    for surface in rows:
        seen: set[str] = set()
        current = surface
        while current in rows and rows[current] != "—":
            if current in seen:
                pytest.fail(f"replacement cycle at {surface}")
            seen.add(current)
            current = rows[current]
