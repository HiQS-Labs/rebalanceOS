---
gh_issue: 377
source: https://github.com/HiQS-Labs/rebalanceOS/issues/377
title: "ci: development red — GH-178 quarantine expired and auto-promote/project-inference fixtures aged out"
status: in-progress
created: 2026-11-11
updated: 2026-11-11
owner: Claude
doc_type: bugfix
complexity: 1
risk: 1
effort: 1
phases: 1
ratings_provisional: false
non_goals:
  - no production code change (rolling windows stay as they are)
  - no new tests, suites or conftest machinery
  - no change to the GH-312 P13 expiry helper or its tests
related:
  - https://github.com/Hypercart-Dev-Tools/rebalance-OS/issues/178
  - "#239 / PR #243 (same class: fixed-date fixtures vs rolling windows)"
  - "#312 (P13 quarantine expiry)"
goal: >
  The 10 GH-178 tests pass on any future date without an xfail marker, KNOWN_FAILING_GH178 is empty,
  and root-noembed is green on development, with production windows unchanged.
---

# GH-377 — GH-178 quarantine expiry and fixture aging

## Status

| What was just completed | What's next |
|---|---|
| Reproduced the 10 failures, traced them, falsified the hypothesis and wrote the plan (below). | Codex plan QA, then implementation. |

## Observed (base `88a8972`, 2026-11-11)

| # | Evidence | Finding |
|---|---|---|
| O1 | CI run 43108616401 (`88a8972`), `root-noembed (3.13)` | `10 failed, 2821 passed`: 9 `test_auto_promote` (`0 != 1`, `0 != 2`, mock not called) and `test_infers_binoid_…` (`'BetaReport' not found in ['Acme']`) |
| O2 | CI run 40994899932 (`f081931`, 2026-10-30) | The same 10 are **XFAIL** with reason `… issue: #178; expires 2026-11-01T00:00:00Z`. Job was green |
| O3 | `tests/conftest.py` `GH178_QUARANTINE_EXPIRES_UTC`, `gh178_quarantine_expired()`, `pytest_collection_modifyitems` | At or after the expiry, the xfail marker is withheld (GH-312 P13 "return to gate"). The "date dependence" first shows up here: the quarantine expired, so red CI on #376 was the first unmasked run, not a regression |
| O4 | `src/rebalance/ingest/project_inference.py:948` `sync_commit_threshold_promotions` → `index_ops.get_watched_repos(since_days=14)["auto_discovered"]` → `_activity_repos` (`index_ops.py:932`) | Candidates require `scan_date >= date('now','-14 days')`, which is the **SQLite** clock, not `time_ops.now_utc` |
| O5 | `tests/test_auto_promote.py:29,46,118-120` | Fixtures default to `committed_at="2026-07-01T00:00:00Z"` / `scan_date="2026-07-01"`, and the sum test uses 06-30, 07-01 and 07-02. That leaves 0 candidates and 0 promotions |
| O6 | `project_inference.py:233` `_load_calendar_events` | `today = now_utc().date()` with a `days_back=90` window. The test's two `BetaReport Weekly` events (2026-04-17 and 04-24) fell out of the window around 2026-07-16, so BetaReport (which needs ≥2 calendar events) is never seeded. Acme survives because `_build_seeds_from_github` has no window |
| O7 | Falsification, scratch clone of `88a8972`, `test_auto_promote.py` dates sed-shifted | today−10d: `16 passed`. today−22d: `9 failed, 7 passed`. The production promotion logic is correct for in-window data, so the 9 are pure fixture aging |
| O8 | Upstream issue Hypercart-Dev-Tools/rebalance-OS#178 (open) | The July report "auto-promote is not promoting" was the same visible symptom. Whatever the July product cause was (pre-`ed320289` `_activity_repos` filter), at HEAD the only remaining cause is the date window (O7) |

**Production change needed?** None is needed to fix these ten failures (O7 plus the traced windows support that scope; this is not a claim that the auto-promote path is defect-free). Both windows are intended rolling windows (`get_watched_repos` docstring, "active in the last 14 days"; calendar 90/14). `_activity_repos` uses SQLite `date('now')` while `_pushed_repos` uses `time_ops.now_utc()`. Both read the real wall clock, and the inconsistency only matters for clock-freezing tests. Not in scope; noted.

## Plan (one phase, test-only)

1. **`tests/test_auto_promote.py`.** Compute fixture dates relative to the current UTC date, because the SQLite `date('now')` cutoff cannot be frozen from Python (same approach as PR #243).
   - Add a module helper `_days_ago(n) -> str` that returns `(datetime.now(timezone.utc).date() - timedelta(days=n)).isoformat()`.
   - `_insert_activity(scan_date=None)` defaults to `_days_ago(1)`; `_insert_commit(committed_at=None)` defaults to `f"{_days_ago(1)}T00:00:00Z"`.
   - `test_activity_commits_sum_across_scan_dates` uses `_days_ago(3)`, `_days_ago(2)` and `_days_ago(1)`. Its docstring/comment contract (sum across scan_dates) is unchanged.
   - Rationale for yesterday instead of today: it sits well inside the 14-day window and avoids a UTC-midnight race between Python's `now` and SQLite's `date('now')`.
2. **`tests/test_project_inference.py::test_infers_binoid_from_github_and_ltvera_from_calendar_only`.** Freeze the Python clock the 90-day window reads: wrap the `infer_project_registry(...)` call in `mock.patch("rebalance.ingest.project_inference.now_utc", return_value=datetime(2026, 4, 28, 16, 0, tzinfo=timezone.utc))`, the fixture's own `scanned_at`/`fetched_at` instant. Assertions are unchanged.
3. **`tests/conftest.py`.** Set `KNOWN_FAILING_GH178` to an empty set, as its own comment requires ("This list must shrink to empty"). Update the comment to record that GH-377 emptied it, and keep the expiry helper, reason text and `tests/test_conftest_quarantine.py` (they test the helper, not the list).
4. **Evidence** in `TESTS-RESULTS/2026-11-11+GH-377/`: red control on base, green on the fix, decay witnesses (below), full `pytest tests/` before and after, smoke receipt and `provenance.jsonl`.

## Acceptance (falsifiable)

- A1: On base `88a8972`, the 10 test IDs fail (red control, recorded). On the fix commit they pass **without** an xfail marker (`-rA` output shows PASSED, not XPASS).
- A2 (decay falsifier, auto-promote): in a disposable clone, temporarily age **both** date inputs outside the 14-day window: the helper defaults (`_days_ago(20)`) **and** the sum test's explicit dates (`_days_ago(22/21/20)`). All 9 fail. Restore, and they pass. This witnesses that fixture dates are the only date coupling. (Plan QA R1: aging only the default would leave the sum test passing, so 8, not 9.)
- A3 (decay falsifier, project inference): remove the `now_utc` patch and the test fails with the `BetaReport` assertion. With the patch it passes. Also run it with the patch at a far-future `now` (2030-01-01, outside the window) and see it fail, which shows the patch is load-bearing.
- A4: `KNOWN_FAILING_GH178 == set()`, and `tests/test_conftest_quarantine.py` passes.
- A5: `pytest tests/` on the fix has no failure outside base's failure set minus these 10 (the local env may carry unrelated pre-existing failures; they are recorded by ID on both sides).
- A6: Hosted `root-noembed` (3.12 and 3.13) green on the PR head.

## Preflight bet check

- **Outcome sought:** CI on `development` regains its red/green signal; the 10 tests guard GH-124 auto-promotion again instead of being masked or red.
- **Smallest bet:** three test files, about 30 changed lines. No production change and no new tests.
- **Alternatives rejected:** (a) re-quarantine with a fresh expiry: hides a now-fixable test defect, and the conftest comment forbids it. (b) Widen or parametrize production windows: changes behavior to suit tests. (c) Patch SQLite `date('now')` or add libfaketime/freezegun: new dependency or machinery for 9 tests, when clock-relative fixtures (precedent #243) suffice.
- **Rollback:** revert the single commit; tests return to red (the quarantine has expired either way).

## Risks

- Python vs. SQLite date at UTC midnight: avoided by using yesterday (−1d) instead of today.
- `test_auto_promoted_row_survives_activity_inference_sync` also runs `sync_inferred_project_registry` (`_seed_status` / calendar windows) on the relative dates. Recent dates give status `active`; its assertions check only that the auto-promoted row survives.

## Rating

rated 70/55/50/85 (2026-11-11). sev 55: CI red on `development` hides new breakage; test-only, no data loss. pri 70: severity-led, every merge goes red until fixed. appeal 50: neutral. effort 85: three test files. Recurrence: same class as #239 (2026-09-21); 1 incident in the last 14 days (this) vs 0 in the prior 14.
