# RELAY · rebalanceOS PR #335 GH-334 independent QA (GLM 5.3 max)
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
6. **Commit only the relay file** (`relay(rebalanceos-pr-335-gh-334-independent-qa-glm-5-3-max): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh334-glm-brief.md** (embedded below — read it here).
- Reviewer: commandcode   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh334-glm-brief.md
```
# Independent QA (GLM 5.3): RebalanceOS PR #335 / GH-334 git-pulse-sync-repair

You are a third-family reviewer. Codex approved the plan and an earlier implementation. Agy approved the current one after finding a real bug in round 1: the skill diagnosed the dev clone, but this Mac's scheduled jobs run from `~/rebalance-runtime` in fleet mode. That bug was fixed in 864ff96. Look for what both missed.

Your worktree is HiQS-Labs/rebalanceOS at PR #335's head (0765c30). The diff against `origin/development` is:
- `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`: the new skill, a procedure document with no code (138 lines)
- `SOP.md`: the "GH-334 exception: aborting a stuck pulse rebase" paragraph, after the GH-325 rollback rule
- `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md`: the approved plan, which is the spec
- `ROADMAP.md`: one entry
- `TESTS-RESULTS/2026-10-18+GH-334/`: smoke logs, `SUMMARY.md`, provenance, and the plan, final and agy QA relays

Operational envelope: a single operator's per-device agent skill, run on their own Macs. Grade at commensurate complexity. Do not ask for new code, suites, daemons or enterprise hardening. The repo forbids new scripts and LaunchAgents (GH-241); the doctor is read-only.

Operator decisions are fixed:
- the skill may repair and then resync
- location `experimental/git-pulse/`
- a stuck rebase may be aborted after verified backups (the SOP exception)
- install after merge via the Skills Army HQ CLI
- RebalanceOS is on every device

Read alongside the skill:
- `src/rebalance/doctor.py` (pulse, pulse fleet and scheduler rows)
- `src/rebalance/ingest/config.py` (how `temp/rbos.config` is resolved)
- `src/rebalance/ingest/pulse.py` (publish, lock, push=False in fleet mode)
- `src/rebalance/lib/git_ops.py` (`git_pull_rebase_safe`, `_cleanup_failed_rebase`)
- `src/rebalance/cli/config_cmds.py` (`set-pulse`, `fleet-enroll`, `refresh-pulse-clone`)
- `scripts/stack.sh`, `scripts/pulse_sync.sh`, `scripts/com.rebalance-os.pulse-sync.plist.template`
- `experimental/git-pulse/collect.sh`, `experimental/git-pulse/com.user.git-pulse.plist.template`
- UPGRADE.md "Fleet self-repair", SCHEDULER.md

Questions:
1. **Does the 864ff96 fix hold?** Step 0 now resolves `RB` from `$REBALANCE_ROOT`, then `~/.config/rebalance/runtime-root`, then the clone with `.venv/bin/rebalance`, and checks it against the plist `ProgramArguments`. FLEET falls back to `pulse_fleet_enabled` in `$RB/temp/rbos.config`. Walk this Mac's state through it: runtime root `~/rebalance-runtime` (11 commits behind development, pre-GH-325, so its doctor has no `pulse fleet` row), `pulse_fleet_enabled: true`, `fleet_mode=true`, both `com.rebalance-os.pulse-sync` and `com.user.git-pulse` installed but not loaded, pulse clone 85 behind / 11 ahead, clean tree. Does every step choose the right action, in the right clone, in the right order?
2. **Copy-paste correctness.** Check every shell line: quoting of paths with spaces, `$RB`/`$PULSE`/`$G` resolution, the PlistBuddy key path against the real plist, `launchctl print`/`kickstart`/`load -w` target syntax, the step 2.4 flock wrapper and how variables cross into `bash -c`, and the Step 3 baseline (log paths, `runs = N`, byte sizes). Cite `file:line` for any line that fails as written.
3. **Safety.** Can any step lose local commits or uncommitted work, race the hourly job, or leave the device worse than it started? Is the stuck-rebase procedure (lock, lsof, re-read, two verified backup branches, patch, abort) complete, and does it stop on everything outside a conflicted rebase?
4. **Doc agreement.** Do `SKILL.md`, the plan, the SOP exception and the SUMMARY agree with each other and with the doctor's own hints?
5. **Over or under-built.** What could be cut, and is anything GH-334 asks for missing?

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
