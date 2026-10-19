# RELAY · rebalanceOS GH-334 git-pulse-sync-repair plan QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-18.
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
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh334-plan-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh334-plan-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-18

### Artifact — gh334-plan-brief.md
```
# Plan QA: RebalanceOS GH-334 git-pulse-sync-repair skill

You are reviewing a PLAN, not code. The target repo is HiQS-Labs/rebalanceOS. Your worktree is that repo at branch `feat/rebalanceOS-gh334-git-pulse-sync-repair-2026-10-18` (head 84307c8).

Read in full: `PROJECT/1-INBOX/GH-334-GIT-PULSE-SYNC-REPAIR.md` (the plan).

Then verify its claims against:
- `src/rebalance/doctor.py`: the scheduler liveness check near line 767, the hints at 842-848, `_check_pulse` at 2155, `_check_pulse_fleet` at 2201, `_check_pulse_collectors` at 1885
- `scripts/stack.sh` (install/up and its preflight, near 599)
- `scripts/com.rebalance-os.pulse-sync.plist.template` and `scripts/pulse_sync.sh`
- `src/rebalance/cli/config_cmds.py`: `refresh-pulse-clone` at 482, `fleet-enroll` at 522
- `src/rebalance/lib/git_ops.py` 570-640
- `experimental/git-pulse/collect.sh` 230-262
- UPGRADE.md "Fleet self-repair" (185-216)
- SOP.md around line 358
- SCHEDULER.md 170-185
- ROUTER.md 51-65 (GH-241 no new scripts)
- AGENTS.md 212-255

Operational envelope: a single-operator, per-device agent skill (a `SKILL.md` procedure) for one person's Macs. Grade against the stated operator decisions at commensurate complexity. Do not ask for new code, daemons, test frameworks or enterprise hardening.

Operator decisions are fixed; do not re-litigate them:
- repair + resync authority
- location `experimental/git-pulse/`
- abort a stuck rebase after a backup branch, with an SOP exception
- install after merge via the Skills Army HQ CLI

Questions:
1. **Grounding.** Is every command in the procedure real, with the stated behavior? In particular, does `bash scripts/stack.sh install pulse-sync` load an installed-but-unloaded job? Is `launchctl kickstart gui/$(id -u)/com.rebalance-os.pulse-sync` the right way to run the scheduled job once (label, domain)? Are the log paths right?
2. **Fleet versus non-fleet.** Is the resync step right in both modes: which job pushes, and when does `refresh-pulse-clone` apply? Is anything missing for a non-enrolled Mac like this one?
3. **Stuck-rebase exception.** Are the backup refs right (`rebase-merge/orig-head` versus `rebase-apply/orig-head`, plus the current HEAD)? Is the abort safe? After the abort, does the publisher's own lock (`<gitdir>/rebalance-publish.lock`) or a live rebase process need checking first, so the skill does not abort a rebase the publisher is running right now?
4. **Bounds.** Is the one-attempt / one-recheck / stop contract complete? Can any step loop, guess values, or touch other clones?
5. **Scope.** Is anything over-built or missing against issue #334? Is the SOP edit placed and scoped right?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: the plan is grounded in real commands and paths, safe within the operator's decisions, and bounded. No Blocker.

### Reviewer block template (copy exactly; `VERDICT:` and `Basis:` each start at the beginning of a line)

```
### Round N — Reviewer (codex)
Findings:
- [Severity] file:line — finding
  Observed input: ...
  Affected scope: ...
  Falsifier: ...
Answers: 1) ... 2) ... 3) ... 4) ... 5) ...
VERDICT: PASS
Basis: <one line>
```
Use `VERDICT: CHANGES` if there is any Blocker or Should; otherwise PASS and set `STATUS: Approved`.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
