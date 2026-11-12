#!/usr/bin/env bash
# GH-377 evidence: red control (A1), decay witnesses (A2/A3), quarantine (A4).
# Usage: witness.sh <disposable-clone> <python> <base-sha> <fix-sha>
# Mutates only the disposable clone's working tree; restores with git checkout.
set -uo pipefail
V="$1" PY="$2" BASE="$3" FIX="$4"
cd "$V" || exit 2
IDS=(
  tests/test_auto_promote.py::AutoPromoteTests::test_activity_commits_sum_across_scan_dates
  tests/test_auto_promote.py::AutoPromoteTests::test_auto_promoted_row_survives_activity_inference_sync
  tests/test_auto_promote.py::AutoPromoteTests::test_cloud_agent_commits_count_toward_threshold
  tests/test_auto_promote.py::AutoPromoteTests::test_direct_push_commits_count_not_just_pr_commits
  tests/test_auto_promote.py::AutoPromoteTests::test_idempotent_rerun_does_not_duplicate
  tests/test_auto_promote.py::AutoPromoteTests::test_name_collision_disambiguates_instead_of_overwriting
  tests/test_auto_promote.py::AutoPromoteTests::test_operator_push_and_bot_commits_combine
  tests/test_auto_promote.py::AutoPromoteTests::test_promotes_repo_at_threshold
  tests/test_auto_promote.py::AutoPromoteTests::test_promotion_fires_auth_log_alert
  tests/test_project_inference.py::ProjectInferenceTests::test_infers_binoid_from_github_and_ltvera_from_calendar_only
)
run() { PYTHONPATH="$V/src" PYTHONDONTWRITEBYTECODE=1 "$PY" -m pytest -p no:cacheprovider -q -rA "$@" 2>&1 | grep -E "^(PASSED|FAILED|XFAIL|XPASS|ERROR)|passed|failed" ; }
echo "## date (UTC): $(date -u +%FT%TZ)"
echo "## A1 red control — base $BASE"; git checkout -q "$BASE"; run "${IDS[@]}"
echo "## A1 green — fix $FIX (expect PASSED, not XPASS)"; git checkout -q "$FIX"; run "${IDS[@]}"
echo "## A2 decay witness — age helper defaults to -20d AND sum-test dates to -22/-21/-20 (expect 9 failed)"
sed -i.bak -e 's/or _days_ago(1)/or _days_ago(20)/' -e 's/or f"{_days_ago(1)}T/or f"{_days_ago(20)}T/' \
  -e 's/scan_date=_days_ago(3)/scan_date=_days_ago(22)/' -e 's/scan_date=_days_ago(2)/scan_date=_days_ago(21)/' \
  -e 's/scan_date=_days_ago(1)/scan_date=_days_ago(20)/' tests/test_auto_promote.py
grep -c "_days_ago(2[0-2])" tests/test_auto_promote.py | sed 's/^/mutated sites: /'
run tests/test_auto_promote.py; git checkout -q -- tests/; rm -f tests/*.bak
echo "## A2 restored"; run tests/test_auto_promote.py
echo "## A3a decay witness — remove the now_utc freeze (patch target -> unused name; expect BetaReport failure)"
sed -i.bak 's/mock.patch("rebalance.ingest.project_inference.now_utc", return_value=fixture_now)/mock.patch("rebalance.ingest.project_inference.COMMIT_THRESHOLD_GENERATED_BY", "x")/' tests/test_project_inference.py
grep -c 'COMMIT_THRESHOLD_GENERATED_BY", "x"' tests/test_project_inference.py | sed 's/^/mutated sites: /'
run "${IDS[9]}"; git checkout -q -- tests/; rm -f tests/*.bak
echo "## A3b decay witness — freeze at 2030-01-01 (outside 90d; expect failure)"
sed -i.bak 's/datetime(2026, 4, 28, 16, 0, tzinfo=timezone.utc)/datetime(2030, 1, 1, 0, 0, tzinfo=timezone.utc)/' tests/test_project_inference.py
grep -c 'datetime(2030' tests/test_project_inference.py | sed 's/^/mutated sites: /'
run "${IDS[9]}"; git checkout -q -- tests/; rm -f tests/*.bak
echo "## A3 restored"; run "${IDS[9]}"
echo "## A4 quarantine list + helper tests"
PYTHONPATH="$V/src" "$PY" -c "import sys; sys.path.insert(0, 'tests'); import conftest; assert conftest.__file__.endswith('tests/conftest.py'), conftest.__file__; print('KNOWN_FAILING_GH178 =', conftest.KNOWN_FAILING_GH178)"
run tests/test_conftest_quarantine.py
git status --short | sed 's/^/DIRTY: /'
