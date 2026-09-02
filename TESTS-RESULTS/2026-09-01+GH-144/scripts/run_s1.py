#!/usr/bin/env python3
"""GH-144 Phase 0 S1 runner — local macOS structure/feasibility measurements.

Implements cells M1-M9 of PROJECT/2-WORKING/GH-144-CI-LANE-PROTOCOL.md (v1.1).
Writes one JSONL record per measurement to runs.jsonl; console output per run
to console/; fail-closed inventory node lists + per-node outcome maps to
inventory/. Timing evidence only — D1 decisions ride on S2 (CI spike), not here.

Usage (from the repo root of the campaign clone):
  python3 TESTS-RESULTS/2026-09-01+GH-144/scripts/run_s1.py <subcommand> ...
Subcommands:
  setup   --py 3.12 --kind c0|c2root|c2hiqs|c3|c4 --mode cold|warm --run N
  collect --py 3.12 --kind c0 --suite tests|hiqs --run N
  suite   --py 3.12 --kind c0 --suite tests|hiqs --cell M4 --run N [--pytest-args ...]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]  # repo root (script lives in TESTS-RESULTS/<campaign>/scripts)
CAMPAIGN = Path(__file__).resolve().parents[1]
CAMP = CAMPAIGN.name
RUNS = CAMPAIGN / "runs.jsonl"
CONSOLE = CAMPAIGN / "console"
INVENT = CAMPAIGN / "inventory"
VENV_ROOT = REPO / "temp" / "gh144" / "venvs"
ARTIFACTS = REPO / "temp" / "gh144" / "artifacts"
COMMIT = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True, text=True).stdout.strip()
SCHEMA = 1


def steps_for(kind: str, mode: str, venv_python: str) -> list[list[str]]:
    """Install argv per candidate kind. Each entry is one timed step."""
    p = nocache(mode)
    if kind == "c0":
        return [
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"] + p,
            [venv_python, "-m", "pip", "install"] + p + ["torch"],
            [venv_python, "-m", "pip", "install"] + p + ["-e", ".[calendar,server,embeddings]", "pytest"],
            [venv_python, "-m", "pip", "install"] + p + ["-e", "HiQS/"],
        ]
    if kind == "c2root":
        return [
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"] + p,
            [venv_python, "-m", "pip", "install"] + p + ["torch"],
            [venv_python, "-m", "pip", "install"] + p + ["-e", ".[calendar,server,embeddings]", "pytest"],
        ]
    if kind == "c2hiqs":
        return [
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"] + p,
            [venv_python, "-m", "pip", "install"] + p + ["-e", "HiQS/", "pytest"],
        ]
    if kind == "c3":
        # No torch: the embeddings extra is the only thing that pulls it, and a
        # torch-free root lane is C3's entire premise. (Protocol §4 C3.)
        return [
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"] + p,
            [venv_python, "-m", "pip", "install"] + p + ["-e", ".[calendar,server]", "pytest"],
        ]
    if kind == "c4":
        return [
            [venv_python, "-m", "pip", "install", "--upgrade", "pip"] + p,
            [venv_python, "-m", "pip", "install"] + p + ["torch"],
            [venv_python, "-m", "pip", "install"] + p + ["-e", ".[calendar,server,embeddings]", "pytest"],
            [venv_python, "-m", "pip", "install"] + p + ["pytest-xdist"],
        ]
    raise SystemExit(f"unknown kind {kind}")


def nocache(mode: str) -> list[str]:
    return ["--no-cache-dir"] if mode == "cold" else []


def sys_python(py: str) -> str:
    return f"/opt/homebrew/bin/python{py}"


def venv_dir(py: str, kind: str, mode: str) -> Path:
    suffix = "" if mode == "warm" else "-cold"
    return VENV_ROOT / f"py{py}-{kind}{suffix}"


def host_info() -> dict:
    chip = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True).stdout.strip()
    macos = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True).stdout.strip()
    return {"platform": platform.platform(), "macos": macos, "chip": chip, "host": platform.node()}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def record(**kw) -> dict:
    rec = {
        "schema_version": SCHEMA,
        "run_id": uuid.uuid4().hex[:12],
        "campaign": CAMP,
        "commit": COMMIT,
        "evidence_source": "S1",
        "recorded_at": utcnow(),
        "host": host_info(),
    }
    rec.update(kw)
    with open(RUNS, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def run_cmd(argv: list[str], console_path: Path, cwd: Path) -> tuple[float, int]:
    t0 = time.monotonic()
    with open(console_path, "wb") as out:
        proc = subprocess.run(argv, cwd=cwd, stdout=out, stderr=subprocess.STDOUT)
    return time.monotonic() - t0, proc.returncode


def already_recorded(want: dict) -> bool:
    """Idempotence: a cell interrupted mid-campaign (e.g. transient DNS) can be
    re-driven without duplicating records. Skips on exact (cell, candidate,
    python, run_index, ...) match."""
    if not RUNS.exists():
        return False
    with open(RUNS) as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if all(r.get(k) == v for k, v in want.items()):
                return True
    return False


def cmd_setup(args) -> None:
    if already_recorded({"cell": "M1" if args.mode == "cold" else "M2", "candidate": args.kind,
                         "python": args.py, "run_index": args.run, "mode": args.mode}):
        print(f"skip (already recorded): setup {args.kind} py{args.py} {args.mode} r{args.run}")
        return
    vp = venv_dir(args.py, args.kind, args.mode)
    if vp.exists():
        subprocess.run(["rm", "-rf", str(vp)], check=True)
    t0 = time.monotonic()
    subprocess.run([sys_python(args.py), "-m", "venv", str(vp)], check=True, capture_output=True)
    venv_python = str(vp / "bin" / "python")
    # venv creation is untimed setup; steps below are the timed cells
    cell = "M1" if args.mode == "cold" else "M2"
    for i, step in enumerate(steps_for(args.kind, args.mode, venv_python), start=1):
        cpath = CONSOLE / f"{cell}-{args.kind}-py{args.py}-{args.mode}-step{i}-r{args.run}.txt"
        wall, rc = run_cmd(step, cpath, REPO)
        record(cell=cell, candidate=args.kind, lane=f"install-step{i}", python=args.py,
               argv=step, cwd=str(REPO), wall_s=round(wall, 3), exit_code=rc,
               console_path=str(cpath.relative_to(REPO)), console_sha256=sha256_file(cpath),
               run_index=args.run, mode=args.mode)
        if rc != 0:
            sys.exit(f"install step {i} failed rc={rc}; see {cpath}")
    freeze_path = ARTIFACTS / f"freeze-{args.kind}-py{args.py}-{args.mode}.txt"
    subprocess.run([venv_python, "-m", "pip", "freeze"], cwd=REPO, stdout=open(freeze_path, "w"), check=True)
    print(f"setup done: {vp} ({time.monotonic()-t0:.1f}s total)")


def cmd_collect(args) -> None:
    if already_recorded({"cell": "M3", "candidate": args.kind, "python": args.py,
                         "run_index": args.run, "lane": f"collect-{args.suite}"}):
        print(f"skip (already recorded): collect {args.suite} py{args.py} r{args.run}")
        return
    vp = venv_dir(args.py, args.kind, "warm")
    venv_python = str(vp / "bin" / "python")
    suite = "tests/" if args.suite == "tests" else "HiQS/tests"
    cpath = CONSOLE / f"M3-{args.suite}-{args.kind}-py{args.py}-r{args.run}.txt"
    argv = [venv_python, "-m", "pytest", suite, "--collect-only", "-q"]
    wall, rc = run_cmd(argv, cpath, REPO)
    text = cpath.read_text()
    nodes = sorted(line.strip() for line in text.splitlines() if "::" in line)
    list_path = INVENT / f"nodes-{args.suite}-py{args.py}.txt"
    list_path.write_text("\n".join(nodes) + "\n")
    record(cell="M3", candidate=args.kind, lane=f"collect-{args.suite}", python=args.py,
           argv=argv, cwd=str(REPO), wall_s=round(wall, 3), exit_code=rc,
           collected=len(nodes), node_list_path=str(list_path.relative_to(REPO)),
           node_list_sha256=sha256_file(list_path), console_path=str(cpath.relative_to(REPO)),
           console_sha256=sha256_file(cpath), run_index=args.run)
    if rc != 0:
        sys.exit(f"collection FAILED rc={rc} (fail-closed, cell invalid); see {cpath}")
    print(f"collected {len(nodes)} nodes rc={rc} wall={wall:.1f}s")


def nodeid_from_junit(classname: str, name: str) -> str:
    """Rebuild the true pytest nodeid. junit omits the file attr, so derive it
    from the dotted classname: a trailing Capitalized part is a test class
    (module.Class::test); otherwise the whole classname is the module."""
    parts = classname.split(".")
    if len(parts) > 1 and parts[-1][:1].isupper():
        return f"{'/'.join(parts[:-1])}.py::{parts[-1]}::{name}"
    return f"{'/'.join(parts)}.py::{name}"


def parse_junit(path: Path) -> dict:
    """Return {'counts': {...}, 'outcomes': {nodeid: outcome}} from a pytest junitxml."""
    root = ET.parse(path).getroot()
    counts = {"passed": 0, "failed": 0, "skipped": 0, "error": 0, "xfailed": 0, "xpassed": 0}
    outcomes = {}
    for tc in root.iter("testcase"):
        nid = nodeid_from_junit(tc.get("classname", ""), tc.get("name", ""))
        kids = list(tc)
        tags = {k.tag for k in kids}
        if "failure" in tags:
            o = "failed"
        elif "error" in tags:
            o = "error"
        elif "skipped" in tags:
            o = "skipped"
        else:
            o = "passed"
        # xfail/xpass: pytest marks via skip/failure with type attr containing "xfail"
        for k in kids:
            t = (k.get("type") or "")
            if "xfail" in t.lower() or "xpass" in t.lower():
                o = "xfailed" if "xpass" not in t.lower() else "xpassed"
        counts[o] = counts.get(o, 0) + 1
        outcomes[nid] = o
    return {"counts": counts, "outcomes": outcomes}


def cmd_suite(args) -> None:
    if already_recorded({"cell": args.cell, "candidate": args.kind, "python": args.py,
                         "run_index": args.run, "lane": f"suite-{args.suite}"}):
        print(f"skip (already recorded): suite {args.cell} {args.kind} py{args.py} r{args.run}")
        return
    vp = venv_dir(args.py, args.kind, "warm")
    venv_python = str(vp / "bin" / "python")
    if args.paths:
        suite_label = args.suite
        suite = args.paths.split()
    else:
        suite_label = args.suite
        suite = ["tests/"] if args.suite == "tests" else ["HiQS/tests"]
    junit = ARTIFACTS / f"junit-{args.cell}-{args.kind}-{suite_label}-py{args.py}-r{args.run}.xml"
    cpath = CONSOLE / f"{args.cell}-{args.kind}-{suite_label}-py{args.py}-r{args.run}.txt"
    argv = [venv_python, "-m", "pytest"] + suite + ["-q", "--durations=50",
            f"--junitxml={junit}"] + (args.pytest_args.split() if args.pytest_args else [])
    wall, rc = run_cmd(argv, cpath, REPO)
    parsed = parse_junit(junit) if junit.exists() else {"counts": {}, "outcomes": {}}
    # publish the per-node outcome map once per cell (identical across runs iff deterministic;
    # the three run records carry the sha256 so drift is visible)
    omap = INVENT / f"outcomes-{args.cell}-{args.kind}-{args.suite}-py{args.py}.jsonl"
    if not omap.exists() or args.run == 1:
        with open(omap, "w") as f:
            for nid, o in sorted(parsed["outcomes"].items()):
                f.write(json.dumps({"nodeid": nid, "outcome": o}, sort_keys=True) + "\n")
    record(cell=args.cell, candidate=args.kind, lane=f"suite-{args.suite}", python=args.py,
           argv=argv, cwd=str(REPO), wall_s=round(wall, 3), exit_code=rc,
           counts=parsed["counts"], executed=len(parsed["outcomes"]),
           junit_path=str(junit.relative_to(REPO)), junit_sha256=sha256_file(junit) if junit.exists() else None,
           outcome_map_path=str(omap.relative_to(REPO)), outcome_map_sha256=sha256_file(omap),
           console_path=str(cpath.relative_to(REPO)), console_sha256=sha256_file(cpath),
           run_index=args.run, cache_hit=None)
    print(f"{args.cell} {args.kind} {args.suite} py{args.py} r{args.run}: rc={rc} wall={wall:.1f}s "
          f"executed={len(parsed['outcomes'])} counts={parsed['counts']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup"); s.add_argument("--py", required=True); s.add_argument("--kind", required=True)
    s.add_argument("--mode", choices=["cold", "warm"], required=True); s.add_argument("--run", type=int, default=1)
    s.set_defaults(fn=cmd_setup)
    c = sub.add_parser("collect"); c.add_argument("--py", required=True); c.add_argument("--kind", default="c0")
    c.add_argument("--suite", choices=["tests", "hiqs"], required=True); c.add_argument("--run", type=int, default=1)
    c.set_defaults(fn=cmd_collect)
    u = sub.add_parser("suite"); u.add_argument("--py", required=True); u.add_argument("--kind", required=True)
    u.add_argument("--suite", choices=["tests", "hiqs", "seam"], required=True)
    u.add_argument("--paths", type=str, default=None, help="space-separated test paths (overrides --suite target)")
    u.add_argument("--cell", required=True)
    u.add_argument("--run", type=int, default=1); u.add_argument("--pytest-args", type=str, default=None)
    u.set_defaults(fn=cmd_suite)
    args = ap.parse_args()
    CONSOLE.mkdir(parents=True, exist_ok=True)
    INVENT.mkdir(parents=True, exist_ok=True)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    args.fn(args)


if __name__ == "__main__":
    main()
