---
gh_issue: 124
source: https://github.com/HiQS-Labs/rebalanceOS/issues/124
title: "Org rename HiQS-Suite→HiQS-Labs: durable fix (self-deriving repo, redirect handling, permanent CI guard)"
status: "Completed — shipped directly to development as a hotfix, commit 217f29b"
created: 2026-08-25
updated: 2026-08-25
owner: noel
doc_type: bugfix
goal: >
  Replace the one-off HiQS-Suite -> HiQS-Labs string swap with a fix that survives the
  NEXT org rename too: derive the target repo at runtime instead of hardcoding it,
  degrade gracefully on an API redirect instead of crashing, and add a permanent CI
  guard so a stale org string can never again rot silently for days.
effort: 2
complexity: 2
risk: 1
phases: 1
ratings_provisional: true
roadmap_exempt: true
---

# GH-124 — Org Rename Durable Fix

## Status

| What was just completed | What's next |
|---|---|
| All three fix layers implemented, tested, committed (217f29b), and pushed to `development`. Two extra live instances of the same bug class caught and fixed by the new guard along the way. | Nothing planned — this is a completed hotfix. Follow-up only if `frontdoor-check.sh`'s CI wiring ever needs extending to more file types. |

## Why

`scripts/health_issue_reporter.py` hard-coded `REPO = "HiQS-Suite/rebalanceOS"`. When the GitHub org
was renamed to HiQS-Labs, every `POST` this script made hard-crashed: GitHub's redirect covers `git
fetch`/`push` and browser links, but not a raw REST API `POST` through Python's `urllib`, which
refuses to auto-follow a 307 for a non-idempotent method and raises `HTTPError` instead. This broke
invisibly for at least a day — the script that would have surfaced the crash as a filed/updated
GitHub issue *was* the crashing script, so GH-84 (the `obsidian-vault-embeddings` health tracker)
never picked up a 20+ hour failure streak that was happening in plain sight in the log files.

A literal string replacement (`HiQS-Suite` → `HiQS-Labs`) would have fixed this specific incident and
nothing else — the next rename, or a repo transfer, would reproduce the exact same failure mode.

## What shipped

1. **Self-deriving repo target.** `_default_repo()` in `health_issue_reporter.py` reads
   `git remote get-url origin` at runtime and parses `OWNER/REPO` out of it. The hardcoded string is
   kept only as a last-resort fallback if git detection fails (e.g. a non-git checkout).
2. **Redirect handling as defense in depth.** `_request()` now manually follows a single 307/308
   redirect (via the response's `Location` header) instead of raising. Covers what layer 1 can't — a
   stale `--repo` CLI override, or a genuine repo *transfer* rather than an org rename.
3. **Permanent regression guard.** `utils/frontdoor-check.sh` gained check 8: a `RETIRED_OWNERS` array
   git-grepped across live/functional files (`*.py *.sh *.js *.json *.yml *.yaml`), excluding the same
   historical-narrative paths check 1 already excludes (CHANGELOG.md, ROADMAP.md, PROJECT/**,
   relay-system/**, marathon-system/**, test/**). Wired into CI's `docs` job so a reintroduced stale
   org string fails the build instead of rotting silently.

**Also fixed, caught live by the new guard:**
- `utils/py/releases_app.py`'s issue/PR-URL regex was pinned to a specific owner for no functional
  reason (it only needs to match the repo name, `XYZ-forge`, not any particular org) — widened to be
  owner-agnostic.
- A stale forward-looking comment in `.github/workflows/ci.yml` ("extraction to HiQS-Suite/HiQS") —
  corrected to the current org, since it described a still-live future plan, not history.
- The repo's own `origin` remote, `manifest.json`, `utils/frontdoor-check.sh`'s manifest-drift check,
  and `utils/pdda/prior-art-check.sh` — all stale, all corrected in an earlier pass the same day.

## Verification

- `python3 utils/py/health_issue_reporter.py --dry-run` (via `.venv`) runs clean, reports
  `repo: HiQS-Labs/rebalanceOS` derived correctly from the fixed remote.
- `bash utils/frontdoor-check.sh` is clean on the org-rename check (one unrelated pre-existing
  pyproject/manifest version-drift finding remains, out of scope for this fix).
- `python3 utils/py/releases_app.py check` — clean, 0 failures.

## Non-goals

- Did not wire `frontdoor-check.sh` into anything beyond the `docs` CI job.
- Did not touch the same class of bug in the upstream `XYZ-forge` harness repo itself, or in
  `aegis-sleuth-slack-bot`'s independently-vendored copy of `releases_app.py` — those are separate
  repos with their own maintainers/review process.
- Did not fix the pre-existing, unrelated `pyproject.toml`/`manifest.json` version-drift finding that
  `frontdoor-check.sh` also currently reports.
