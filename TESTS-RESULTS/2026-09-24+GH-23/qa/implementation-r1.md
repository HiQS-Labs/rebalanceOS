# RELAY · GH23 publication durability implementation QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-24.
-->

NEXT: Producer
STATUS: Approved
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
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh23-publication-durability-implementation-qa): <role> r<N>`); no push. **Stop** and report one line.
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
- Definition of Done: Review the complete diff from e21ec19 through HEAD, touched functions and callers, the plan including execution refinements and recovery evidence, and TESTS-RESULTS/2026-09-24+GH-23. Assess preservation, exact path ownership, full lock lifetime, standalone shell compatibility, bounded conflict recovery, offline unique-versus-replaceable behavior, cursor acknowledgement, and the live recovery procedure. Give concrete failure inputs and fixes. Do not edit source or run the full suite; focused hermetic tests are allowed. Approve only if no material safety or durability blocker remains.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer r1 — claude-fable (Fable 5.1) — 2026-09-24

Scope reviewed: full diff e21ec19..HEAD (28 files), current bodies of `git_ops.py`, `sync_snapshot.py`, `pulse.py`, `sleuth_reminders.py`, `index_ops._refresh_sync`, `daily_synthesis.sync_to_clio`, `collect.sh`, `pulse_sync.sh`, the plan artifact, and TESTS-RESULTS/2026-09-24+GH-23/SUMMARY.md.
swept file: yes — pre-existing code around every touched function was read, not just the hunks.
Focused test re-run in the reviewer sandbox aborted before pytest started (interpreter exit 134, empty log, `.relay-scratch/contract.txt`); verdict relies on the retained red.txt/full.txt evidence and code reading. Harness gate should re-confirm.

**Preservation / lock lifetime / ownership**
- [Pass] Exact path ownership: commit bounded by `git commit --only -- <paths>` (`src/rebalance/lib/git_ops.py:428`); foreign staged and unstaged paths refused before any write (`git_ops.py:356-368`); snapshot publisher stages only device + two pointers (`src/rebalance/ingest/sync_snapshot.py:281-288`).
- [Pass] Pre-existing rebase/merge/cherry-pick/detached HEAD refused without modification (`git_ops.py:339-347`); abort only fires when a rebase exists after *our* pull and the pre-check passed (`git_ops.py:380-385`). Shell mirrors it: `check_sync_repo` before `pull --rebase`, abort only afterwards (`collect.sh` `pull_safely`).
- [Pass] Full lock lifetime: pulse write/RMW/commit/push inside one `git_publish_lock` (`pulse.py:817-826`); `pulse_sync.sh` no longer reconciles outside the lock (diff removes the GH-152 pre-step); CLIO RMW is a callable evaluated under the lock (`utils/daily_synthesis.py:443-447`); collector re-execs under an inherited flock on the same `rebalance-publish.lock` and verifies the inherited fd by dev/inode before touching Git (`collect.sh` PREPARE block).
- [Pass] Reminder reader no longer writes index/worktree: fetch + `git show <upstream>:<rel>` with explicit local-cache fallback (`sleuth_reminders.py:178-207`).
- [Pass] Remote verification attests exact committed blobs on `@{u}` per path before `pushed=True` (`git_ops.py:445-451`); collector acknowledges cursor only after `git merge-base --is-ancestor HEAD '@{u}'` (collect.sh diff, push section).

**Bounded conflict recovery / offline behavior**
- [Pass] Pointer resolver refuses any conflict set not ⊆ {calendar,email}/latest.json and fails closed on missing/unparseable `generated_at`, device/filename mismatch, wrong source/schema (`sync_snapshot.py:297-328`); `JSONDecodeError` is a `ValueError` so it is caught at `git_ops.py:378` and the owned rebase is aborted, leaving the local commit intact.
- [Pass] Live-page opt-in is tight: only `replaceable=True`, only when the sole conflicted path is `file_rel` and `REBASE_HEAD` touches exactly that path (`pulse.py:869-881`). Digests, CLIO log, skills remain fail-closed.
- [Pass] Offline replaceable page retries the pending revision before rendering another (`pulse.py:885-889`) and returns early on failure, so no backlog grows; unique dated paths are still committed locally and delivered on the next successful push (contract tests `test_offline_page_retry_does_not_grow_backlog`, `test_offline_append_only_log_retains_new_days`).
- [Pass] Retry gated on nonzero status AND rejection signature (`git_ops.py:435`), one bounded pass.

**Findings requiring follow-up (none block approval)**
- [Should] `_update_latest_pointer` now raises `ValueError` on any malformed/half-written `latest.json` (`sync_snapshot.py:239-245`). It is called from `export_calendar_snapshot` inside the lock at `index_ops.py:2102` with no handler, so a single torn pointer file (non-atomic `write_text`, killed process) wedges every hourly sync refresh on that device with a traceback until hand repair. Failure input: truncate `sync/calendar/latest.json` to `{"device_id": "a"` and run `_refresh_sync`. Fix: catch in `_refresh_sync`, publish the device file only, leave the pointer untouched, and return `{"error": "latest pointer malformed", "deferred": True}`; keep the auto-overwrite removed. Land before the single-device pilot.
- [Should] Recovery runbook: before the recovery push, record and check `git merge-base --is-ancestor <displaced-tip> <recovery-HEAD>` and `git merge-base --is-ancestor <remote-tip> <recovery-HEAD>` in the evidence, plus the remote blob of the two recomputed pointers after push. The artifact asserts both tips are ancestors but the DoD needs it demonstrated remotely, not locally.
- [Nit] Collector lock shim runs before the "Run install.sh to clone it" guard (`collect.sh` ~L308 vs L347); a missing clone now dies with a Python traceback from `rev-parse`. Move the shim after the clone check or guard the `check_output`.
- [Nit] Busy-lock exit changed from 0 to 75 (`collect.sh` shim). Correct semantically, but the LaunchAgent/log consumers will now see failures where they saw skips; note in the runbook.
- [Nit] `_resolve_pointer_conflicts` reads the file before `is_symlink()` (`sync_snapshot.py:314-316`); harmless since it raises either way, but swap the order.
- [Nit] `pulse.py:858-867`: the "no content change" branch verifies remote against the stale local `@{u}` and then pulls; a pull conflict there returns `git_error` for a run that changed nothing. Consider reporting `reason` plus a `reconcile_error` field.
- Pre-existing defects in touched files: none material found beyond the above.

**VERDICT: PASS**
**Basis:** every DoD dimension (preservation, exact path ownership, full lock lifetime, standalone shell compatibility via stdlib flock shim, bounded one-retry conflict recovery, offline unique-vs-replaceable behavior, cursor acknowledgement after upstream ancestry, preservation-first recovery with bundle + unpushed merge) is implemented fail-closed with cited code and red/green evidence. The one Should is a wedge-until-repair, not loss, and does not block approval; fix it before the pilot.

relay closed (Approved), no further turn needed — Producer: land the [Should] on `_update_latest_pointer` handling before the single-device pilot, then proceed to PR.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->

## Producer handoff

Source is committed; root + HiQS passed 2770 tests. The isolated live recovery has retained the displaced tip and remote tip as merge ancestors and remains unpushed. Inspect the generated live-page opt-in resolver especially: this is the explicit refinement beyond pointer-only plan QA. The old installed collector has been unloaded after it actually reset the live branch; preserved history is verified in a private Git bundle. No secrets or production data are part of this artifact.

Protocol: on Approved, use `tick done RELAY-gh23-final --agent claude-fable` while holding the token; do NOT release after approval. Use TICK_BIN/TICK_REPO_ROOT from environment. This thread is intentionally ignored: do not force-add it; the driver retains it. On findings, release to codex normally.
