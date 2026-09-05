---
gh_issue: 177
source: https://github.com/HiQS-Labs/rebalanceOS/issues/177
title: "GH-177 doctor warns daily when the runtime trails origin/development"
status: "Proposed (1-INBOX — not yet active). Rated 2026-09-04; ratings await operator confirmation."
created: 2026-09-04
updated: 2026-09-04
owner: noel
doc_type: hygiene
goal: >
  Surface `stack.sh drift` from the daily `rebalance doctor` run as a WARN, so a runtime
  that trails development is reported without anyone typing a command. Reuse the existing
  check; do not grow a second drift algorithm.
effort: 2
complexity: 2
risk: 1
phases: 1
ratings_provisional: true
roadmap_exempt: true
---

# GH-177 — doctor warns daily when the runtime trails development

## Status

| What was just completed | What's next |
|---|---|
| The check itself shipped in PR #178: `scripts/stack.sh drift` (exit 1 when behind), the same line at the foot of `stack.sh status`, a `.githooks/post-merge` reminder, SOP.md § 7, and `tests/test_runtime_drift.py` including the `GIT_DIR` trap. Rated here. | Operator confirms the ratings (flip `ratings_provisional` to `false`), then it is eligible for auto-pick: `risk 1`, `ease 4`, one phase. |

## Why

`stack.sh drift` only speaks when someone runs it or merges in a dev checkout. The failure it
exists to catch is *nobody doing anything*: on 2026-09-04 eight PRs merged and the runtime
stayed on 2026-09-02's code all day. `doctor` ran that morning and listed five problems — none
of them "you are running two-day-old code", because it had no way to know. The durable half is
the daily job saying it.

## Ratings, with reasons

| Field | Value | Why |
|---|---|---|
| `effort` | 2 | ~20 lines: a `_check_runtime_drift()` in the shape of `_check_token()` ([doctor.py:203](../../src/rebalance/doctor.py#L203)) that shells to `stack.sh drift` and maps exit 1 → WARN; one test; one `TESTS-RESULTS/` record for the two acceptance runs. |
| `complexity` | 2 | One integration seam, Python → bash, and one constraint worth getting right: resolve the runtime through `~/.config/rebalance/runtime-root` as `install_common.sh` does, never a `parents[N]` walk (AGENTS.md #152). The `GIT_DIR` trap is already handled inside `stack.sh`. Not a 1 because the seam crosses languages and the threshold needs a stated rule. |
| `risk` | 1 | Additive, WARN-only, read-only (a `git fetch`). Reversible by deleting one function. "Easy" on the reversibility scale. |
| `phases` | 1 | — |

`ease = effort + complexity = 4`. Eligible for auto-selection once the operator clears
`ratings_provisional`.

## Plan

1. `_check_runtime_drift()` in `src/rebalance/doctor.py`: run `bash scripts/stack.sh drift` with
   `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` unset; exit 0 → no check emitted (or OK, per the
   existing convention for quiet checks); exit 1 → `WARN` with the script's stdout as the message
   and the pull command as the remedy.
2. Threshold: warn at ≥ 1 commit behind **and** the runtime's `HEAD` commit date ≥ 24 h old.
   A runtime one commit behind for an hour is normal. Record the rule in the docstring.
3. Test: monkeypatch the subprocess result; assert WARN on exit 1, silence on exit 0. The real
   drift arithmetic is already pinned by `tests/test_runtime_drift.py`; do not duplicate it.
4. Acceptance: with the runtime deliberately one day behind, the next scheduled `doctor` run
   shows the WARN and the health issue carries it; up to date, no line. Both runs into
   `TESTS-RESULTS/` (SOP § 1).

## Non-goals

- Auto-deploying. The pull stays a deliberate operator action (AGENTS.md § "Deploy runtime folder").
- Paging. This is a reminder; FAIL is reserved for things that break a run.
