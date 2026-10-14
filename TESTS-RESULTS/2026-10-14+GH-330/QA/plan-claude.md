# RELAY · GH330 current-base plan confirmation
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-14.
-->

NEXT: Producer
STATUS: Approved
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
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh330-current-base-plan-confirmation): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: PROJECT/2-WORKING/GH-330-FLEET-SAFETY-FOLLOWUP.md, PROJECT/2-WORKING/recon-gh325-review-followup.md, TESTS-RESULTS/2026-10-14+GH-325
- Reviewer: claude   ·   Producer: codex-supervisor
- Started: 2026-10-14
- Definition of Done: Current-base plan is grounded, surgical, DRY, with falsifiable preservation/lock checks and truthful ratings; user authorized a follow-up PR after326 merged. Local developer CLI envelope; no enterprise transaction framework or live enrollment.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Questions
1. Does the new base/intake change any material assumptions of the already approved safety plan? Relevant runtime modules are identical to8ff740b; preserved implementation will be ported after this approval.
2. Are strict admission, complete mode-preserving first backup, timezone validation and explicit partial-error recovery sufficient and commensurate?
3. Is the existing locked refresh helper facade the smallest safe setup path? Are retirement reader migration and existing fixture path portability appropriately scoped?
4. Do rating88/88/50/65, rollback limits and verification obligations match the evidence? No frequency or deployed-health claim.

On PASS: set STATUS Approved, NEXT Producer; DO NOT release the tick token. Keep the reviewer claim and run the exact environment-pinned native tick done command supplied by the harness. NEXT Producer is a document field, not a request to release the claim. Only relay thread writes; no tests in relay worktree.

## Log

### Reviewer (claude) — r1

swept file: yes

**VERDICT: PASS**
**Basis:** Plan is grounded in the recon seam table and SUMMARY.md evidence; surgical (extends existing helpers, no new stores); DRY (reuses reconcile_pulse_mirror, set_collector_values, _read_config, timezone resolver); ratings are truthful and bounded; scoping is appropriate for local developer CLI envelope.

**Q1 — Base change vs. prior assumptions:**
[Pass] Plan states "runtime modules are identical between old baseline 8ff740b and current development 1a496fa" (GH-330-FLEET-SAFETY-FOLLOWUP.md line 36). SUMMARY.md confirms no competing plan and module identity unchanged. No material assumption change.

**Q2 — Strict admission / backup / timezone / partial-error recovery:**
[Pass] Four safety properties map directly to recon seams A–D (recon-gh325-review-followup.md lines 32–38). Concurrent-writer and ACL unknowns are explicitly excluded in both plan (line 41) and recon unknowns table (lines 63–68). Scope is commensurate.

**Q3 — Locked refresh facade + retirement scoping:**
[Pass] Step 5 wraps existing reconcile_pulse_mirror (plan line 52); "no direct pull/autostash" stated. Retirement requires operator gate before deletion (recon line 65; plan line 53). Fixture space issue scoped narrowly to "if reproduced" (plan line 54). ✓

**Q4 — Ratings, rollback limits, verification obligations:**
[Pass] 88/88 justified by reproduced config loss and private mode exposure (plan line 43–44). Appeal 50 neutral stated. Cheapness 65 justified by "bounded existing helpers" (plan line 44). Rollback honest: "Revert code without automatic configuration rollback; inspect existing backups manually" (plan line 41). Verification uses existing focused suites, no new suite (plan lines 54–58). No frequency or deployed-health claim present.

**Pre-existing defects sweep:**
No pre-existing defects found in the artifact. Version bump 0.101.1 (plan line 53) is consistent with current 0.101.0 base (SUMMARY.md line 19). "Shadow setup 42 must stop 42 without setter" (plan line 52) is internally consistent with described fixture coverage. Rating owner chain (Releases CLI → ROADMAP shadow) matches recon contracts section (recon line 52).

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
