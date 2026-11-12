# RELAY · gh377-final-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-11-11.
-->

NEXT: Producer
STATUS: Approved
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
- Definition of Done: plan acceptance A1–A5 are substantiated by the retained receipts (A6, hosted CI, is verified after the PR opens). The code matches the approved plan with no production change, no new test/suite and no conftest machinery added. KNOWN_FAILING_GH178 is empty and its helper is intact. The rating 70/55/50/85 still matches the evidence.  [Unverified — no citation]

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

### Reviewer · Round 1 · codex

swept file: yes

Reviewed the whole three test files, approved plan, campaign summary, witness script and all listed receipts; traced the calendar clock/status consumers. No additional pre-existing functional defect requiring a test-file change was identified. This is source/receipt review, not an independent suite execution or an independently reconstructed base diff (git is prohibited in this seat).

- [Pass] **Fixture implementation matches steps 1–3.** `tests/test_auto_promote.py:29–38,41–42,57–64,127–137` supplies UTC-relative defaults and all three explicit sum dates; no fixed `2026-` date remains in that file. All current callers supply either omitted values or nonempty explicit dates, so `or` does not change an existing explicit-value case. Yesterday remains inside the inclusive 14-day window across UTC midnight; it does not require Python and SQLite to sample the same date. Keep this bounded approach.
- [Pass] **Freeze covers both consumers and is scoped.** `tests/test_project_inference.py:143–152` patches the module-bound import at `src/rebalance/ingest/project_inference.py:11`; calendar loading at line 240 and `_seed_status` at line 468 both execute inside that context. The April 17/24 inputs (test lines 118–131) remain in-window. Other fixed dates in the file support GitHub-only assertions without a calendar seed requirement. The context manager restores the binding afterward. `tests/conftest.py:105,138–139` leaves an empty quarantine and existing expiry machinery intact.
- [Pass] **Retained receipts substantiate A1–A5 at the stated scope.** `witnesses.txt` reports “mutated sites: 5”, “9 failed, 7 passed”, then “16 passed”; its nine A2 failure IDs equal the auto-promote subset of A1. The witness script targets both defaults and three explicit sum sites. A3 mutations each report one site and one failure, followed by restoration passing; the appended assertion excerpt is “'BetaReport' not found in ['Acme']”. A4 reports “KNOWN_FAILING_GH178 = set()” and four helper passes. `root-tests.txt` lists exactly the same ten base failure IDs and “2849 passed”/“exit=0” for the fix. These are retained producer receipts, not reruns by this reviewer.
- [Should] **Resolve the version-policy conflict before closeout.** Setup question 5 proposes skipping a bump because this is test-only, but `AGENTS.md:217–219` requires a bump for “Every fix or feature” and exempts documentation-only changes. Historical #243 precedent alone does not establish an exception to that current instruction. Cheapest fix: apply the normal patch bump/changelog at commit/merge, or cite an explicit applicable operator authorization/policy exception in the existing task doc. No production behavior change is requested.
  Observed input: this fixture bugfix changes executable test code, while Setup question 5 explicitly asks whether skipping its bump is consistent.
  Affected scope: GH-377 release metadata and its claimed policy compliance only.
  Falsifier: an explicit applicable instruction exempting test-only fixes would make a bump unnecessary; cite it and retain the test-only scope.
- [Should] **Finish the campaign's validity disclosure.** `SOP.md` §4.1 requires every SUMMARY to end with threats to validity and deviations. The current SUMMARY ends with the doctor omission and has no such disclosure. Append a short paragraph covering the local Python 3.13.15 run, 21 skipped tests, pending hosted 3.12/3.13 evidence, filtered rather than complete witness output, and any deviations; do not imply all environments or skipped paths were measured. This is a documentation correction, not a request for another suite.
  Observed input: `SUMMARY.md` ends “the live runtime, DB or scheduler that doctor inspects”; `root-tests.txt` reports “21 skipped” and A6 remains pending.
  Affected scope: interpretation of this campaign's A1–A5 evidence.
  Falsifier: an existing final validity section explicitly covering those limits would satisfy the requirement; none appears in the supplied summary.
- [Pass] **Scope remains proportionate.** The plan's “no production code change” and “no new tests, suites or conftest machinery” match the reviewed fixture approach. The summary's doctor omission is reasonable for that scope. The 70/55/50/85 rating remains a prioritization judgment supported by the plan's CI-impact and three-file effort rationale, not a measured product metric. Keep the small repair; no new subsystem is warranted.
- [Unverified — needs clone run] No pytest, executable fixtures, validation scripts or git commands ran this turn. Independent behavior execution remains the harness gate; A6 remains the explicitly deferred hosted PR check. The identity receipt brackets `ae11876…` with `dirty=0`, but this seat did not independently reconstruct the commit diff or re-fetch #243.

VERDICT: FAIL
Basis: The source and retained behavioral evidence support the fixture repair. Closeout still needs the explicit version-policy disposition and SOP-required validity disclosure; no additional functional change or new test is requested.

Handing off to Producer (claude-a) — disposition these two findings, then return for review. Go to the Producer window and say 'take your turn'.

### Producer · Round 1 · claude-a

- [Should] version-policy conflict: **Implemented.** AGENTS.md:217 ("Every fix or feature gets a version bump") is the current instruction; the #243 precedent does not override it. Patch bump 0.107.0 → 0.107.1 in `src/rebalance/__init__.py`, `manifest.json` and `pyproject.toml`, plus a dated `## [0.107.1]` CHANGELOG `### Fixed` entry in plain language (no paths or names, per AGENTS.md:220).
- [Should] SOP §4.1 validity disclosure: **Implemented.** `SUMMARY.md` now ends with "Threats to validity and deviations": environment (local 3.13.15 only, A6 pending), 21 skipped, mypy/doctor not run, filtered witness output, the remaining real-UTC coupling and its margin, and deviations (bump added in QA, A4 probe corrected once).
- No test or fixture code changed this round. Static gates rerun on the new head (see static-gates.txt).

Handing back to Reviewer (codex) for Round 2.

### Reviewer · Round 2 · codex

swept file: yes

Re-read the complete three test files, plan, witness script and retained campaign receipts, plus the release metadata added in response to R1. No additional pre-existing functional defect requiring a change was identified in the reviewed test files. This is source and receipt review; no git, suite, executable fixture or validation script ran in this seat.

- [Pass] **R1 version-policy finding resolved.** `src/rebalance/__init__.py:33`, `manifest.json:5` and `pyproject.toml:7` now carry `0.107.1`; CHANGELOG's quoted heading “## [0.107.1] - 2026-11-11” has a Fixed entry explaining the fixture aging and restored normal checks. This is the narrow release-metadata exception to the plan's no-production-change wording, with no runtime logic change requested.
- [Pass] **R1 validity-disclosure finding resolved.** `SUMMARY.md:21–27` now explicitly covers local Python 3.13.15, 21 skipped tests, pending hosted evidence, filtered output, residual clock coupling and deviations. The quoted deviation “final QA R1 added the patch bump” explains the scope adjustment.
- [Pass] **A1–A5 remain supported by retained producer receipts.** `witnesses.txt` retains “mutated sites: 5”, “9 failed, 7 passed”, “16 passed”, both single-site A3 failures and “KNOWN_FAILING_GH178 = set()”; `root-tests.txt` retains the same ten base failure IDs and “2849 passed, 21 skipped”. The witness script still targets both defaults and all three sum dates. The source conclusions and bounded rating rationale in R1 stand; no new machinery is warranted.
- [Pass] **Release metadata received targeted clone validation.** `static-gates.txt:23–25` records version-sync/dashboard tests with exit 0 and “3 passed”. Its header identifies head `98665a5`; the behavioral suite receipts remain tied to `ae11876`. The PDDA receipt at lines 20–22 is an observe-mode exit 0 with 26 diagnostics, not an assertion that those diagnostics were fixed.
- [Nit] **Some earlier summary wording predates the bump.** `SUMMARY.md:14,19` still says “no src/ change” and “touches only tests/”; lines 24 and 27 supply the accurate version-string exception. When preparing PR prose, describe the scope as test fixtures plus release metadata. This inconsistency does not invalidate the receipts or justify another relay cycle.
- [Unverified — needs clone run] Independent behavioral reruns and commit-diff reconstruction were not performed in this restricted reviewer seat. The harness gate remains responsible for its own execution; A6 remains pending on the hosted PR head (`SUMMARY.md:12`).

VERDICT: PASS
Basis: Both R1 Should findings are resolved. The reviewed source and retained receipts support A1–A5, with the release-metadata deviation and evidence limits disclosed. Approval is final QA for this artifact, not a claim that deferred hosted A6 has run.

Relay closed (Approved), no further turn needed.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
