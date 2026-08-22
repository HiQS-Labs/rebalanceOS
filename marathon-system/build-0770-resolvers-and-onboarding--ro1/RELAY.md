# Marathon Phase ro1
STATUS: Approved
NEXT: codex (Builder)

<!-- marathon-drive: task=MARATHON-RO1-TURN builder=codex reviewer=agy round-cap=7 -->

## Phase Brief

---
title: "Phase ro1 Live Slack User Resolver and Write-Through Cache Origin"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Phase ro1 brief"
roadmap_exempt: true
pdda_hold: true
---

# Phase ro1 — Live Slack User Resolver & Cache Origin (#114)

## Status

| What was just completed | What's next |
|---|---|
| Phase brief authored and dry-run validated. | Execute phase ro1 in marathon harness. |

## Objective
Implement live Slack user name resolution in `src/rebalance/ingest/slack_users.py` backed by optional Slack API token or publisher-embedded names, caching resolved user maps write-through to `temp/slack_users.json`, and add comprehensive test coverage in `tests/test_slack_users.py`.

## Context & Files
- Target files: `src/rebalance/ingest/slack_users.py`, `src/rebalance/ingest/config.py`, `tests/test_slack_users.py`
- Issue: #114 — Durable resolver so new machines/installs do not degrade to raw Slack UIDs.

## Tasks
1. Support reading embedded display names from export payload or querying Slack Web API `users.info` when `slack_bot_token` is present in config.
2. Maintain `temp/slack_users.json` as a write-through cache rather than an unbacked manual file.
3. Create `tests/test_slack_users.py` covering cache hits, cache misses, token resolution, and fallback behavior.
4. Verify tests pass with `.venv/bin/pytest tests/test_slack_users.py -q`.

## Definition of Done
- `pytest tests/test_slack_users.py` passes with >90% coverage.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): src/rebalance/ingest/slack_users.py,src/rebalance/ingest/config.py,tests/test_slack_users.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick
   - /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick claim MARATHON-RO1-TURN --agent codex --paths "marathon-system/build-0770-resolvers-and-onboarding--ro1/RELAY.md,src/rebalance/ingest/slack_users.py,src/rebalance/ingest/config.py,tests/test_slack_users.py"
   - /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick ping MARATHON-RO1-TURN --agent codex
   - /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick release MARATHON-RO1-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/build-0770-resolvers-and-onboarding--ro1/RELAY.md and src/rebalance/ingest/slack_users.py,src/rebalance/ingest/config.py,tests/test_slack_users.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: codex (Builder)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: src/rebalance/ingest/slack_users.py,src/rebalance/ingest/config.py,tests/test_slack_users.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick release MARATHON-RO1-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick done MARATHON-RO1-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /tmp/rebalance-marathon-set-b-1787360678/.xyz/bin/tick
   Edit ONLY marathon-system/build-0770-resolvers-and-onboarding--ro1/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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

### Round 1 · Builder · codex

Implemented a live, write-through Slack user resolver. `slack_users.py` now
uses cached names first, extracts display names from export-style payloads or
inline mentions, and falls back to Slack `users.info` when configured; newly
resolved names are persisted to the existing cache-file shape. Added the
optional `config.get_slack_bot_token()` secret resolver and focused tests for
cache hits, payload cache misses, token-backed API resolution, and unresolved
fallback rendering. Verified with `python3 -m pytest tests/test_slack_users.py -q`
(the requested `.venv/bin/pytest` executable is not present in this worktree).

### Round 1 · Reviewer · agy

swept file: yes

The code covers the requirements in the phase brief, and tests are passing. However, I found two issues during my sweep (one pre-existing defect and one concurrency hazard) that need to be addressed:

1. **Pre-existing defect in `_SLEUTH_PREFIX_RE`**: Now that `slack_users.py` uses real names instead of raw IDs, the resolved names will often contain spaces (e.g., `@Ada Lovelace`). The current `_SLEUTH_PREFIX_RE` pattern uses `^@\S+`, which stops matching at the first space and will fail to match for real names. This breaks `compact_sleuth_reminder`. Please update the regex to allow spaces in names (e.g. `r"^@[^,:\-–—]+(?:\s*,\s*@[^,:\-–—]+)*\s*[-–—:]\s*please\s+follow\s+up\s+on\s+"` or similar).
2. **Concurrency hazard in `_write_user_map`**: The JSON cache file is written without atomic file replacement or file lock, and is outside of `_cache_lock`. If two threads encounter cache misses simultaneously, they will both mutate the map and write it back concurrently, leading to JSON corruption or lost updates. Please ensure file writes are atomic and/or synchronize the write using the existing `_cache_lock`.

**Verdict:** Changes requested

### Round 2 · Builder · codex

Addressed both review findings in `slack_users.py` and added focused
regressions in `tests/test_slack_users.py`. The Sleuth header matcher now
accepts resolved names containing spaces. Cache writes now hold the existing
process lock over the merge and atomic temporary-file replacement, preserving
simultaneous resolutions and preventing partially-written JSON from being
observed. The resolver tests cover multi-word reminder compaction and
concurrent misses retaining both user names.

Verified with `.venv/bin/pytest tests/test_slack_users.py -q`.

### Round 2 · Reviewer · agy

swept file: yes

The builder correctly addressed both issues. `_SLEUTH_PREFIX_RE` has been updated to handle multi-word names properly, and `_write_user_map` correctly utilizes `_cache_lock` with atomic file replacement to ensure there's no concurrency issue or JSON corruption. Tests are comprehensive and pass successfully. No additional defects were found during the sweep.

**Verdict:** Approved
