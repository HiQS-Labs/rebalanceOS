---
gh_issue: 236
source: https://github.com/HiQS-Labs/rebalanceOS/issues/236
title: "Diagnose a broken runtime virtualenv across the scheduler fleet"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-09-21
updated: 2026-09-21
owner: Codex
doc_type: bugfix
goal: >
  Make doctor and stack status identify a missing or dangling runtime virtualenv
  interpreter as the shared cause of fleet-wide launchd EX_CONFIG failures.
effort: 2
complexity: 2
risk: 2
phases: 1
---

# GH-236 — runtime virtualenv diagnostics

## Bug

A Homebrew Python patch upgrade can leave the declared runtime checkout's
`.venv/bin/python` symlink chain pointing at a removed Cellar interpreter. launchd
then exits every interpreter-backed scheduler job with status 78 before the job
wrapper can write a current log. `stack.sh verify` identifies the missing executable,
but `stack.sh status` and `rebalance doctor` currently present only opaque per-job
failures and a kickstart remedy that cannot repair the interpreter.

## Acceptance

- `rebalance doctor` emits one fleet-level failure when installed Rebalance plists
  reference the declared runtime interpreter and it is missing, non-executable, or a
  dangling symlink; the finding names the affected-job count and explicit repair flow.
- Per-job nonzero-exit hints direct operators through `stack.sh verify` before logs or
  kickstart, so status 78 no longer implies kickstart alone is sufficient.
- `stack.sh status` prints the same root-cause warning and points to `stack.sh verify`.
- Hermetic tests cover a healthy executable, an absent path, and a dangling symlink.
- Diagnosis stays read-only; the product does not delete or recreate a virtualenv.

## Assessment

Rated 90/90/50/80 (priority/severity/neutral appeal/cheapness). The confirmed incident
disabled 12 of 13 managed jobs and left indexed sources five days stale, while the
repair is localized to existing doctor and stack diagnostics. One incident is proven;
there is not enough same-root-cause history to claim an increasing recurrence trend.

