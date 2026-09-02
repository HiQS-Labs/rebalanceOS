#!/usr/bin/env python3
"""GH-144 Phase 0 — aggregate the S1 primitive and check D2 (exact-once union).

Reads runs.jsonl + inventory/*.jsonl outcome maps, prints:
  - per-cell wall-time median/min/max and result counts (S1)
  - D2 executed-inventory comparisons per candidate vs C0 (node-level)

D2 rule (protocol §7.3): the exact-once multiset union of executed nodeids
across a candidate's required lanes == the incumbent's executed set for that
suite+python, with identical outcome classes.
"""
from __future__ import annotations

import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

CAMP = Path(__file__).resolve().parents[1]
REPO = CAMP.parents[1]


def load_runs() -> list[dict]:
    return [json.loads(l) for l in (CAMP / "runs.jsonl").read_text().splitlines() if l.strip()]


def med_min_max(xs: list[float]) -> str:
    if not xs:
        return "-"
    if len(xs) == 1:
        return f"{xs[0]:.1f}"
    return f"{statistics.median(xs):.1f} [{min(xs):.1f}-{max(xs):.1f}]"


def summary_table(runs: list[dict]) -> None:
    print("== S1 per-cell summary (wall_s median [min-max]; n) ==")
    cells = defaultdict(list)
    for r in runs:
        if "wall_s" in r:
            cells[(r["cell"], r["candidate"], r.get("lane", ""), r["python"])].append(r)
    for key in sorted(cells):
        recs = cells[key]
        walls = [r["wall_s"] for r in recs]
        counts = recs[-1].get("counts") or {}
        cstr = " ".join(f"{k}={v}" for k, v in sorted(counts.items()) if v)
        rc = {r["run_index"]: r["exit_code"] for r in recs}
        print(f"{key[0]:>4} {key[1]:<8} {key[2]:<14} py{key[3]} n={len(recs)} "
              f"wall={med_min_max(walls)} rc={sorted(set(rc.values()))} {cstr}")


def load_outcomes(cell: str, kind: str, suite: str, py: str) -> dict[str, str]:
    p = CAMP / "inventory" / f"outcomes-{cell}-{kind}-{suite}-py{py}.jsonl"
    if not p.exists():
        return {}
    return {json.loads(l)["nodeid"]: json.loads(l)["outcome"] for l in p.read_text().splitlines() if l.strip()}


def flips(a: dict[str, str], b: dict[str, str]) -> list[str]:
    return sorted(n for n in set(a) & set(b) if a[n] != b[n])


def d2_checks() -> None:
    print("\n== D2 executed-inventory checks (node-level vs C0) ==")
    for py in ("3.12", "3.13"):
        base_root = load_outcomes("M4", "c0", "tests", py)
        base_hiqs = load_outcomes("M5", "c0", "hiqs", py)
        if not base_root:
            print(f"py{py}: base root outcomes missing; skip")
            continue
        # C2: root lane without HiQS installed
        m4b = load_outcomes("M4b", "c2root", "tests", py)
        if m4b:
            print(f"py{py} C2-root: base={len(base_root)} lane={len(m4b)} "
                  f"missing={len(set(base_root)-set(m4b))} added={len(set(m4b)-set(base_root))} "
                  f"flips={len(flips(base_root, m4b))}")
        # C4: xdist
        for cell, label in (("M8", "n2"), ("M9", "n4")):
            mx = load_outcomes(cell, "c4", "tests", py)
            if mx:
                print(f"py{py} C4-{label}: base={len(base_root)} lane={len(mx)} "
                      f"missing={len(set(base_root)-set(mx))} added={len(set(mx)-set(base_root))} "
                      f"flips={len(flips(base_root, mx))}")
        # C2: HiQS lane
        m6 = load_outcomes("M6", "c2hiqs", "hiqs", py)
        if base_hiqs and m6:
            print(f"py{py} C2-hiqs: base={len(base_hiqs)} lane={len(m6)} "
                  f"missing={len(set(base_hiqs)-set(m6))} added={len(set(m6)-set(base_hiqs))} "
                  f"flips={len(flips(base_hiqs, m6))}")
        # C3: root-without-embeddings vs base (differences = the seam requirement set)
        m7 = load_outcomes("M7", "c3", "tests", py)
        if m7:
            sfiles, delta = seam_files(py)
            diff = sorted(set(base_root) ^ set(m7))
            bad = [n for n in diff if n.rsplit("::", 1)[0] not in sfiles]
            print(f"py{py} C3-probe: base={len(base_root)} lane={len(m7)} "
                  f"delta-nodes={len(delta)} seam-files={len(sfiles)} "
                  f"flips={len(flips(base_root, m7))} outside-seam={len(bad)}")
            for f in sfiles:
                print(f"    seam: {f}")
            if bad:
                print("  outside-seam nodes (first 10):")
                for n in bad[:10]:
                    print(f"    {n}")
        # C3 union: remaining-root + seam lane == base, exact-once
        m7b = load_outcomes("M7b", "c0", "seam", py)
        if m7 and m7b:
            seamset = {n for n in m7b}
            union: dict[str, str] = {}
            dup = []
            for n, o in m7.items():
                if n in seamset:
                    continue
                union[n] = o
            for n, o in m7b.items():
                if n in union:
                    dup.append(n)
                union[n] = o
            print(f"py{py} C3-union: union={len(union)} base={len(base_root)} "
                  f"missing={len(set(base_root)-set(union))} added={len(set(union)-set(base_root))} "
                  f"dups={len(dup)} flips={len(flips(base_root, union))}")


def seam_files(py: str) -> tuple[list[str], list[str]]:
    """Files whose tests depend on the embeddings extra — derived from the M7
    outcome map: any node whose outcome differs from the C0 base (failed /
    error / skip-flip / missing) marks its file as seam. Returns (files,
    delta_nodes)."""
    m7 = load_outcomes("M7", "c3", "tests", py)
    base = load_outcomes("M4", "c0", "tests", py)
    delta = [n for n, o in m7.items() if base.get(n) != o]
    files = sorted({n.rsplit("::", 1)[0] for n in delta})
    return files, delta


def main() -> None:
    runs = load_runs()
    summary_table(runs)
    d2_checks()


if __name__ == "__main__":
    sys.exit(main())
