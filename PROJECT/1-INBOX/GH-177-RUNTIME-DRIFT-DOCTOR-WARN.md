---
gh_issue: 177
source: https://github.com/HiQS-Labs/rebalanceOS/issues/177
title: "GH-177 doctor warns daily when the runtime trails origin/development"
status: "Proposed (1-INBOX — not yet active). Rated 2026-09-04, re-rated 2026-09-05 after advisory review; ratings_provisional stays true deliberately — see Ratings."
created: 2026-09-04
updated: 2026-09-05
owner: noel
doc_type: hygiene
goal: >
  Surface `stack.sh drift` from the daily `rebalance doctor` run as a WARN, so a runtime
  that trails development is reported without anyone typing a command. Reuse the existing
  check; do not grow a second drift algorithm.
effort: 2
complexity: 3
risk: 2
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

Re-rated 2026-09-05. An advisory review disputed all three axes; two were raised and the
eligibility flag deliberately left set. **Codex was unavailable** (its configured model needs a
newer CLI), so this was one advisor's read plus first-hand evidence from the session that built
`stack.sh drift` — not a cross-verified consult.

| Field | Value | Why |
|---|---|---|
| `effort` | 2 | ~20 lines: a `_check_runtime_drift()` in the shape of `_check_token()` ([doctor.py:203](../../src/rebalance/doctor.py#L203)) that shells to `stack.sh drift` and maps exit 1 → WARN; one test; one `TESTS-RESULTS/` record for the two acceptance runs. Unchanged. |
| `complexity` | 3 | **Raised from 2.** Four concerns, not one: a Python→bash seam; resolving the runtime through `~/.config/rebalance/runtime-root` (never a `parents[N]` walk, AGENTS.md #152); a *compound* threshold needing both a commit count and a commit date; and a test that monkeypatches the subprocess. The original 2 assumed the threshold was free because `stack.sh` already computes drift. It is not — the date half is a second query nothing provides yet. |
| `risk` | 2 | **Raised from 1.** Still the Easy end of the reversibility scale — additive, WARN-only, deleted in one function. But a subtle bug here does not merely fail: it emits a false green in a daily automated report, masking the exact drift the check exists to catch. Within the 1–2 bucket, that is a 2. Still `<= 2`, so eligibility is unaffected. |
| `phases` | 1 | Unchanged. |

`ease = effort + complexity = 5` (was 4).

### Why `ratings_provisional` stays `true`

The blocker is concrete, not caution. Step 2 needs the runtime's `HEAD` **commit date**, and
`stack.sh drift` does not emit one — so whoever implements this writes a *new* git call against
the runtime. That is precisely where the `GIT_DIR` trap lives: git hooks export
`GIT_DIR`/`GIT_WORK_TREE`, and with them set `git -C <runtime>` silently measures the calling
checkout instead. It has already happened once here — the first `.githooks/post-merge` probe
printed "up to date" while the runtime was 51 commits behind. `runtime_drift()` clears those three
variables; a fresh git call in `doctor.py` would not, unless the implementer knows to.

An agent auto-selecting this on `ease = 5` would not know to. So the flag stays set, and the
condition to clear it is written down rather than left to judgement:

> **Clear `ratings_provisional` once `stack.sh drift` also emits the runtime `HEAD` commit date**,
> so the doctor check consumes one already-guarded command and makes no git call of its own. At
> that point the compound threshold is a string parse, `complexity` drops back to 2, and the item
> is safe to auto-pick.

That is a small change to a file that already has the guard and the test. It is the cheapest way
to make this item genuinely autonomous rather than nominally so.

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
