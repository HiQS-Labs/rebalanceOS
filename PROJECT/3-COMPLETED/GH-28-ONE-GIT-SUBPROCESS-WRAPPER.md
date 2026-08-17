---
gh_issue: 28
source: https://github.com/HiQS-Suite/rebalanceOS/issues/28
title: "GH-28 One git subprocess wrapper (4 private variants, 4 different contracts)"
status: "Completed — shipped in the Build 0.73.0 Subsystem Unification marathon (phase su5) as PR #40 (0.73.0)"
created: 2026-08-16
updated: 2026-08-17
owner: noel
doc_type: code-quality
goal: >
  Consolidate all private git subprocess runners into a single canonical wrapper in
  src/rebalance/lib/git_ops.py with consistent timeout, returncode, and error handling.
effort: 2
complexity: 1
risk: 1
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-28 — One Git Subprocess Wrapper

## Status

| What was just completed | What's next |
|---|---|
| Four divergent private git subprocess variants inventoried across collectors. | Phase 0 review of wrapper contracts and error handling conventions in `lib/git_ops.py`. |

## Why

`src/rebalance/lib/git_ops.py` defines `_git(repo_path, *args, timeout=30.0)`, but several collectors maintain private git runners with inconsistent semantics:
1. `_run_git` is defined verbatim in `src/rebalance/ingest/pulse.py:1027` and `src/rebalance/ingest/sync_snapshot.py:238`.
2. `src/rebalance/ingest/sleuth_reminders.py:195` defines `_git(cwd, *args)` using `check=True` and a 60s timeout.
3. `src/rebalance/ingest/ask_self_scan.py:125` has its own `git remote get-url origin` invocation and exception handling.
4. The `git pull --rebase` + `rebase --abort` repair pattern is duplicated across `pulse.py:82` and `sync_snapshot.py:278`.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Canonical git wrapper and rebase helper](#phase-1--canonical-git-wrapper-and-rebase-helper)
- [Phase 2 — Migration and contract test](#phase-2--migration-and-contract-test)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `src/rebalance/lib/git_ops.py:80`: `_git(repo_path, *args, timeout=30.0) -> str | None`.
- `src/rebalance/ingest/pulse.py:1027`: `_run_git`
- `src/rebalance/ingest/sync_snapshot.py:238`: `_run_git`
- `src/rebalance/ingest/sleuth_reminders.py:195`: `_git`
- `src/rebalance/ingest/ask_self_scan.py:125`: `_git_remote_url`

**Research questions:**
1. Define the public API in `git_ops.py`: e.g. `run_git(repo_path, *args, timeout=30.0, check=False) -> str | None` and `git_pull_rebase_with_abort(repo_path) -> bool`.
2. Standardize timeout defaults (30.0s standard, configurable per call).

**Acceptance criteria for Phase 0:**
- Unified `run_git` signature agreed upon that satisfies all 4 existing use cases.

## Phase 1 — Canonical git wrapper and rebase helper

- [ ] Export `run_git(repo_path: Path | str, *args: str, timeout: float = 30.0) -> str | None` from `src/rebalance/lib/git_ops.py`.
- [ ] Add `git_pull_rebase_safe(repo_path: Path | str) -> bool` to encapsulate `git pull --rebase` with automatic `rebase --abort` on error.
- [ ] Add unit tests in `tests/test_git_ops.py` covering success, nonzero exit code, timeout expiration, and rebase abort logic.

**QA gate:**
- `pytest tests/test_git_ops.py` passes with 100% branch coverage on the git runner.

## Phase 2 — Migration and contract test

- [ ] Replace private `_run_git` in `pulse.py` and `sync_snapshot.py`.
- [ ] Replace private `_git` in `sleuth_reminders.py`.
- [ ] Replace custom git invocation in `ask_self_scan.py`.
- [ ] Add AST / banned-pattern test in `tests/test_banned_imports.py` asserting `subprocess.run(["git", ...])` is not invoked outside `git_ops.py`.

**QA gate:**
- Full test suite passes; zero private `subprocess.run(["git", ...])` calls outside `lib/git_ops.py`.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
