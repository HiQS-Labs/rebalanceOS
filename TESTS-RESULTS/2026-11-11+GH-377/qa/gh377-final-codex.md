# RELAY · gh377-final-codex
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
6. **Commit only the relay file** (`relay(gh377-final-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: the implementation diff from base 88a8972 to HEAD on this branch, specifically `tests/test_auto_promote.py`, `tests/test_project_inference.py` and `tests/conftest.py`, plus the plan `PROJECT/2-WORKING/GH-377-AUTO-PROMOTE-FIXTURE-AGING.md` (Approved in `TESTS-RESULTS/2026-11-11+GH-377/qa/gh377-plan-codex.md`) and the campaign `TESTS-RESULTS/2026-11-11+GH-377/` (its SUMMARY, witnesses, root-tests, smoke, static-gates, identity and provenance receipts and the witness script).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-11-11
- Definition of Done: plan acceptance A1–A5 are substantiated by the retained receipts (A6, hosted CI, is verified after the PR opens). The code matches the approved plan with no production change, no new test/suite and no conftest machinery added. KNOWN_FAILING_GH178 is empty and its helper is intact. The rating 70/55/50/85 still matches the evidence.

**Operational envelope:** a test-only fix in a single-repo Python suite. Grade against stated acceptance and commensurate complexity. No freezegun/libfaketime, no production refactor, no new suites.

### Questions
1. Do the three test-file changes implement exactly plan steps 1–3? Is any fixed date left that can still age out (`grep 2026-` in `tests/test_auto_promote.py`)? Is the remaining fixed date in `test_project_inference` covered by the freeze for every window it crosses (`_load_calendar_events`, `_seed_status`)?
2. Is the `_days_ago` / `None`-default pattern correct? Does `committed_at or …` / `scan_date or …` change any test that passes an explicit value? Is there a UTC-midnight race between Python `datetime.now(timezone.utc)` and SQLite `date('now')` at −1 day?
3. Is the `mock.patch("rebalance.ingest.project_inference.now_utc", …)` target correct (module-bound import, `project_inference.py:11`)? Does it leak beyond the `with` block?
4. Do the receipts substantiate A1–A5? Check the witness script's mutations actually hit the intended sites ("mutated sites" counts), that A2's failure set is exactly the 9 IDs, and that base failures equal the 10 GH-178 IDs.
5. Is skipping a version bump consistent with repo precedent (#243, test-only) and with AGENTS.md § Versioning? Is skipping `rebalance doctor` justified for a tests-only diff?
6. Anything over-built, missing, or a duplicate subsystem/writer?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns. Plain blank separators may be added or removed between sections; preserve every substantive line, indentation, and fenced/literal blank line. A historical FAIL→PASS edit or changed fenced example is forbidden.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
