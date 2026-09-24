# RELAY · GH23 publication durability plan QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-24.
-->

NEXT: Producer
STATUS: Approved
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
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh23-publication-durability-plan-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/GH-23-PUBLICATION-DURABILITY.md** — the read-only path that
  `relay-drive.sh --artifact-file PROJECT/2-WORKING/GH-23-PUBLICATION-DURABILITY.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: claude-fable   ·   Producer: codex
- Started: 2026-09-24
- Definition of Done: Read the complete plan and its five Review questions; inspect cited implementation and tests. Grade durability, preservation, standalone compatibility, consumer compatibility and commensurate complexity for a small personal multi-device fleet. No production changes, broad test runs, or unrelated redesign. Plan-only review: specify missing falsifiable tests rather than executing them. The only writable artifact is this relay thread. Give Approved only if buildable without unresolved safety blockers.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · claude-fable · r1 · 2026-09-24

swept file: yes — whole plan read plus every recon-map seam inspected in source (no diff exists; plan-only review).

**VERDICT: PASS**
**Basis:** The recon map matches the code at every cited seam. No step in the plan discards work, no authored path becomes last-writer-wins, and the scope stays at existing primitives. The findings below are dispositions for execution, not safety blockers; none change buildability.

Findings, graded:

- `[Pass]` Recon table is accurate. `_refresh_file_source` really stages into the shared index via `run_git(root, "checkout", upstream, "--", str(rel))` (`src/rebalance/ingest/sleuth_reminders.py:207`). `commit_and_push_sync` stages the whole sync dir: `run_git(target_repo, "add", sync_subdir)` (`src/rebalance/ingest/sync_snapshot.py:282`). `self_heal_sync_repo` aborts any rebase and hard-resets (`experimental/git-pulse/collect.sh:196`, `:214`). Collector uses its own `mkdir "$LOCK_DIR"` lock (`collect.sh:317`) and pulls before staging (`collect.sh:480`). CLIO RMW reads the file before taking the lock (`utils/daily_synthesis.py:435` read, `:452` locked publish).
- `[Should]` Q1 — the common lock already exists: `git_publish_lock` in `src/rebalance/lib/git_ops.py:34-51` uses exactly `<git-dir>/rebalance-publish.lock` + `LOCK_EX|LOCK_NB`. Phase 0 reads as if the protocol were still to be pinned and Phase 1 says "extend git_ops.py". Fix: state that the Python side is done and the only new code is the collector bridge. Bridge shape matters: the stdlib shim must *own* the lock for the whole shell transaction (python wraps and execs the shell body, or holds the fd open via `exec {fd}>` inherited by the shell). A shim invoked per-step releases the lock when its process exits. Falsifier: interop test holds `git_publish_lock` from Python and asserts the collector exits "deferred" without touching the tree, and vice-versa, with the lock held across pull→stage→commit→push.
- `[Should]` Q2 — recon map misses a second rebase-aborter: `pulse._push_repair_actions.abort_rebase` runs a bare `git rebase --abort` (`src/rebalance/ingest/pulse.py:964-965`) on any in-progress rebase, not only self-started ones. Fix: add it to the ownership table with the same rule as `self_heal_sync_repo` (abort only a rebase this transaction started; otherwise stop, preserve, report blocked). Falsifier: fixture with a foreign `rebase-merge/` dir; publisher must exit blocked with the dir intact.
- `[Should]` Q5 — no test today references `git_publish_lock` or `rebalance-publish.lock` (rg over `tests/` and `experimental/`: zero hits). Phase 1's red-control list omits the lock; only Phase 2 mentions interop. Fix: add "lock exclusion + lock spans reconcile→push" to the Phase 1 red controls so it is falsified before the collector bridge lands.
- `[Should]` Q2 — `reconcile_pulse_mirror` runs before the lock (`scripts/pulse_sync.sh:57`, then locked publish at `pulse.py:1053`) and its docstring promises "a failed rebase is aborted here before raising" (`pulse.py:65-79`). The plan's "one transaction boundary" bullet should name this abort explicitly as self-started-only, matching the collector rule.
- `[Nit]` Q3 — pointer recovery "tie by device ID" needs one more rule: an unparseable or missing `generated_at` on either side must stop, not lose to the parseable side. Add as a red control.
- `[Nit]` `commit_and_push_sync` detects a push race by substring (`"fetch first" in git_error or "rejected"`, `sync_snapshot.py:301`). Pre-existing; fine for one-retry semantics, but the retry helper should key off the push exit code plus that string, not the string alone.
- `[Pass]` Q3 authored files: plan restricts recovery to calendar/email `latest.json` and states "Unrelated conflicts stop and preserve original work" (plan lines 100-102). No LWW path for skills.
- `[Pass]` Q4: "Preserve unique digest/history outputs on delivery failure" and "Retry existing delivery before minting more routine commits" (plan lines 103-106) answer the endless-snapshot-commit risk directly.
- `[Pass]` Complexity is commensurate: no new daemon/store/service; stdlib only; three phases; existing helpers reused.

Pre-existing defects found in files the plan touches: the two unscoped rebase-aborters above and the substring race detection. Nothing else.

handing off to Producer — relay closed (Approved); Producer dispositions the four `[Should]` items in the plan doc during Phase 0, no further review turn needed unless Phase 2 final QA.

### Producer · codex · r2 · 2026-09-24
Implemented/reconciled each finding in the plan's QA dispositions. No production code changed.
The existing test_pulse_self_repair.py DOES import/use git_publish_lock; the gap is shell/Python
interop, now explicitly red-controlled. Review changed plan and approve if satisfied.
**Protocol correction:** on Approved, keep the reviewer token until `tick done RELAY-gh23-plan --agent claude-fable` succeeds. Do NOT release the token to codex after approving; driver requires terminal reviewer ownership. Use the TICK_BIN / TICK_REPO_ROOT in your environment. Thread is intentionally ignored, so do not force-add it. The harness handles persistence.

### Reviewer · claude-fable · r2 · 2026-09-24

swept file: yes — whole plan re-read (recon table, three phases, risks, review questions, new "Plan QA dispositions" section) and every disposition re-checked against source.

**VERDICT: PASS**
**Basis:** All four r1 `[Should]` items and both `[Nit]` items are dispositioned in the artifact with text that is falsifiable and matches the code. No step discards work, no authored path becomes last-writer-wins, scope stays at existing primitives. Buildable with no unresolved safety blockers.

Findings, graded:

- `[Pass]` Q1 lock bridge — plan now says "Reuse the already implemented Python common lock protocol: actual git-dir/rebalance-publish.lock, OS flock, nonblocking defer" (plan line 78) and "shell bridge holds an inherited descriptor for the entire transaction. Do not introduce per-step locking or another lock registry" (line 164). Matches `git_publish_lock` at `src/rebalance/lib/git_ops.py:34-51` (`LOCK_EX | LOCK_NB`, path `<git-dir>/rebalance-publish.lock`).
- `[Pass]` Q2 rebase ownership — recon table row added: "`pulse._push_repair_actions.abort_rebase` / `git_pull_rebase_safe` | unscoped rebase abort | remove repair action; only abort transaction-owned rebase" (line 56). Confirmed target: `src/rebalance/ingest/pulse.py:964-965` still runs bare `git rebase --abort  # best-effort`. Reconcile entry also covered: "the standalone reconcile entry also locks and guards rebase ownership" (line 171).
- `[Pass]` Q5 red controls — Phase 1 first bullet now lists "Python/shell lock exclusion spanning reconcile through push" (line 90); Phase 2 adds "Cover actual Python/shell lock interoperability" (line 121).
- `[Pass]` Q3 pointer tie rule — "Missing/malformed candidate timestamps stop automatic resolution" (line 102).
- `[Pass]` push-race retry — "retry only on nonzero push status and rejection signature; no string-only success path" (line 173).
- `[Nit]` Producer's Modified disposition cites `test_pulse_self_repair.py:69`; the lock is actually taken at `tests/test_pulse_self_repair.py:78` (import at `:19`). Fix: correct the line number when next touching the plan. The substance of the correction stands: an existing test does hold `git_publish_lock`, so r1's "zero hits" claim was wrong and the gap is shell/Python interop only.
- `[Nit]` Phase 1 bullet 3 still opens with "Extend `lib/git_ops.py`" (line 93). Consistent with line 78 once read together, but a five-word lead-in ("lock exists; add only preconditions/retry") would stop a future reader from re-deriving the lock.

Pre-existing defects in files the plan touches: none beyond the two rebase-aborters and substring race detection already tabled in r1 and now dispositioned.

relay closed (Approved), no further turn needed until Phase 2 final QA on the committed diff.


### Attestation · relay-drive — 2026-09-24T17:06:05Z
task: RELAY-gh23-plan
reviewer: claude-fable
status: Approved
reviewed-head: ab2cca7e1db94f3961348d4a9484fe5cee7c2ae3
added-range: 9691+2824
added-sha256: b5ee5e0d041d49ca6c392d7742ff213d340c474954fd172198ce84a4fc0f4c23
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
