#!/bin/bash
# GH-144 Phase 0 M10 — witnessed-red negative controls (protocol §8).
# For each lane: append a failing test (the mutation), run ONLY the lane
# command, capture red exit + failing node, revert, re-run for post-green.
# Every artifact is retained under console/ with an M10- prefix.
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
CAMP=TESTS-RESULTS/2026-09-01+GH-144
CON=$CAMP/console
RUNS=$CAMP/runs.jsonl
MUT='
def test_gh144_witnessed_red_negative_control():
    assert False, "GH-144 Phase 0 witnessed-red negative control (M10)"
'

record() { # label phase exit_code wall_s console_path extra_json
  python3 - "$@" <<'PY'
import json, sys, uuid, subprocess, datetime
label, phase, rc, wall, cpath, extra = sys.argv[1:7]
rec = {"schema_version":1, "run_id":uuid.uuid4().hex[:12], "campaign":"2026-09-01+GH-144",
       "commit":subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True).stdout.strip(),
       "evidence_source":"S1", "cell":"M10", "candidate":"witnessed-red", "lane":label,
       "phase":phase, "exit_code":int(rc), "wall_s":float(wall),
       "console_path":cpath, "recorded_at":datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
if extra and extra != "-":
    rec.update(json.loads(extra))
open("TESTS-RESULTS/2026-09-01+GH-144/runs.jsonl","a").write(json.dumps(rec, sort_keys=True)+"\n")
PY
}

witness() { # label file venv_python pytest_args...
  local label=$1 file=$2 venv=$3; shift 3
  local args="$*"
  echo "=== $label: mutation -> red -> revert -> green ==="
  cp "$file" "$file.gh144bak"
  printf '%s\n' "$MUT" >> "$file"
  git diff -- "$file" > "$CON/M10-$label-mutation.diff"
  local t0=$(date +%s) rc=0
  "$venv" -m pytest $args -q > "$CON/M10-$label-red.txt" 2>&1 || rc=$?
  local t1=$(date +%s)
  record "$label" "red" "$rc" "$((t1-t0))" "$CON/M10-$label-red.txt" '{"failing_node":"tests_or_hiqs::test_gh144_witnessed_red_negative_control"}'
  echo "  red: exit=$rc wall=$((t1-t0))s"
  mv "$file.gh144bak" "$file"
  git status --porcelain -- "$file" | grep -q . && { echo "  REVERT FAILED"; exit 1; }
  echo "  revert: tree clean"
  t0=$(date +%s); rc=0
  "$venv" -m pytest $args -q > "$CON/M10-$label-postgreen.txt" 2>&1 || rc=$?
  t1=$(date +%s)
  record "$label" "post-green" "$rc" "$((t1-t0))" "$CON/M10-$label-postgreen.txt" '-'
  echo "  post-green: exit=$rc wall=$((t1-t0))s"
}

PY312_C0=temp/gh144/venvs/py3.12-c0/bin/python
PY312_C2HIQS=temp/gh144/venvs/py3.12-c2hiqs/bin/python
PY312_C3=temp/gh144/venvs/py3.12-c3/bin/python
PY312_C4=temp/gh144/venvs/py3.12-c4/bin/python
IGN="--ignore=tests/test_embedder.py --ignore=tests/test_embedder_metal_unavailable.py"

# Lane controls (protocol §8). Root mutation lands in a NON-seam file so it
# must route to every root lane (C0/C2/C4 and C3-root).
witness root-lane      tests/test_querier.py "$PY312_C0" tests/
witness xdist-lane-n4  tests/test_querier.py "$PY312_C4" tests/ -n 4 --dist load
witness hiqs-lane      HiQS/tests/test_events.py "$PY312_C2HIQS" HiQS/tests
witness seam-lane      tests/test_embedder_metal_unavailable.py "$PY312_C0" tests/test_embedder.py tests/test_embedder_metal_unavailable.py

# Routing control: with the mutation inside a SEAM file, the C3 root lane
# (which ignores seam files) must stay GREEN — the failure belongs to the seam
# lane, which went red above.
echo "=== c3-root-routing: seam mutation must NOT fail the ignoring lane ==="
cp tests/test_embedder_metal_unavailable.py tests/test_embedder_metal_unavailable.py.gh144bak
printf '%s\n' "$MUT" >> tests/test_embedder_metal_unavailable.py
t0=$(date +%s); rc=0
"$PY312_C3" -m pytest tests/ $IGN -q > "$CON/M10-c3root-routing-green.txt" 2>&1 || rc=$?
t1=$(date +%s)
record "c3-root-routing" "green-under-seam-mutation" "$rc" "$((t1-t0))" "$CON/M10-c3root-routing-green.txt" '-'
echo "  c3-root green under seam mutation: exit=$rc wall=$((t1-t0))s"
mv tests/test_embedder_metal_unavailable.py.gh144bak tests/test_embedder_metal_unavailable.py
git status --porcelain -- tests/ | grep -q . && { echo "  REVERT FAILED"; exit 1; }
echo "M10 complete"
