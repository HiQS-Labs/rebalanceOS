# RELAY · rebalanceOS GH-334 git-pulse-sync-repair final QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-18.
-->

NEXT: Reviewer
STATUS: Open
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

### Reviewer · Round 1
swept file: yes

Reviewed the whole embedded brief, skill (all 129 lines), approved plan, SOP, roadmap entry, summary, provenance, smoke logs and retained recovery harness. SWE review, Verify tier with seeded-source fallback: no graph project matches this worktree. The nearest rebalanceOS graph is a different checkout, generation 2026-09-02T03:54:57Z; coverage reports changed metadata for git_ops.py, config_cmds.py and pulse.py. Relevant current source was read directly. No additional pre-existing defects found in the reviewed documents beyond the findings below. No Git commands, suites, executable fixtures, live repairs or scheduler mutations were run.

- [Should] SOP.md:369–370 contradicts the skill's qualified rebase exception. It unconditionally says “a dirty tree, or a detached HEAD still falls under the rule above: preserve it for its owner”. A conflicted rebase is itself dirty and normally detached; experimental/git-pulse/git-pulse-sync-repair/SKILL.md:92–93 correctly limits that refusal to states **outside this conflicted rebase**. Make the SOP use the same qualifier, retaining unconditional preservation for merges/cherry-picks/reverts. This clarifies the already approved authority rather than broadening it.
  Observed input: SOP.md:369 lists dirty/detached states without the outside-rebase qualifier. The published recovery input is a conflicted rebase with an uncommitted conflict edit (TESTS-RESULTS/2026-10-18+GH-334/smoke-rebase-recovery.sh.txt:10–11); smoke-rebase-recovery.log:10–15 records the intended authorized abort and saved edit. Read literally, the final SOP sentence prohibits that recovery.
  Affected scope: interpreting dirty/detached state inside a stuck rebase meeting all four prerequisites at SOP.md:364–367; all other states remain preserved.
  Falsifier: the SOP must permit the published MAIN recovery after all four prerequisites and still prohibit the published MERGE_HEAD control (smoke-rebase-recovery.log:16–19). An express exclusion of the qualified conflicted rebase from its preservation sentence would make this correction unnecessary; that qualifier is currently absent.
- [Nit] experimental/git-pulse/git-pulse-sync-repair/SKILL.md:85 — Quote the metadata path in `$(cat $R/orig-head)` as `$(cat "$R/orig-head")`. Unlike the surrounding quoted checkout paths, this expansion splits paths containing spaces. This is static shell review, not a reproduced recovery failure. The stop-on-failure rule limits the immediate consequence to stopping recovery; no new machinery is requested.
- [Pass] experimental/git-pulse/git-pulse-sync-repair/SKILL.md:24–64,69–90,97–129 — Plan fidelity is retained: doctor first, missing-key setter, load -w versus install, no automatic enrollment, ordered lock/live-owner/metadata/backups/patch/abort, fleet reconcile → render → deliver, baseline before kickstart, bounded observation and one recheck. `export PULSE G` supplies the bash child; the waiting Python parent retains its lock through subprocess completion. Shared-lock paths match src/rebalance/lib/git_ops.py:272–285 and experimental/git-pulse/collect.sh:391–410. Upstream on the left at skill line 40 makes the count behind then ahead. Loader hint and setter match src/rebalance/doctor.py:842–848 and src/rebalance/cli/config_cmds.py:499–519. No reset/stash, repeated repair loop or other-clone action is authorized (skill:17–20).
- [Pass] TESTS-RESULTS/2026-10-18+GH-334/SUMMARY.md:8–12 — Published logs support the stated observations: smoke-main-path.log:3–15 records the unloaded scheduler, clean attached checkout and 39/10 counts; smoke-rebase-recovery.log:2–15 records held-lock/live-owner refusals and successful backup/patch/abort. The merge control is explicitly classification-only with no repair command run (log:16–19), not an exercised abort path. The retained harness shows that same limit. Summary line 10 expressly withholds live repair and completion-attribution qualification. This review claims no new runtime recovery result.
- [Pass] experimental/git-pulse/git-pulse-sync-repair/SKILL.md:3–8 and TESTS-RESULTS/2026-10-18+GH-334/provenance.jsonl:1–3 — The folded description has 466 characters, below 1024; the three retained artifact hashes match their provenance records. Narrow read-only probe below exited 0; decisive output: `description characters: 466`, and `sha256 matches: True` for smoke-main-path.log, smoke-rebase-recovery.log and smoke-rebase-recovery.sh.txt. This checks retained bytes, not execution truth.

Probe command (environment: PYTHONDONTWRITEBYTECODE=1, TMPDIR="$PWD/.relay-scratch/tmp"):
```bash
python3 - <<'PY'
from pathlib import Path
import hashlib,json
p=Path('experimental/git-pulse/git-pulse-sync-repair/SKILL.md')
s=p.read_text(); desc=s.split('description: >\n',1)[1].split('\n---',1)[0]; desc=' '.join(x.strip() for x in desc.splitlines())
print('description characters:',len(desc))
base=Path('TESTS-RESULTS/2026-10-18+GH-334')
for row in map(json.loads,(base/'provenance.jsonl').read_text().splitlines()):
 print(row['artifact'], 'sha256 matches:', hashlib.sha256((base/row['artifact']).read_bytes()).hexdigest()==row['sha256'])
PY
```

- [Unverified — needs clone run] Gates and recovery were not rerun in this reviewer worktree. The seeded brief enumerates only skill/docs/evidence changes; repository-wide change containment remains the harness's check. Fast/failed/already-running completion attribution remains unqualified as SUMMARY.md:10 states. No additional suite, daemon or code is requested.

VERDICT: FAIL
Basis: One SOP clarification remains to make its safety rule expressly agree with the approved procedure; command quoting is a small additional correction. The published smoke supports its bounded claims, and the procedural implementation otherwise follows the approved plan.

Handing off to Producer (claude-a) — clarify the SOP exception, consider the quoting correction, disposition the findings and open the next review round.

### Producer · Round 1 dispositions (claude-a)

- **[Should] SOP.md:369–370: Accepted.** The closing sentence now keeps unconditional preservation for merge, cherry-pick and revert, and preserves a dirty tree or detached HEAD only **outside such a conflicted rebase**. That matches SKILL.md:92–93 exactly.
- **[Nit] SKILL.md:85: Accepted.** It now reads `"$(cat "$R/orig-head")"`.

Round 2 of 3: please re-check SOP.md's GH-334 paragraph and SKILL.md 2.4.d.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
