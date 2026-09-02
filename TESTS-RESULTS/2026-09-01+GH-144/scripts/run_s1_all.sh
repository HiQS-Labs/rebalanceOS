#!/bin/bash
# GH-144 Phase 0 S1 driver — executes cells M1-M9 sequentially per protocol §6.
# M7 suite failures are expected data (seam enumeration), so this script does
# NOT stop on pytest non-zero; only setup failures (run_s1.py exits) stop it.
set -uo pipefail
cd "$(dirname "$0")/../../../" || exit 1
S="TESTS-RESULTS/2026-09-01+GH-144/scripts/run_s1.py"
PY=python3

echo "=== M1 cold installs (c0) ==="
for r in 2 3; do $PY "$S" setup --py 3.12 --kind c0 --mode cold --run "$r" || exit 1; done
for r in 1 2 3; do $PY "$S" setup --py 3.13 --kind c0 --mode cold --run "$r" || exit 1; done

echo "=== M2 warm installs (c0) ==="
for py in 3.12 3.13; do
  for r in 1 2 3; do $PY "$S" setup --py "$py" --kind c0 --mode warm --run "$r" || exit 1; done
done

echo "=== M3 collection (c0) ==="
for py in 3.12 3.13; do
  for s in tests hiqs; do
    for r in 1 2 3; do $PY "$S" collect --py "$py" --kind c0 --suite "$s" --run "$r" || exit 1; done
  done
done

echo "=== M4 root suite + M5 HiQS suite (c0) ==="
for py in 3.12 3.13; do
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c0 --suite tests --cell M4 --run "$r"; done
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c0 --suite hiqs --cell M5 --run "$r"; done
done

echo "=== M4b root lane without HiQS installed (c2root) ==="
for py in 3.12 3.13; do
  for r in 1 2 3; do $PY "$S" setup --py "$py" --kind c2root --mode warm --run "$r" || exit 1; done
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c2root --suite tests --cell M4b --run "$r"; done
done

echo "=== M6 HiQS lane, HiQS-only venv (c2hiqs) ==="
for py in 3.12 3.13; do
  for r in 1 2 3; do $PY "$S" setup --py "$py" --kind c2hiqs --mode warm --run "$r" || exit 1; done
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c2hiqs --suite hiqs --cell M6 --run "$r"; done
done

echo "=== M7 root suite without embeddings extra (c3) — failures are the data ==="
for py in 3.12 3.13; do
  for r in 1 2 3; do $PY "$S" setup --py "$py" --kind c3 --mode warm --run "$r" || exit 1; done
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c3 --suite tests --cell M7 --run "$r"; done
done

echo "=== M7IGN + M7b: C3 gate — remaining root green with seam ignored, seam green with the extra ==="
# Seam files derived from M7's outcome deltas at 8f733ce (analyze.py re-derives
# and checks them; a new embeddings-dependent test outside these files must
# fail M7IGN red — that is the fail-closed property, do not paper over it).
IGN="--ignore=tests/test_embedder.py --ignore=tests/test_embedder_metal_unavailable.py"
SEAM="tests/test_embedder.py tests/test_embedder_metal_unavailable.py"
for py in 3.12 3.13; do
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c3 --suite tests --cell M7IGN --run "$r" --pytest-args="$IGN"; done
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c0 --suite seam --paths "$SEAM" --cell M7b --run "$r"; done
done

echo "=== M8/M9 xdist root suite (c4) ==="
for py in 3.12 3.13; do
  for r in 1 2 3; do $PY "$S" setup --py "$py" --kind c4 --mode warm --run "$r" || exit 1; done
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c4 --suite tests --cell M8 --run "$r" --pytest-args="-n 2 --dist load"; done
  for r in 1 2 3; do $PY "$S" suite --py "$py" --kind c4 --suite tests --cell M9 --run "$r" --pytest-args="-n 4 --dist load"; done
done

echo "=== S1 driver complete ==="
