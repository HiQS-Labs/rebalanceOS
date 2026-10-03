#!/usr/bin/env bash
# Commands that produced the receipts in console/ (review device, disposable
# full clone of HiQS-Labs/rebalanceOS on the PR branch, .venv with all extras).
set -euo pipefail
DB=/tmp/rb-308-fix-data/rebalance.db   # consistent `sqlite3 .backup` of the device DB

PY=.venv/bin/python
REB=.venv/bin/rebalance
CAM=TESTS-RESULTS/2026-10-02+GH-307

# Focused suites
$PY -m pytest tests/test_github_close_loop.py tests/test_github_readiness.py \
  tests/test_queries_mirror_invariance.py -q | tee "$CAM/console/focused-tests.log"

# CLI smoke (json + wall time per repo)
for repo in HiQS-Labs/rebalanceOS HiQS-Labs/XYZ-forge HiQS-Labs/Needle-fork; do
  safe=${repo//\//-}
  /usr/bin/time $REB github-close-loop --repo "$repo" --database "$DB" --output json \
    > "$CAM/console/cli-smoke-${safe}.json" 2> "$CAM/console/cli-smoke-${safe}.time"
done

# Mutation red-controls: apply each mutation to the committed tree, run the
# close-loop suite, `git checkout --` the file back. Full transcript with
# expectations: console/mutation-red-controls.log.

# Corpus fractions
sqlite3 "$DB" < scripts/corpus-fractions.sql | tee "$CAM/console/corpus-fractions.txt"
