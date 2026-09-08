# RELAY · GH199 CLIO first-prompt final review
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-08.
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
6. **Producer commits only the relay file** (`relay(gh199-final-review): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `utils/CLIO/clio-codex-tail.sh`, `test/clio-codex-tail.sh`, `utils/CLIO/INSTALL.md`, `PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md`, `TESTS-RESULTS/2026-09-08+GH-199/`, and the GH-199 CHANGELOG/version/roadmap delta.
- Reviewer: codex · Producer: claude-a
- Started: 2026-09-08
- Definition of Done: Final implementation QA for canonical RebalanceOS GH-199. Read the full touched runtime, test and install files, the approved plan and retained test receipts. Evaluate first-discovery capture, full-precision eligibility on every chunk, original-file child provenance, genuine root resumes, legacy retries versus reset, source read-only and existing writer acceptance/dedup. Require nonempty positive controls and witnessed-red counter-controls. Identify correctness regressions with file:line evidence; keep unrelated feature work outside this producer repair.
- Gate reporting: the broader baseline already failed the scheduled-runtime-root test, and doctor did not finish. Compare candidate receipts to baseline; do not mistake focused-suite success for overall merge readiness. A draft canonical PR must disclose unresolved broader gates. Approval here is code-review approval only, never deployment/backfill or merge authorization.
- Containment: only this relay thread may be written. Do not run source scripts, installed hooks, broad suites or git mutations. Read retained evidence and source. No product files may be edited. The producer will commit this thread.
- OUTPUT CONTRACT: append one `### Reviewer — codex — Round 1` block with literal `VERDICT: PASS` (approved), `VERDICT: FAIL` (changes required), or `VERDICT: PARKED` (cannot decide), a nonempty `Basis:` paragraph and `swept file: yes` or `swept file: no`. Cite each material finding. Set top-level `STATUS: Approved` and `NEXT: none` only on approval; otherwise `STATUS: Open` and `NEXT: Producer`. Preserve previous blocks. End with an explicit handoff. These exact labels are required by the harness.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). The producer commits the thread; reviewer appends only, no git commands.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
