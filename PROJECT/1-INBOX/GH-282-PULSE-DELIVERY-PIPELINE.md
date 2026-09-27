---
gh_issue: 282
source: https://github.com/HiQS-Labs/rebalanceOS/issues/282
title: "GH-282 pulse delivery pipeline: reliable writes, honest liveness, and one owner per path"
status: "Active (Phase 1 implemented in PR #283). Rated 2026-09-26."
created: 2026-09-26
updated: 2026-09-26
owner: noel
doc_type: architecture
goal: >
  Harden the Git Pulse sync delivery pipeline across fleet Macs: establish an honest exit code
  taxonomy (0=OK, 1=Config, 2=Git Error, 70=Render Error, 75=Busy/Skip), add explicit push/pull timeouts,
  replace silent UTC fallback with local Pacific timezone resolution, add bounded jittered retries,
  and transition to disjoint per-device namespaces (`devices/<id>/...`) with reader aggregation.
effort: 65
complexity: 3
risk: 2
phases: 3
ratings_provisional: true
roadmap_exempt: false
---

# GH-282 — Pulse delivery pipeline: reliable writes, honest liveness, and one owner per path

## Status

| What was just completed | What's next |
|---|---|
| Phase 1 implemented in PR #283: honest exit taxonomy (0/1/2/70/75), bounded 120s git timeouts, timezone fallback defaulting to local host timezone, rebase cleanup, and launchd exit 75 skip logging. | Land PR #283, deploy to MacBook Pro 14", then proceed with Phase 2 (bounded jittered retry and per-device namespaces). |

## Why

Hourly delivery fails on multiple Macs due to push collisions on shared files, lock contention, and uncaught timeouts. Currently, git timeouts and exceptions are swallowed and logged as Exit 1 ("config or render error"), and busy locks exit 2 (counted as failure). Furthermore, `pulse_health.py` reports devices as ALIVE even when pulse delivery has failed for days because it only inspects the collector heartbeat.

## Ratings, with reasons

Rated 2026-09-26 per consensus in AgentChorus #132026.

| Field | Value | Why |
|---|---|---|
| `pri` | 80 | High fleet impact: hourly pulse sync repeatedly fails or collides across 4 Macs. |
| `sev` | 70 | Misleading diagnostic reporting and silent delivery failures. |
| `appeal` | 55 | Operator wants reliable hands-free fleet sync across all devices. |
| `effort` | 65 | Phase 1 is clean, localized, and highly testable (~50 lines across 3 files). |

## Implementation Plan

### Phase 1: Diagnostic Honesty & Resilience (Current Scope)
1. **Exit Code Taxonomy**:
   - Update `scripts/pulse_sync.sh` to classify exits cleanly: Exit 0 (OK/no-change), Exit 1 (Config error only), Exit 2 (Git error after retries/timeout), Exit 70 (Render/Python exception), Exit 75 (Busy lock / skip).
2. **Git Timeout & Error Handling**:
   - Update `src/rebalance/lib/git_ops.py` to catch `subprocess.TimeoutExpired` / `OSError` in `publish_git_paths` and return `git_error` + `pending=True`.
   - Add configurable timeout (default 120s, env `REBALANCE_GIT_TIMEOUT`) for `publish_git_paths` and `git_pull_rebase_safe`.
3. **Timezone Fallback**:
   - In `src/rebalance/ingest/pulse.py:965`, remove `or "UTC"` so `_resolve_timezone` correctly falls back to `local_tz()` (America/Los_Angeles).
4. **Doctor Exit 75 Handling**:
   - In `src/rebalance/doctor.py:1269`, treat status `75` as a non-failing skip state (`idle, skipped (75)`).

### Phase 2: Jitter & Namespace Partitioning (Future PR)
- Bounded jittered retry (≤ 3 attempts, 2–20s) and per-device deterministic stagger delay.
- Disjoint namespaces (`devices/<id>/live-pulse.md`).
- Reader aggregation `fleet_view()` and deprecation of committing `latest.json`.

### Phase 3: Multi-Dimensional Liveness (Future PR)
- `devices/<id>/status/<job>.yaml` and collector mirroring.
- `pulse_health.py` `ALIVE_NOT_PUBLISHING` state.
