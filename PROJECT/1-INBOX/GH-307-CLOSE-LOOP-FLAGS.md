---
gh_issue: 307
source: https://github.com/HiQS-Labs/rebalanceOS/issues/307
title: Close-the-loop flags from the local GitHub corpus
status: Proposed (1-INBOX — not yet active)
created: 2026-10-02
doc_type: feedback
effort: 2
complexity: 2
risk: 1
phases: 1
related: [300, 232, 233, 120, 150, 29]
---

# GH-307 — Close-the-loop flags from the local GitHub corpus

Capture of [#307](https://github.com/HiQS-Labs/rebalanceOS/issues/307). The live issue is the discussion surface.

## Ask

Add one read-only, deterministic (no LLM) per-repo report over the existing local GitHub corpus,
reusing the readiness read path. Expose it as a CLI command with JSON output so the storyline
experiment (#300) and the triple-arm timeline work can consume Rebalance's signal instead of
re-fetching GitHub. N defaults to 7 days.

| Flag | Rule (corpus only) |
|---|---|
| `stale_pr` | Open, non-draft PR with no update for more than N days |
| `forgotten_draft` | Open draft PR with no update for more than N days |
| `pr_needs_refinement` | Open PR with changes requested or failing checks |
| `closed_without_delivery` | Issue closed as completed (or with no reason) with no merged PR linking it; surfaced for confirmation |
| `started_not_shipped` | Open issue with a `gh-N`-style branch, no linked PR, and no update for more than N days |

## Acceptance

- A seeded-corpus test fires each flag and not its negative twin. `not_planned` is excluded. An
  unsynced repo returns `no_local_data`.
- Existing readiness behaviour is unchanged by default.
- `pytest tests/`, the PDDA checks and the ratchets (script inventory, read layer, sqlite connect) pass.

## Not in scope

Focus 5 UI, Daily integration, LLM phrasing, new GitHub API calls, cross-repo links, and a
CLIO-based "no activity since" condition.
