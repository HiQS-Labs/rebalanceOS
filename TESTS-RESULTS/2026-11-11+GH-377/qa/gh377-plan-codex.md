# RELAY · gh377-plan-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-11-11.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 2 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns. Plain blank separators may be added or removed between sections; preserve every substantive line, indentation, and fenced/literal blank line. A historical FAIL→PASS edit or changed fenced example is forbidden.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh377-plan-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/2-WORKING/GH-377-AUTO-PROMOTE-FIXTURE-AGING.md` (the plan). Plan QA happens before any implementation; no test/code change exists yet.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-11-11
- Definition of Done: the plan is grounded in the actual code paths, fixes the 10 named failures by removing the tests' time dependence without changing production behavior, stays surgical and test-only, and has falsifiable acceptance (A1–A6).

### Step 1: paraphrase first (GH-1414)
Read **only the plan doc** first. Before opening any source file, write 2–5 sentences under each of **What this proposes** and **How the existing system works, per this document**, plus a short **What it's not**. Label inferences. Record the input boundary ("plan doc only").

### Step 2: source-backed validation
Then read these and validate the plan (label this part source-backed):
- `tests/conftest.py` (GH-178 quarantine list + expiry helper), `tests/test_conftest_quarantine.py`
- `tests/test_auto_promote.py`, `tests/test_project_inference.py`
- `src/rebalance/ingest/project_inference.py` (`_load_calendar_events`, `_seed_status`, `infer_project_registry`, `sync_commit_threshold_promotions`, `_count_operator_commits`)
- `src/rebalance/ingest/index_ops.py` (`_activity_repos`, `_pushed_repos`, `get_watched_repos`)
- Issue https://github.com/HiQS-Labs/rebalanceOS/issues/377 (body mirrors the plan); precedent PR #243 for #239.

**Operational envelope:** a test-only fix in a single-repo local/CI Python suite. Grade against the stated acceptance and commensurate complexity. Do not ask for freezegun/libfaketime, new suites, or production refactors unless you show a concrete failing input that the plan misses.

### Questions
1. Do the cited code paths and line refs match? Is the 14-day window really SQLite `date('now')`, and the calendar 90-day window really `now_utc()` in `project_inference`'s namespace (so patching `rebalance.ingest.project_inference.now_utc` takes effect)?
2. Does any of the 9 auto-promote tests depend on a date other than the `_insert_activity` / `_insert_commit` defaults and the sum test's explicit dates? Does anything break when `test_auto_promoted_row_survives_activity_inference_sync` runs with recent dates?
3. In the project-inference test, is freezing `now_utc` at 2026-04-28T16:00Z sufficient and correct for `_seed_status` too? Does it make BetaReport seed (≥2 calendar events inside 90d)?
4. Is emptying `KNOWN_FAILING_GH178` correct and safe with respect to `tests/test_conftest_quarantine.py` and the collection hook?
5. Is the "no production bug" conclusion supported? Is there any genuine defect in the auto-promote path at HEAD that the tests would expose once in-window?
6. Are A1–A6 falsifiable, and are the red controls (A2/A3) meaningful? Is anything missing or over-built?
7. Is the 70/55/50/85 rating grounded (appeal neutral)?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns. Plain blank separators may be added or removed between sections; preserve every substantive line, indentation, and fenced/literal blank line. A historical FAIL→PASS edit or changed fenced example is forbidden.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1 · codex

Input boundary: plan doc only (recorded before opening source files).

**What this proposes**
The plan replaces fixed July promotion dates with recent UTC dates and freezes calendar inference at the April fixture instant. It empties the expired quarantine while retaining expiry machinery, then requires base/fix and deliberate decay controls plus hosted CI evidence.

**How the existing system works, per this document**
Repository candidates use SQLite's rolling 14-day date filter, while calendar seeding uses the imported Python `now_utc` over 90 days. Calendar-only seeds need two events; quarantine expiry exposes nine promotion failures and one missing calendar seed. Inference: changing fixture time inputs should restore coverage without changing production windows.

**What it's not**
This is not a production change, renewed quarantine, new clock dependency, or production refactor.

**Source-backed validation**

swept file: yes

Reviewed the entire plan and all four named test files, plus the relevant production candidate/counting, calendar seed/status, write partition and stale cleanup paths. No additional pre-existing defect was identified in the test files beyond the known fixed-date fixtures; this is a bounded plan review, not a claim that all production behavior is defect-free.

- [Should] **Make A2's mutation match its expected nine failures.** The plan says “temporarily pass `scan_date=_days_ago(20)` ... to the default, and the 9 fail,” but the sum test bypasses that default with three explicit dates (`tests/test_auto_promote.py:118–120`; plan step 1 keeps explicit −3/−2/−1). Aging only the default leaves this test eligible. Cheapest fix: explicitly age all three sum-test dates as well (e.g. −22/−21/−20), or expect eight failures for the default-only mutation and separately witness the sum test's decay. This is an acceptance-protocol correction, not a request for production behavior changes.
  Observed input: three explicit `scan_date` arguments in `test_activity_commits_sum_across_scan_dates`, preserved as recent relative dates by step 1.
  Affected scope: A2's default-only mutation and its claimed nine-failure result.
  Falsifier: in the disposable clone, change only the default to −20 while retaining explicit −3/−2/−1; the sum test should pass. If it fails specifically from candidate aging, this finding is wrong.
- [Pass] **Clock ownership and minimal fix are supported.** `_activity_repos` uses `WHERE scan_date >= date('now', ?)` (`src/rebalance/ingest/index_ops.py:953`); `get_watched_repos` defaults to 14 days. `project_inference.py:11,240,468` imports and reads the same module-bound `now_utc` in calendar loading and status calculation. Patching that namespace for the entire inference call covers both; the April 17/24 events are within 90 days of April 28, and `project_inference.py:776` admits calendar-only seeds with at least two events. Keep the planned fixture-only approach.
- [Pass] **No additional date dependency found in the nine promotion tests.** The fixed inputs are the helper defaults and the explicit sum dates (`tests/test_auto_promote.py:29,46,118–120`); counting itself has no timestamp predicate (`project_inference.py:831`, `_count_operator_commits`). Recent inputs can change inferred status but stale deletion explicitly owns only `activity_inference_v1` (`project_inference.py:676–692`), so it does not delete an auto-promotion marker. Keep the survival assertion unchanged.
- [Pass] **Empty quarantine is compatible with existing helper coverage.** Collection tests membership before adding xfail (`tests/conftest.py:145`); the four tests in `tests/test_conftest_quarantine.py:18–36` exercise expiry/reason helpers rather than list contents. Use `set()`, not `{}`, and retain the helper tests as planned.
- [Unverified — no citation] **Scope and precedent fit.** Issue #377's “Plan (test-only, surgical)” matches the artifact. Merged PR #243 states “Production cutoffs are unchanged” and its diff derives activity snapshots from current UTC dates. The plan's “three test files” and neutral appeal 50 support a small, bounded repair; 70/55/50/85 is a reasonable prioritization judgment, not a measured score.
- [Nit] **Qualify the production conclusion.** “Production bug? No” is broader than the demonstrated fixture diagnosis. Prefer “No production change is needed to address these ten failures”; O7 and the traced windows support that scope, not universal correctness. No production refactor is requested.
- [Unverified — needs clone run] A1, A3–A6 and O7's behavioral results were not independently executed here. A1/base comparison, A3's removed/future freeze, A4's helper run, A5's failure-ID comparison and A6's two hosted lanes are falsifiable and proportionate. Preserve their raw evidence in the campaign; approve implementation results only after those receipts exist. No pytest, fixtures, validate scripts, or git commands were run in this turn.

VERDICT: FAIL
Basis: The implementation approach is sound and surgical, but A2 currently describes a mutation that cannot produce its claimed failure set. Clarify that red control before execution; no source change or additional suite is needed.

Handing off to Producer (claude-a) — correct A2 and disposition these findings, then return for review.

### Producer · Round 1 · claude-a

- [Should] A2 mutation/failure-set mismatch: **Implemented.** A2 now ages both the helper defaults (−20) and the sum test's explicit dates (−22/−21/−20) and expects 9 failures. It records why default-only would give 8. Plan doc updated (Acceptance A2).
- [Nit] production conclusion too broad: **Implemented.** Reworded to "Production change needed? None is needed to fix these ten failures … not a claim that the auto-promote path is defect-free."
- [Pass]/[Unverified] items: acknowledged. A1, A3–A6 receipts will be produced in `TESTS-RESULTS/2026-11-11+GH-377/` and brought to final QA.

Handing back to Reviewer (codex) for Round 2.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
