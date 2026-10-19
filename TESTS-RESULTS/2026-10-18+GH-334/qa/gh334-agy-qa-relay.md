# RELAY · rebalanceOS PR #335 GH-334 independent QA (agy)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
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
6. **Commit only the relay file** (`relay(rebalanceos-pr-335-gh-334-independent-qa-agy): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh334-agy-brief.md** (embedded below — read it here).
- Reviewer: agy   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh334-agy-brief.md
```
# Independent QA (agy): RebalanceOS PR #335 / GH-334 git-pulse-sync-repair

You are a second-family reviewer. Codex approved both the plan and the implementation. Look for what a different reviewer misses.

Your worktree is HiQS-Labs/rebalanceOS at PR #335's head (475f2e2). The diff against `origin/development` is:
- `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`: the new skill, a procedure document with no code
- `SOP.md`: the GH-334 stuck-rebase exception paragraph, after the GH-325 rollback rule
- `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md`: the approved plan, which is the spec
- `ROADMAP.md`: one entry
- `TESTS-RESULTS/2026-10-18+GH-334/`: smoke logs, `SUMMARY.md`, provenance, and the plan and final QA relays

Operational envelope: a single operator's per-device agent skill, run on their own Macs. Grade at commensurate complexity. Do not ask for new code, suites, daemons or enterprise hardening.

Operator decisions are fixed:
- authority to repair and resync
- location `experimental/git-pulse/`
- a stuck rebase may be aborted after verified backups (an SOP exception)
- install after merge via the Skills Army HQ CLI
- RebalanceOS is on every device

Read alongside the skill:
- `src/rebalance/doctor.py` (around 767-848, 1885, 2155-2230)
- `scripts/stack.sh`
- `scripts/pulse_sync.sh`
- `scripts/com.rebalance-os.pulse-sync.plist.template`
- `experimental/git-pulse/com.user.git-pulse.plist.template`
- `experimental/git-pulse/collect.sh` (230-262, 391-410)
- `src/rebalance/lib/git_ops.py` (272-290, 570-640)
- `src/rebalance/cli/config_cmds.py` (482-560)
- UPGRADE.md "Fleet self-repair"
- SCHEDULER.md 170-185

Questions:
1. **Would it work on a real Mac, end to end?** Walk this Mac's actual state through the skill: scheduler installed but not loaded, `pulse` configured, fleet not enrolled, clean tree, 39 behind / 10 ahead, `PULSE_PUSH` unset. Does every step produce the right action? In particular, after `launchctl load -w`, does `kickstart` of a job with `RunAtLoad` false actually run it? Does the off-fleet pulse-sync push rebase over 39 upstream commits safely through `git_pull_rebase_safe`?
2. **Copy-paste correctness.** Check each shell line in SKILL.md: quoting, `$G` resolution, `@{u}` with no upstream configured, the PlistBuddy key path versus the real plist structure, `launchctl print`/`kickstart` target syntax, and how the step 2.4 `bash -c` wrapper receives `R`/`S` across steps b–f. Cite `file:line` for any line that would fail as written.
3. **Safety gaps.**
   - Can any step lose local commits or uncommitted work, or race the hourly job?
   - Is the 10-minute observation window right for a job capped at 1800 s (`job_guard --max-runtime-seconds 1800`)?
   - Is anything missing that could leave the device worse than it started?
4. **Doc agreement.** Do `SKILL.md`, the plan and the SOP exception agree with each other, and with doctor's own hints?
5. **Over or under-built.** What could be cut, and is anything that #334 asks for missing?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines. You may run narrow read-only probes; quote the command and its output.
```
- Definition of Done: the skill would work as written on a real Mac within the operator's decisions; no Blocker or Should.

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
