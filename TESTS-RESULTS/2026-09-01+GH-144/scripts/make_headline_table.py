#!/usr/bin/env python3
"""GH-144 Phase 0 — regenerate SUMMARY.md's D1 headline table from
ci-job-timings.jsonl, so the decision numbers cannot drift from the primitive.

Critical path per candidate = max(job wall) over the candidate's required
jobs, per Python, medians of the M11 samples. Cuts are vs the c0 medians.
"""

from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

CAMP = Path(__file__).resolve().parents[1]

# candidate -> job-name templates it makes required (per Python)
LANES = {
    "C0": ["c0-incumbent ({py})"],
    "C1": ["c1-cache ({py})"],
    "C2": ["c2-root ({py})", "c2-hiqs ({py})"],
    "C3": ["c3-root-noembed ({py})", "c3-embed-seam ({py})", "c2-hiqs ({py})"],
    "C4": ["c4-xdist ({py}, 4)", "c2-hiqs ({py})"],
}


def python_of(job_name: str) -> str:
    """M11 records identify Python only inside the job name's parenthetical —
    'c0-incumbent (3.12)', 'c4-xdist (3.13, 4)'. Published records are never
    rewritten, so derive it here instead."""
    inner = job_name[job_name.rfind("(") + 1 : job_name.rfind(")")]
    return inner.split(",")[0].strip()


def main() -> None:
    recs = [json.loads(line) for line in (CAMP / "ci-job-timings.jsonl").read_text().splitlines() if '"M11"' in line]
    med: dict[tuple[str, str], float] = {}
    samples: dict[tuple[str, str], list[float]] = defaultdict(list)
    for r in recs:
        samples[(python_of(r["job_name"]), r["job_name"])].append(r["wall_s"])
    for k, ws in samples.items():
        med[k] = statistics.median(ws)

    base = {py: med[(py, f"c0-incumbent ({py})")] for py in ("3.12", "3.13")}
    print("| Candidate | CP 3.12 | CP 3.13 | Cut 3.12 | Cut 3.13 |")
    print("|---|---|---|---|---|")
    for cand, templates in LANES.items():
        cps = {}
        for py in ("3.12", "3.13"):
            walls = [med[(py, t.format(py=py))] for t in templates]
            cps[py] = max(walls)
        c12 = (base["3.12"] - cps["3.12"]) / base["3.12"] * 100
        c13 = (base["3.13"] - cps["3.13"]) / base["3.13"] * 100
        print(f"| {cand} | {cps['3.12']:.0f} s | {cps['3.13']:.0f} s | {c12:.1f} % | {c13:.1f} % |")
    print(f"\n(base medians: 3.12={base['3.12']:.0f}s, 3.13={base['3.13']:.0f}s; n=3 samples per job, S2 same-SHA)")


if __name__ == "__main__":
    sys.exit(main())
