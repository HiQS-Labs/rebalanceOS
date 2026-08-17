---
gh_issue: 25
source: https://github.com/HiQS-Suite/rebalanceOS/issues/25
title: "GH-25 Consolidate all timestamp handling through lib/time_ops"
status: "Completed — shipped in the Build 0.73.0 Subsystem Unification marathon (phase su2) as PR #40 (0.73.0)"
created: 2026-08-16
updated: 2026-08-17
owner: noel
doc_type: code-quality
goal: >
  Eliminate remaining timestamp handling bypasses and alias wrappers across the codebase,
  converging all UTC generation and ISO parsing on canonical src/rebalance/lib/time_ops.py.
effort: 2
complexity: 1
risk: 1
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-25 — Consolidate Timestamp Handling Through lib/time_ops

## Status

| What was just completed | What's next |
|---|---|
| Mechanical sweep of direct `datetime.now(timezone.utc)` calls in `src/` and `scripts/` completed in PR #13 (down from 92 to 0 direct calls). | Phase 0 audit of remaining 4 alias wrappers and cutoff-date calculation sites. |

## Why

`src/rebalance/lib/time_ops.py` is the canonical home for time operations (`now_iso()`, `now_utc()`, `parse_utc_iso()`), which honors the `rebalance.tz_utils` freeze-clock test seam.

Remaining items:
1. Four one-line alias wrappers of `parse_utc_iso`:
   - `_parse_datetime` in `sleuth_reminders.py`
   - `_parse_utc` in `pulse_health.py`
   - `_parse_ts` in `claude_cloud.py`
   - `_parse_status_timestamp` in `index_ops.py`
2. Inline cutoff-date calculations `(now - timedelta(days=N)).isoformat()` re-implemented across 8+ modules.
3. Private-name imports (e.g. `_parse_iso`, `_now`, `_now_utc` in `diagnose.py`).

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Alias wrapper and cutoff helper consolidation](#phase-1--alias-wrapper-and-cutoff-helper-consolidation)
- [Phase 2 — Contract test & lint enforcement](#phase-2--contract-test--lint-enforcement)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `src/rebalance/lib/time_ops.py:66`: `parse_utc_iso(value)`
- `src/rebalance/lib/time_ops.py:46`: `now_utc()`
- `src/rebalance/lib/time_ops.py:51`: `now_iso()`
- `src/rebalance/ingest/sleuth_reminders.py`: `_parse_datetime`
- `src/rebalance/ingest/pulse_health.py`: `_parse_utc`
- `src/rebalance/ingest/claude_cloud.py`: `_parse_ts`
- `src/rebalance/ingest/index_ops.py`: `_parse_status_timestamp`

**Spike / Research approach:**
1. Check if any domain-specific parsers (`gmail._parse_received_at`, `apple_reminders.core_data_timestamp`) should remain untouched (yes, per contract).
2. Propose `cutoff_utc(days: int)` or `cutoff_iso(days: int)` helper in `time_ops.py` to standardize the 8+ inline `(now - timedelta(days=N))` sites.

**Acceptance criteria for Phase 0:**
- Complete inventory of remaining time wrapper sites and cutoff calculations.

## Phase 1 — Alias wrapper and cutoff helper consolidation

- [ ] Add `cutoff_iso(days: int) -> str` / `cutoff_utc(days: int) -> datetime` to `src/rebalance/lib/time_ops.py` if beneficial.
- [ ] Collapse alias wrappers (`_parse_datetime`, `_parse_utc`, `_parse_ts`, `_parse_status_timestamp`) onto direct imports of `parse_utc_iso`.
- [ ] Update private-name imports (`_parse_iso`, `_now`) to public `time_ops` exports.
- [ ] Consolidate cutoff-date sites across `github_scan.py`, `github_knowledge.py`, `note_builder.py`, `index_ops.py`, `next_actions.py`, `sync_snapshot.py`, `querier.py`.

**QA gate:**
- All tests in `tests/test_time_ops.py` and across ingest pass.

## Phase 2 — Contract test & lint enforcement

- [ ] Add AST / contract test in `tests/test_banned_imports.py` asserting no unapproved local datetime parsing helpers exist.
- [ ] Verify freeze-clock seam tests in `tests/test_tz_utils.py` and `tests/test_time_ops.py` pass cleanly.

**QA gate:**
- `pytest tests/` green; zero datetime bypasses across all active modules.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
