# Recon Map — UTC Timezone Boundary & System-wide Timekeeping

Commit: ed320289f78abe2e5f0228457a95b07a614c2d00 · Date: 2026-09-06 · Mode: graph+read+grep · Lanes: A (Entry/Call), B (State/Data), C (Contracts/Boundaries), D (Build/Ops)

## Table of contents
- Subject and change class
- Seams and call paths
- State and contracts
- Key findings and timekeeping flaws
- Build, failure and operations
- Unknowns
- Current-state radius

## Subject and change class
System-wide audit and architecture for temporal boundary, timezone resolution, and timestamp query/storage semantics across Rebalance (`src/rebalance/**`, `scripts/**`, `.agents/skills/**`).
Change class: Cross-module query/filtering contract and timezone harmonization. Raw store remains ISO-8601 UTC; all temporal windowing, day-bucketing, SQLite lookbacks, and operator queries convert through a canonical operator local timezone window.

## Seams and call paths
| Seam | Location | Crosses | Breaks if |
|---|---|---|---|
| Local TZ resolution | `src/rebalance/lib/time_ops.py:152` | Env `REBALANCE_TZ` → `/etc/localtime` → UTC | Operator config (`rbos.config`) has `pulse_timezone` but `time_ops` ignores it |
| Local day bounds helper | `src/rebalance/ingest/pulse.py:110` | Python local day → UTC interval `[start_utc, end_utc)` | Pattern private to `pulse.py`; other modules reinvent or use naive string/UTC filters |
| SQLite `date('now')` lookbacks | `src/rebalance/ingest/index_ops.py:897`; `ingest/db/github.py:33`; `ingest/github_watch.py:270` | SQLite internal `date('now', ?)` → UTC midnight | Evaluates UTC date in SQLite; shifts lookback window by +1 day after 5:00 PM PDT |
| Prompt & CLIO queries | `src/rebalance/ingest/clio.py:120`; `mcp/tools/index.py` | UTC ISO timestamp `clio_prompts` → local day queries | Queries filtering `timestamp LIKE 'YYYY-MM-DD%'` lose all evening prompts (stored in next UTC day) |
| Calendar event dates | `src/rebalance/cli/calendar.py:485,554`; `mcp/tools/calendar.py:89,185` | Mixed ISO offsets vs UTC `Z` in `calendar_events` | Prefix matching (`start_time LIKE 'YYYY-MM-DD%'`) fails on UTC-formatted timestamps |
| Claude Cloud local day | `src/rebalance/ingest/claude_cloud.py:203,220` | `time_ops.now_utc().astimezone().date()` | Uses OS runtime timezone, bypassing `REBALANCE_TZ` and operator config |
| Doctor staleness check | `src/rebalance/doctor.py:611` | `(now_utc().date() - latest_dt.date()).days` | Compares raw UTC dates; false-stale or off-by-one across UTC midnight boundary |
| Next Actions date resolution | `src/rebalance/ingest/next_actions.py:1169,1427` | `pulse_timezone` → `local_tz()` fallback to UTC | Falls back to UTC date instead of local date if tz lacks `utcoffset` |

## State and contracts
- **Raw Storage Invariant**: Storage columns (`clio_prompts.timestamp`, `github_commits.committed_at`, `github_activity.created_at`, `semantic_documents.created_at`, `ranked_next_actions.computed_at`) MUST remain timezone-aware UTC ISO-8601 (`YYYY-MM-DDTHH:MM:SSZ` or `+00:00`). No local naive timestamps in the database.
- **Query Boundary Invariant**: Any query against a local date (e.g. "today", "yesterday", or "2026-09-05") must convert the operator's local day `[local_midnight, next_local_midnight)` into UTC ISO bounds `[start_utc_iso, end_utc_iso)` in Python, then query SQLite with `WHERE timestamp >= ? AND timestamp < ?`.
- **No SQLite `date('now')` without local offset**: SQLite's native `date('now')` is UTC. Lookback expressions like `date('now', '-14 days')` must either use Python-computed UTC cutoff bounds (`now_utc() - timedelta(days=N)`) or SQLite's `date('now', 'localtime', ?)` / `datetime('now', 'localtime')`.

## Key findings and timekeeping flaws
1. **The 5:00 PM PDT Drop-off (UTC Day Boundary Flaw)**:
   - At 17:00 PDT (00:00 UTC), the UTC calendar day advances.
   - Any query using `WHERE timestamp LIKE 'YYYY-MM-DD%'` or `date(timestamp) = 'YYYY-MM-DD'` drops all activity generated in the operator's evening (17:00–23:59 PDT).
   - Confirmed in CLIO prompt searches and daily synthesis: evening prompts on 2026-09-05 were stored with timestamp `2026-09-06T03:xx:xxZ` and omitted from `2026-09-05%` filters.
2. **Timezone Config Fragmentation**:
   - `temp/rbos.config` holds `pulse_timezone`.
   - `lib/time_ops.py:local_tz()` checks `REBALANCE_TZ` env var, then `/etc/localtime`, but never reads `temp/rbos.config`.
   - `claude_cloud.py` uses bare `.astimezone()` (OS timezone).
   - Need a single centralized `get_operator_timezone()` in `lib/time_ops.py` that resolves: `REBALANCE_TZ` → `temp/rbos.config` (`pulse_timezone` / `timezone`) → `/etc/localtime` → `UTC`.
3. **Private Day-Bounds Logic in `pulse.py`**:
   - `pulse.py` wrote a clean `_local_day_bounds(tz)` and `_utc_iso_floor(dt)` function, but it is private to `pulse.py`.
   - It should be promoted to `lib/time_ops.py` as `get_local_day_utc_bounds(target_date_or_now, tz=None) -> tuple[str, str]` and reused across `doctor.py`, `clio.py`, `calendar.py`, `daily_report.py`, `next_actions.py`, and MCP tools.
4. **Doctor Age / Staleness Calculation**:
   - `src/rebalance/doctor.py:611` calculates age via `(now_utc().date() - latest_dt.date()).days`.
   - Compares UTC dates directly. A sync at 16:30 PDT (23:30 UTC) checked at 08:30 PDT the next morning (15:30 UTC) reports `1 days ago` despite being only 16 hours old. Should measure elapsed duration `(now_utc() - latest_dt).total_seconds() / 86400` or local date difference.

## Build, failure and operations
- **Test Seam**: `src/rebalance/lib/time_ops.py:_current_time` provides the freeze-clock seam. Tests must patch `time_ops._current_time` or `time_ops.now_utc`.
- **Existing tests**: `tests/test_time_ops.py`, `tests/test_pulse.py`, `tests/test_calendar.py`, `tests/test_next_actions.py`.
- **Rollback Safety**: Purely additive Python helper functions and SQL parameter bindings. Zero database migrations or schema alterations required.

## Unknowns
| Unknown | Why it matters | What settles it |
|---|---|---|
| Historical calendar events with mixed UTC vs offset strings | Some legacy rows may have raw local strings without TZ indicator | Quick SQL audit of `calendar_events.start_time` formats |
| Non-macOS / Docker deployments without `/etc/localtime` | Fallback precedence when no config, env var, or system symlink exists | Verified: falls back gracefully to UTC in `time_ops.py` |

## Current-state radius
`src/rebalance/lib/time_ops.py`, `src/rebalance/ingest/pulse.py`, `src/rebalance/ingest/index_ops.py`, `src/rebalance/ingest/clio.py`, `src/rebalance/ingest/calendar.py`, `src/rebalance/ingest/claude_cloud.py`, `src/rebalance/ingest/next_actions.py`, `src/rebalance/doctor.py`, `src/rebalance/cli/calendar.py`, `src/rebalance/mcp/tools/calendar.py`, and `.agents/skills/daily/**`.
