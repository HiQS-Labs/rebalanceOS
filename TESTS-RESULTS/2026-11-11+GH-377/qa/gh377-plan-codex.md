# RELAY · gh377-plan-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-11-11.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 1 / 3

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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
