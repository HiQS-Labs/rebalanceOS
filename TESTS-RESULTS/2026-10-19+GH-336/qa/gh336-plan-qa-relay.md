# RELAY · rebalanceOS GH-336 plan QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 1 / 2

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
6. **Commit only the relay file** (`relay(rebalanceos-gh-336-plan-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh336-plan-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh336-plan-brief.md
```
# Plan QA (Codex): RebalanceOS GH-336, binary-safe stuck-rebase backup

Review the plan `PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md` before any implementation. Your worktree is HiQS-Labs/rebalanceOS on `fix/rebalanceOS-gh336-binary-safe-rebase-backup-2026-10-19` (the intake commit on top of development e5a42ed).

Read in full:
- the plan above
- `experimental/git-pulse/git-pulse-sync-repair/SKILL.md` (step 2.4, lines 80-105)
- `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md` (step (e), line 95)
- `SOP.md`, the "GH-334 exception" paragraph
- issue https://github.com/HiQS-Labs/rebalanceOS/issues/336

Operational envelope: one operator's per-device agent skill, which is a procedure document with no code. The pulse repo tracks 327 files and 0 binaries, has no LFS and no submodules. The operator wants this bounded: no backup redesign, no new scripts, tests or daemons. The repo forbids new scripts and LaunchAgents (GH-241), and verification is a manual smoke recorded under `TESTS-RESULTS/`.

Questions:
1. **Correctness of the fix.** Does `git diff --binary HEAD`, taken during a conflicted rebase, capture every tracked edit that `rebase --abort` would discard? That covers staged and unstaged edits, and unmerged paths in text and binary files. Is the restore hint (a detached worktree at the `-head` backup, then `git apply <patch>`) right? Name any tracked-edit case it misses, such as mode changes, deletions or renames, with a concrete input.
2. **The stricter check.** Is "patch non-empty when `git diff HEAD` is non-empty, and no `Binary files … differ` line" the right verification, and sufficient? Is there a simpler or more exact check?
3. **Scope.** Is the GLM Nit fold-in (bare `rebalance` → `"$RB/.venv/bin/rebalance"`, a step 0 mismatch action, the 2.1 load-triggered-run note) reasonable in this PR, or should it be split out? Is anything else required to keep the SKILL, the GH-334 plan and the SOP consistent?
4. **Verification.** Do the smoke, the red control and the adjacent path actually prove the fix and detect the old failure? Is the post-merge redeploy step (Skills Army HQ `intake.py update` + `sync.py`) correct and sufficient?
5. **Bounding.** Are the timebox, the pivots and the stop rules sound? Is anything over- or under-built for a one-flag fix?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines. You may run narrow read-only probes in a scratch git repo under `.relay-scratch/`; quote the command and its output.
```
- Definition of Done: the plan is correct, bounded and sufficient to fix #336 as a wording change; no Blocker or Should.

Reviewer block: plain lines; `VERDICT: PASS` or `VERDICT: FAIL` and `Basis:` each at the start of a line, with no bold. On PASS set `STATUS: Approved`.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
