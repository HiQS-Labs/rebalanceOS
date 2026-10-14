"""GH-312 pre-push gate spike timing runner.

Runs a command N times serially, emitting one JSONL primitive record per run to
stdout and the full console of each run to a file. Serial by design: timing runs
must not overlap or they contend and the medians lie.
"""
import datetime as dt
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

def tree_state():
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    st = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True).stdout
    dirty = [l[3:] for l in st.splitlines() if l.strip()]
    return head, sorted(dirty)

def main():
    label, n = sys.argv[1], int(sys.argv[2])
    cmd = sys.argv[sys.argv.index("--") + 1:]
    outdir = Path("temp/spike-gh312/consoles"); outdir.mkdir(parents=True, exist_ok=True)
    head, _ = tree_state()
    for i in range(1, n + 1):
        t0 = time.perf_counter()
        started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        p = subprocess.run(cmd, capture_output=True, text=True)
        wall = time.perf_counter() - t0
        ended = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        console = outdir / f"{label}-run{i}.txt"
        console.write_text((p.stdout or "") + (p.stderr or ""))
        rec = {
            "schema_version": 1,
            "run_id": f"{label}-run{i}",
            "kind": label,
            "cmd": cmd,
            "exit": p.returncode,
            "wall_s": round(wall, 2),
            "started_utc": started,
            "ended_utc": ended,
            "head": head,
            "console": str(console),
        }
        print(json.dumps(rec), flush=True)

if __name__ == "__main__":
    main()
