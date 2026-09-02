#!/usr/bin/env python3
"""GH-144 Phase 0 — regenerate outcome maps from retained junit XMLs.

The first parse_junit (as run for cells completed before 2026-09-01 evening)
mangled class-based nodeids (junit omits the file attr; the fallback derived
`module/Class.py::test` instead of `module.py::Class::test`). Counts were
unaffected and comparisons were internally consistent, but the maps were not
comparable with the --collect-only node lists. This regenerates every
inventory/outcomes-*.jsonl deterministically from the SAME junit files whose
sha256 is recorded in runs.jsonl — the audit chain is junit -> this script ->
map. Run once after the driver finishes.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_s1 import parse_junit  # noqa: E402 — fixed reconstruction

CAMP = Path(__file__).resolve().parents[1]
ARTIFACTS = CAMP.parents[1] / "temp" / "gh144" / "artifacts"
INVENT = CAMP / "inventory"

PAT = re.compile(r"junit-([A-Za-z0-9]+)-(c0|c2root|c2hiqs|c3|c4)-(tests|hiqs|seam)-py(3\.1[23])-r(\d)\.xml")


def main() -> None:
    n = 0
    unmatched = []
    for xml in sorted(ARTIFACTS.glob("junit-*.xml")):
        m = PAT.match(xml.name)
        if not m:
            unmatched.append(xml.name)
            continue
        cell, kind, suite, py, run = m.groups()
        parsed = parse_junit(xml)
        omap = INVENT / f"outcomes-{cell}-{kind}-{suite}-py{py}.jsonl"
        with open(omap, "w") as f:
            for nid, o in sorted(parsed["outcomes"].items()):
                f.write(json.dumps({"nodeid": nid, "outcome": o}, sort_keys=True) + "\n")
        n += 1
        print(f"{xml.name} -> {omap.name} ({len(parsed['outcomes'])} nodes)")
    # A junit file this script cannot map is an audit-chain break, not a skip:
    # the "regenerated every map" claim is only true if nothing fell through.
    if unmatched:
        raise SystemExit(f"UNMATCHED junit files (pattern cannot parse them): {unmatched}")
    print(f"regenerated {n} maps")


if __name__ == "__main__":
    main()
