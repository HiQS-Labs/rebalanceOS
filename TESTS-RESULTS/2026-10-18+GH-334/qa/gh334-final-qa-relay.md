# RELAY · rebalanceOS GH-334 git-pulse-sync-repair final QA (codex)
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
6. **Commit only the relay file** (`relay(rebalanceos-gh-334-git-pulse-sync-repair-final-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh334-final-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-18

### Artifact — gh334-final-brief.md
```
# Final QA: RebalanceOS GH-334 git-pulse-sync-repair (implementation)

Your worktree is HiQS-Labs/rebalanceOS at branch `feat/rebalanceOS-gh334-git-pulse-sync-repair-2026-10-18`, head cf2c07d. The diff against `origin/development` (830a7d6):
- `experimental/git-pulse/git-pulse-sync-repair/SKILL.md` (new)
- `SOP.md` (the GH-334 exception paragraph after the GH-325 rollback rule)
- `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md`, promoted from 1-INBOX (the approved plan)
- the `ROADMAP.md` entry
- `TESTS-RESULTS/2026-10-18+GH-334/` (smoke logs, `SUMMARY.md`, `provenance.jsonl`, the plan-QA relay)

The approved plan is the spec: plan QA was attested against b246a70.

Operational envelope: a single-operator, per-device agent skill, which is a procedure document with no code. Grade it at commensurate complexity. Do not ask for new code, suites or daemons. The operator decisions are fixed (repair + resync, location, the stuck-rebase abort exception, install after merge via Skills Army HQ).

Questions:
1. **Fidelity.** Does `SKILL.md` implement the approved plan's procedure exactly? Check steps 0–4, the 2.1 `load -w` versus `stack.sh install` split, the 2.2 `set-pulse` path, 2.3 no enrollment, the 2.4 a–f order, step 3's fleet render → deliver order, the baseline-before-kickstart completion rule, and step 4 with one recheck and no loops. Name any drift.
2. **Commands.** Are the commands copyable and correct as written? Check the lock wrapper (`export PULSE G`, `bash -c` steps), `rev-list --left-right --count @{u}...HEAD` (which is behind then ahead), the PlistBuddy/plist push-policy check, and `launchctl print`/`kickstart` targets. Cite `file:line` for anything wrong.
3. **Safety.** Do the SOP exception and the skill agree exactly on the four prerequisites? Is every other in-progress operation still preserved for its owner? Is anything in the skill able to reset, stash, discard, loop, guess, or touch another clone?
4. **Evidence.** Do the smoke logs support the `SUMMARY.md` claims? Check the red controls for a held lock, a live owner and a merge in progress, plus the main recovery. Are the limits stated honestly: no live repair run, completion attribution not runtime-qualified?
5. **Scope.** Is there anything extra (new scripts, jobs, code) or missing against #334? Does the description stay under 1024 characters?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change needs `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: `SKILL.md` implements the approved plan faithfully and safely, the commands are correct, the evidence supports the claims, and there is no Blocker or Should.

Reviewer block: plain lines; `VERDICT: PASS` or `VERDICT: FAIL` and `Basis:` each at the start of a line. On PASS set `STATUS: Approved`.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
