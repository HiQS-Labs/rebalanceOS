# RELAY · rebalanceOS GH-336 plan QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
-->

NEXT: Producer
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

### Reviewer · Round 1

VERDICT: FAIL
Basis: The one-flag correction is appropriate, but the timebox pivots must not bypass unresolved correctness findings or the required recovery proof. One Should; no observed execution Blocker. This is plan review, not recovery attestation.
swept file: yes

Reviewed the whole GH-336 plan and the whole referenced SKILL and GH-334 plan, including pre-existing procedure and dispositions; read the SOP's evidence rules and GH-334 exception. No additional evidenced pre-existing Blocker found. Existing bare CLI calls and missing load-run note are already covered by the proposed fold-in. Graph check: nearest indexed project `rebalanceOS` is another checkout, generation `2026-09-02T03:54:57Z`; coverage reports missing freshness for the three artifact paths and changed SOP metadata. Used current local source directly, not stale graph evidence.

- [Should] S1 — Keep correctness gates intact at the timebox. `PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md:133` says to ship after plan QA ends without approval, and `:135` promises “at least the one-flag fix” at two hours. Neither conditions that fallback on resolving correctness findings and passing the recorded restore smoke; `:134` instead says to stop after unresolved final QA. Fix: say that round/time limits stop expansion and leave unresolved work parked; the reduced one-flag change may proceed only with its applicable findings dispositioned and its smoke/red control/static gate passed. Otherwise stop and report. No extra rounds or machinery needed.
  Observed input: The literal pivot row at `:133`: “Plan QA reaches round 2 without Approved | Ship the one-flag fix as a simple change.” Read command: `nl -ba PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md`, exit 0; decisive output is that row and the unconditional minimum at `:135`.
  Affected scope: Only the plan's round-cap/time-expiry delivery decisions when correctness findings or required verification remain unresolved; ordinary verified reduced-scope delivery stays allowed.
  Falsifier: Evaluate a round-2 unresolved finding against the binary restore itself, or a deadline reached before the smoke completes. Expected outcome: park/stop, no claim of verified delivery. If the pivots already required that outcome, this request would be unnecessary; their current text does not.

- [Pass] P1 — The proposed fix targets the reported omission without adding infrastructure. Plan `:83-87` adds `--binary` and mirrors step (e); the current omission is at `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:99-100` and `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md:95`. The [Git diff manual](https://git-scm.com/docs/git-diff#Documentation/git-diff.txt---binary) documents an applyable binary patch plus full blob IDs. The detached worktree at the saved HEAD (`:86`) uses the appropriate patch base. This supports the design, not a claim that its smoke ran. `gh api repos/HiQS-Labs/rebalanceOS/issues/336 --jq '{title,body,state}'`, exit 0, returned the open issue requesting this same flag/check and reporting the old-command binary apply failure.

- [Unverified — needs clone run] U1 — Do not equate a working-tree patch with an exact index snapshot. The universal wording at plan `:66-70` exceeds the three-case scenario at `:98-102`. The [Git diff description](https://git-scm.com/docs/git-diff#_description) distinguishes comparison of working tree against HEAD from `--cached` comparison of the index. Concrete proposed falsifier, not an observed incident: during an unrelated unresolved conflict, another tracked file has HEAD bytes A, staged bytes B, and working-tree bytes A again. A working-tree-against-HEAD patch cannot encode B. Clarify whether recovery promises final on-disk bytes only; if exact staged versions are required, measure this input in the disposable clone before asserting completeness. No backup redesign requested on an unexecuted example. Mode/deletion/rename recovery and conflicted-binary restoration were not executed here either.

- [Pass] P2 — The verification plan is proportionate for the stated binary-content defect: main scenario, old-command red control, text-only adjacent path, durable commands/output and provenance are explicit at plan `:97-105`, with acceptance at `:140-145`. Keep the byte comparison and command exit statuses explicit in the eventual receipt. The nonempty/no-placeholder check at `:84-85` is a useful omission guard, not independent proof of complete restoration; the planned restore smoke supplies that evidence. No Git, test suite, executable fixture or recovery probe was run this turn.

- [Pass] P3 — Scope and consistency: the three wording fold-ins at plan `:88-95` address existing procedure steps and are reasonably small. SOP `:361-372` delegates the procedure and does not quote `diff HEAD`, so it needs no command substitution. The source-update then link-reconciliation sequence at plan `:110-113` matches the Skills Army HQ documented copy/link model; remote-device arrival remains delivery to be observed, not proven by local links.

- [Nit] N1 — Expand the post-merge shorthand into the existing manager workflow when executing it: status/list first, preview the exact update, inspect warnings, apply, then status/list and source parity plus link read-through. Plan `:146-147` checks only that one line exists; it does not prove intended source revision or whole-folder parity. Use the existing Skills Army HQ checks, with no new automation. Distinguish local deployment from app discovery and other devices' eventual receipt.

Root cause: the plain patch omits binary payloads; fix site: the procedure's patch-generation command and its mirrored plan; why not upstream/downstream: the backup branches preserve commits, while this command owns capture of uncommitted working-tree bytes. Behavioral proof remains the Producer's disposable-clone smoke.

Handing off to Producer (claude-a): disposition S1 and the remaining review notes, revise the plan, and return for round 2. Only this relay file was edited; the harness owns its commit.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
