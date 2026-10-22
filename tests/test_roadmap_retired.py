"""GH-348: ROADMAP.md is retired; releases.db is the only work ledger.

Mirrors XYZ Forge's GH-269 invariants. Read-only: every command here only reads the ledger
(`roadmap sync` is a no-op in releases mode, which is exactly what is asserted).
"""

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APP = REPO / "utils" / "py" / "releases_app.py"
MARKER = re.compile(r"^\s*ROADMAP_SOURCE\s*=\s*releases\s*(#.*)?$", re.M)


def _app(*args):
    return subprocess.run(
        [sys.executable, str(APP), "--root", str(REPO), *args],
        cwd=REPO, capture_output=True, text=True, timeout=120,
    )


def test_roadmap_md_is_absent_and_marker_is_set():
    assert not (REPO / "ROADMAP.md").exists(), "ROADMAP.md is retired (GH-348); park work with `roadmap add`"
    mode = (REPO / ".pdda-mode").read_text()
    assert MARKER.search(mode), ".pdda-mode must carry ROADMAP_SOURCE=releases"
    first = next(ln.strip() for ln in mode.splitlines() if ln.strip() and not ln.lstrip().startswith("#"))
    assert first in {"observe", "light", "full"}, "the PDDA mode must stay the first non-comment line"


def test_roadmap_sync_is_a_no_op_in_releases_mode():
    r = _app("roadmap", "sync")
    assert r.returncode == 0, r.stderr
    assert "skipped — releases-mode repo" in r.stdout


def test_roadmap_list_reads_the_db():
    r = _app("roadmap", "list")
    assert r.returncode == 0, r.stderr
    rows = [ln for ln in r.stdout.splitlines() if ln.startswith("rmi-")]
    assert len(rows) >= 147, "the final GH-348 import had 147 rows"
    sections = {"In progress", "Queue / parked intake", "Completed"}
    assert all(any(s in ln for ln in rows) for s in sections)


def test_roadmap_coverage_reads_the_db_not_the_file():
    r = subprocess.run(
        ["bash", str(REPO / "utils" / "pdda" / "pdda.sh"), "roadmap-coverage"],
        cwd=REPO, capture_output=True, text=True, timeout=120, env={"PDDA_MODE": "full", "PATH": "/usr/bin:/bin"},
    )
    out = r.stdout + r.stderr
    assert "SUMMARY [pdda-check-roadmap-coverage]" in out
    assert "no readable releases.db ledger" not in out
    assert "ROADMAP.md not found" not in out
    # A doc parked only in the DB must count as covered (red control: drop its row and this fails).
    assert "GH-348-RETIRE-ROADMAP-MD.md" not in out
