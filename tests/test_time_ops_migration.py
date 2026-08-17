"""GH-5 Phase R (old-repo #304) — all clock reads go through the shared time library.

The old repo's campaign (GH-292) built ``now_iso()``/``now_utc()`` with a
test-time freeze seam; adoption was stranded in an unmerged PR while raw
``datetime.now(timezone.utc)`` sites kept accumulating here (109 measured at
port time). This guard is the regression control the migration ships with —
red before the migration, and a new raw site fails it loudly instead of
silently widening the unfrozen surface.

Deliberately NOT scanned: ``HiQS/`` and ``utils/3-eyes/`` (plus its launchd
shim ``utils/3-eyes-session-log.py``). Both are standalone packages under the
"duplicate, don't import" rule — routing their clocks through
``rebalance.lib`` would be exactly the coupling ``HiQS/tests/test_clean_room.py``
exists to prevent. Their raw sites are a deliberate exemption, not a miss.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# The implementation itself is the one legitimate home of the raw calls.
EXEMPT = {REPO_ROOT / "src" / "rebalance" / "lib" / "time_ops.py"}

RAW_CLOCK = re.compile(r"datetime\.now\(timezone\.utc\)|datetime\.utcnow\(")


def _scan_tree(root: Path) -> list[str]:
    hits: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path in EXEMPT or "__pycache__" in path.parts:
            continue
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if RAW_CLOCK.search(line) and "# raw-ok" not in line:
                hits.append(f"{path.relative_to(REPO_ROOT)}:{lineno}: {line.strip()}")
    return hits


def test_product_trees_have_no_raw_clock_reads():
    hits = _scan_tree(REPO_ROOT / "src" / "rebalance") + [
        h
        for h in _scan_tree(REPO_ROOT / "scripts")
    ]
    assert hits == [], (
        "raw clock reads found — use rebalance.lib.time_ops.now_utc()/now_iso() "
        "(or mark a deliberate exception with `# raw-ok`):\n" + "\n".join(hits)
    )


def test_the_scan_itself_sees_files():
    """Scan-nothing must not read as found-nothing (same LOUD-failure posture
    as HiQS/tests/test_clean_room.py)."""
    src_files = list((REPO_ROOT / "src" / "rebalance").rglob("*.py"))
    assert len(src_files) > 50, f"scanned suspiciously few sources: {len(src_files)}"


def test_time_ops_itself_is_exempt():
    # time_ops spells its real clock read `datetime.now(tz or timezone.utc)`,
    # so it would pass the RAW_CLOCK scan anyway — the exemption documents
    # intent. Assert it still holds an actual datetime.now call at all.
    time_ops = REPO_ROOT / "src" / "rebalance" / "lib" / "time_ops.py"
    assert "datetime.now(" in time_ops.read_text(encoding="utf-8"), (
        "time_ops.py no longer contains the real clock call — this guard's "
        "exemption list is stale"
    )
