# RELAY · GH-196 shutdown plan completeness
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-07.
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
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **Verdict**
     (Approved | Changes requested | Blocked). **Review the whole file, not just the diff** (GH-268):
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
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh196-shutdown-completeness): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md`
- Reviewer: agy   ·   Producer: codex
- Started: 2026-09-07
- Definition of Done: Dedicated requirements-completeness review of a not-yet-implemented MVP execution plan; identify every user ask without an equivalent in the target, not a summary of the plan. A separate subsequent turn will review feasibility/safety in depth.
- Handoff: cli-driven (agy), via shipped relay-xyz, review-only ALLOW_PATHS.

### Source requirements — omission-diff against every item

1. Skill named shutdown, originally requested in XYZ Forge, now operator considering/asking for its plan in RebalanceOS alongside daily to reuse existing machinery and folder structure.
2. Activity within existing repos (CRUD), NOT repo/clone creation dates. Today, yesterday, and a recommended configurable cutoff.
3. All locally discovered repos with such activity, including dirty checkouts, worktrees and full clones; no hardcoded shortlist of favorite repos.
4. First report/review/triage; offer optional execution at the end, with user choice.
5. Reuse merge-cleanup for reports, PR sequencing, merges and safe retirement, not a competing cleanup engine.
6. Preserve cross-repo/agent continuity so the user need not reconstruct yesterday from chats.
7. Tomorrow's brief is a nudge toward finishing an unfinished part/phase of a longer arc; merging a phase PR is not the whole project finishing.
8. A PR intentionally not merged tonight carries a reminder to test, gather feedback/review, and merge when ready; preserve the reason for holding.
9. Interact conversationally through VS Code, Codex, Gemini/Agy, or ZCode, including while working in XYZ Forge.
10. Mostly self-contained basic repo scan -> end-of-day synthesis; no Rebalance runtime required for basic mode.
11. Optional configured Rebalance runtime/DB enrichment, machine-local config in temp, reuse already collected data; do not invent a second data pipeline.
12. Two-pass activity check; if second pass reveals ongoing activity, state that and leave the repo out of shutdown candidates.
13. MVP: an incremental useful improvement, not a perfect/general system. User explicitly discourages overengineering.
14. Inspect prior daily skill/output, even when few cycles ran today; retain useful handoff when daily wasn't run.
15. Current authorization: write execution plan into RebalanceOS GitHub issue, Agy relay QA; NOT implementation/deployment/live cleanup.

### Questions and output

1. For each of 15 source requirements, name its equivalent section/line in the plan, or the exact missing/changed requirement. An implicit promise is a gap.
2. Did source-to-plan translation silently add prerequisites or authority (especially paired-skill install, output location, optional execution, active detection)? Explain whether additions are reasonable MVP assumptions or require operator choice.
3. Is any must-have left out of the acceptance matrix? Cite the cheapest plan correction, not speculative features.

Read the ENTIRE plan. Append one Reviewer block, `swept file: yes`, Basis: textual only (plan review, not code executed), concrete file:line citations, and a literal standalone `VERDICT: PASS` / `VERDICT: FAIL` / `VERDICT: PARKED` matching your human verdict. Approved/PASS closes this completeness thread only, not the project or implementation QA. Do not edit the plan, run tests/refresh/DB queries, or push. The supervising shim handles token/commit. Report omissions even if other sections sound convincing.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
