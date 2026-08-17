# Marathon Phase su4
STATUS: Open
NEXT: codex (Builder)

<!-- marathon-drive: task=MARATHON-SU4-TURN builder=codex reviewer=agy round-cap=7 -->

## Phase Brief

---
title: "Phase su4 Deduplicate Persistence and Upsert Paths"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Phase su4 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase su4 — Deduplicate Persistence/Upsert Paths Across Collectors (#27)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase su4 in marathon harness. |

## Objective
Extract shared `table_exists` and `db_connection_readonly` helpers in `src/rebalance/ingest/db/connection.py`, deduplicating persistence loops in Gmail and GitHub knowledge collectors.

## Context & Files
- Target files: `src/rebalance/ingest/db/connection.py`, `src/rebalance/ingest/gmail.py`, `src/rebalance/ingest/github_knowledge.py`, `src/rebalance/ingest/sleuth_reminders.py`
- Issue: #27 — Duplicate 9-column email insert, duplicate 100-line issue/PR persist loops, and multiple `_table_exists` copies.

## Tasks
1. Add `table_exists()` and `db_connection_readonly()` in `src/rebalance/ingest/db/connection.py`.
2. Deduplicate message persistence in `gmail.py` into a single persister function.
3. Deduplicate issue/PR loops in `github_knowledge.py` by extracting shared item record builder and upsert steps.
4. Route `sleuth_reminders.py` through standard `db_connection()`.

## Definition of Done
- `pytest tests/test_db_connection.py tests/test_gmail.py tests/test_github_knowledge.py tests/test_sleuth_reminders.py` passes cleanly.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): src/rebalance/ingest/db/connection.py,src/rebalance/ingest/gmail.py,src/rebalance/ingest/github_knowledge.py,src/rebalance/ingest/sleuth_reminders.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick claim MARATHON-SU4-TURN --agent codex --paths "marathon-system/build-0730-subsystem-unification--su4/RELAY.md,src/rebalance/ingest/db/connection.py,src/rebalance/ingest/gmail.py,src/rebalance/ingest/github_knowledge.py,src/rebalance/ingest/sleuth_reminders.py"
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick ping MARATHON-SU4-TURN --agent codex
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-SU4-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/build-0730-subsystem-unification--su4/RELAY.md and src/rebalance/ingest/db/connection.py,src/rebalance/ingest/gmail.py,src/rebalance/ingest/github_knowledge.py,src/rebalance/ingest/sleuth_reminders.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: src/rebalance/ingest/db/connection.py,src/rebalance/ingest/gmail.py,src/rebalance/ingest/github_knowledge.py,src/rebalance/ingest/sleuth_reminders.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-SU4-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick done MARATHON-SU4-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   Edit ONLY marathon-system/build-0730-subsystem-unification--su4/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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
