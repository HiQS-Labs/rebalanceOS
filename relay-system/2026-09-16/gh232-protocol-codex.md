# RELAY · GH-232 protocol fallback review
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-16.
-->

NEXT: Producer
STATUS: Escalated
ROUND: 1 / 1

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
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh-232-protocol-fallback-review): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/GH-232-CLIO-JOURNEY-FOLLOWUP.md** — the read-only path that
  `relay-drive.sh --artifact-file PROJECT/2-WORKING/GH-232-CLIO-JOURNEY-FOLLOWUP.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: codex   ·   Producer: coordinator
- Started: 2026-09-16
- Definition of Done: The frozen diagnostic protocol has explicit pass/fail criteria, privacy
  boundaries, positive and negative controls, and no accuracy claim from assistant labels.
  Read the artifact and tests/test_journey_replay.py only. Do not inspect private/ignored files.
  Answer: are the fixed-input controls and two-pass cap adequate; does the step-four fallback
  avoid forcing a false success; is the scope minimal? Cite findings and write VERDICT: PASS
  or FAIL with Basis. No tests or code edits needed. Agy timed out without a review; this is
  the one bounded fallback, not approval inherited from an earlier plan.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer — codex — round 1 — 2026-09-16

swept file: yes

- [Blocker] Unresolved additions have no explicit fail disposition: the protocol requires inspecting “unresolved/wrong additions” but only states that a “known-good loss or wrong new association blocks progression” (.relay-artifacts/GH-232-CLIO-JOURNEY-FOLLOWUP.md:54–59). An inspected but unresolved association could therefore pass the gate. Concrete fix: state that any unresolved addition also blocks progression and routes step four to the failure report; require every changed reference, including the prior 24 cases, to have a recorded disposition before declaring the gate passed.
- [Pass] Fixed-input controls are adequate for this bounded diagnostic scope: baseline/cutoff, capture hash, start decisions, membership and coverage are frozen, with parent changes reported separately (artifact:47–50). Synthetic cases cover foreign context, planned ordinals, formatted PRs and deduplication (tests/test_journey_replay.py:72–101); mutation and deliberately broken join controls are present (tests/test_journey_replay.py:61–69,135–143). These are source-review findings; tests were not executed. Preserve these controls and input invariants.
- [Pass] Two narrow repair passes and a two-hour total cap bound the work; the step-four fallback explicitly says “a failure report with a narrower next proposal, not a forced reconstruction” (artifact:57–59). Preserve that fallback and apply it to the unresolved-addition condition above.
- [Pass] Privacy and inference boundaries are explicit: “Raw prompts and reviewer-only source excerpts stay in private ignored scratch, never in QA packets” (artifact:51–52), and assistant inspection is diagnostic with no accuracy/generalization or statistical claim (artifact:60–61). Preserve these boundaries.
- [Pass] Scope is minimal: only reference extraction changes, with no source capture changes, new collector, unguarded model calls, merge or deployment (artifact:40–43,63–64); blocked application gates prohibit readiness claims (artifact:73–77). Preserve that scope. The whole artifact and test file were swept; no additional pre-existing defects were identified within the permitted review surface.

VERDICT: FAIL
Basis: The controls, cap, privacy boundaries and conditional fallback satisfy the bounded diagnostic intent, but the reference gate must explicitly fail on unresolved additions before progression can be approved. This is an independent fallback review, not inherited approval. Only the artifact and tests/test_journey_replay.py were read for substantive review; no tests, private-file inspection or artifact edits were performed.

Handing off to Producer (coordinator) — resolve the blocker and obtain a fresh review; the one-round relay is Escalated.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
