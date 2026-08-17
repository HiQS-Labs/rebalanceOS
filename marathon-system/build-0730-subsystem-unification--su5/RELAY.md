# Marathon Phase su5
STATUS: Open
NEXT: codex (Builder)

<!-- marathon-drive: task=MARATHON-SU5-TURN builder=codex reviewer=agy round-cap=7 -->

## Phase Brief

---
title: "Phase su5 One Git Subprocess Wrapper"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su5 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su5 — One Git Subprocess Wrapper (#28)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su5 in marathon harness. |

## Objective
Consolidate all private git subprocess runners across pulse, snapshot, sleuth, and ask-self modules onto `src/rebalance/lib/git_ops.py`.

## Context & Files
- Target files: `src/rebalance/lib/git_ops.py`, `src/rebalance/ingest/pulse.py`, `src/rebalance/ingest/sync_snapshot.py`, `src/rebalance/ingest/sleuth_reminders.py`, `src/rebalance/ingest/ask_self_scan.py`
- Issue: #28 — Four private git runners with divergent timeout/error contracts.

## Tasks
1. Export `run_git(repo_path, *args, timeout=30.0)` and `git_pull_rebase_safe(repo_path)` from `lib/git_ops.py`.
2. Replace private `_run_git` and `_git` across `pulse.py`, `sync_snapshot.py`, `sleuth_reminders.py`, and `ask_self_scan.py`.
3. Add contract test asserting no direct `subprocess.run(["git", ...])` calls outside `git_ops.py`.

## Definition of Done
- `pytest tests/test_git_ops.py tests/test_sync_snapshot.py tests/test_pulse.py` green; zero private git runners.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): src/rebalance/lib/git_ops.py,src/rebalance/ingest/pulse.py,src/rebalance/ingest/sync_snapshot.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/ask_self_scan.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick claim MARATHON-SU5-TURN --agent codex --paths "marathon-system/build-0730-subsystem-unification--su5/RELAY.md,src/rebalance/lib/git_ops.py,src/rebalance/ingest/pulse.py,src/rebalance/ingest/sync_snapshot.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/ask_self_scan.py"
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick ping MARATHON-SU5-TURN --agent codex
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-SU5-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/build-0730-subsystem-unification--su5/RELAY.md and src/rebalance/lib/git_ops.py,src/rebalance/ingest/pulse.py,src/rebalance/ingest/sync_snapshot.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/ask_self_scan.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: src/rebalance/lib/git_ops.py,src/rebalance/ingest/pulse.py,src/rebalance/ingest/sync_snapshot.py,src/rebalance/ingest/sleuth_reminders.py,src/rebalance/ingest/ask_self_scan.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-SU5-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick done MARATHON-SU5-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   Edit ONLY marathon-system/build-0730-subsystem-unification--su5/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
4b. TO VERIFY A FINDING, WRITE PROBE FILES OUTSIDE THE REPO — under $TMPDIR, never inside the
   working tree. Creating even one scratch file in the repo is an off-lane write: containment
   reverts it and FAILS YOUR WHOLE TURN, discarding the review you just did (GH-441). Observed
   2026-08-08: a reviewer found a real latent crash, wrote two probe files in-tree to demonstrate
   it, and lost the turn for doing so — the finding survived only because RELAY.md happens to be
   on your allowlist. `cp` what you need to "$TMPDIR/probe.$$/" and work there instead. Verifying
   is wanted; verifying in-tree is what costs you the turn.
5. HAND OFF EXPLICITLY (GH-268): end your turn by naming who acts next — "handing off to codex —
   codex, take your turn" when requesting changes, or "relay closed, no further turn needed" when
   approving. The beta report singled this out: the Reviewer turn did not tell the user to go back to the
   Producer, so the relay looked stalled when it was simply waiting. Do this EVERY round.
