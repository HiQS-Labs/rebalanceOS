---
title: "SQLite gateway routing — retire the nine direct-connect bypasses"
status: "Shipped"
created: 2026-08-30
updated: 2026-08-30
owner: noel
gh_issue: 136
goal: "Route every direct sqlite3.connect outside the two gateway directories through a gateway, behind a CI ratchet that pins the exact baseline and only lets it shrink."
release: "0.76.0 + 0.79.0"
---

# GH-136 — SQLite gateway routing

**TOC**

- [Settled up front](#settled-up-front)
- [Status](#status)
- [Phase 0 — settle and pin (done)](#phase-0--settle-and-pin-done)
- [Phase 1 — route the five read-only sites](#phase-1--route-the-five-read-only-sites)
- [Phase 2 — route the three untracked src sites](#phase-2--route-the-three-untracked-src-sites)
- [Phase 3 — decide utils/py and gh250](#phase-3--decide-utilspy-and-gh250)
- [Phase 4 — tighten to zero and close](#phase-4--tighten-to-zero-and-close)
- [Verification commands](#verification-commands)
- [Links](#links)

## Settled up front

Two questions the issue asked to settle before scoping; both are closed and must not
be relitigated without new evidence:

1. **Do the two gateways address the same database files? No — by design.**
   `rebalance.ingest.db` opens whatever explicit path it is given (callers resolve
   `REBALANCE_DB` → the repo's `rebalance.db`). `hiqs.db` defaults to
   `~/Library/Application Support/hiqs/hiqs.db`; every call site in `HiQS/` uses that
   default and nothing under `HiQS/` references `REBALANCE_DB` or `rebalance.db`. The
   ROADMAP's HiQS entry states the intent: clean-room rebuild, own DB at the
   app-data path, staged to spin out to its own repo. **No convergence work**; the
   answer is recorded in `ROUTER.md` → "Canonical rules" (issue acceptance
   criterion 2).
2. **Does the read-only helper exist? Yes.** `db_connection_readonly()` lives at
   `src/rebalance/ingest/db/connection.py` (landed via PR #40, the 0.73.0 Subsystem
   Unification marathon; `sleuth_reminders.py` already uses it). Phases below only
   *route*, never *add*.

## Status

| What was just completed | What's next |
|---|---|
| All four phases shipped 2026-08-30: gateway question settled + ratchet live (0.76.0); five read-only sites, three src sites routed; four reasoned exemptions; baseline `{}` — no unexempted direct connect remains | Nothing — issue closes with the routing PR; future bypasses are CI-blocked by the ratchet |

## Phase 0 — settle and pin (done)

- [x] Answer the gateway question (different files, by design — recorded in `ROUTER.md`)
- [x] Post the two corrections on the issue (helper exists; gateway answer)
- [x] Ratchet in `utils/pdda/check_banned_imports.py` (`--check` / `--update-baseline`;
      identity = path + count; additions **and** stale shrinks fail; reads fail closed)
- [x] Exact baseline `utils/pdda/sqlite_connect_baseline.json`: 9 files / 12 sites
- [x] CI step in the `lint` job (issue acceptance criterion 3)
- [x] Constraint tests in `tests/test_sqlite_gateway_ratchet.py` (7)

## Phase 1 — route the five read-only sites (done)

All five already open `mode=ro` URIs; each becomes
`with db_connection_readonly(path) as conn:`. The helper never creates the parent
directory or file, and callers that treat a missing DB as empty must keep checking
existence first (the helper's docstring says the same).

- [x] `src/rebalance/ingest/apple_reminders.py:316`
- [x] `src/rebalance/ingest/apple_reminders.py:776`
- [x] `src/rebalance/ingest/apple_reminders.py:980`
- [x] `src/rebalance/ingest/ask_self_scan.py:148`
- [x] `src/rebalance/doctor.py:2149`
- [x] Tighten the baseline (`--update-baseline`), review the diff, keep CI green

## Phase 2 — route the three untracked src sites (done)

- [x] `src/rebalance/ingest/sleuth_grouping.py:359` (writable connect — use
      `db_connection`/`get_connection`; confirm schema-ensure expectations first)
- [x] `src/rebalance/web.py:1936` (aliased `_sqlite3.connect` — same rule)
- [x] `src/rebalance/mcp/server.py:38` (probe-and-close — decide whether the gateway
      fits a connection-liveness probe or warrants an explicit written exemption)
- [x] Tighten the baseline

## Phase 3 — decide utils/py and gh250 (done — exemptions)

The issue allows either routing or a written exemption — silence is what produced
these two.

- [x] `utils/gh250/reclaim.py:145` — route or exempt with reason
- [x] `utils/py/releases_app.py:402,3430` — route or exempt with reason (note the
      `isolation_level=None` autocommit expectations before routing)
- [x] `utils/py/releases_cycle.py:43` — route or exempt with reason
- [x] Record exemptions, if any, beside the baseline (not in an issue comment)

## Phase 4 — tighten to zero and close (done)

- [x] Baseline empty (or exemptions-only); `--check` green
- [x] Issue acceptance criterion 1 holds:
      `grep -rn "sqlite3.connect" --include="*.py" src/ utils/ HiQS/` returns hits
      only inside `src/rebalance/ingest/db/`, `HiQS/hiqs/`, tests, or exempted files
- [x] Close #136; move this doc to `3-COMPLETED`

## Verification commands

```bash
python utils/pdda/check_banned_imports.py --check   # ratchet: must be green
python utils/pdda/check_banned_imports.py --update-baseline  # only when retiring debt
pytest tests/test_sqlite_gateway_ratchet.py
pytest tests/
```

## Links

- Issue: [#136](https://github.com/HiQS-Labs/rebalanceOS/issues/136)
- Ratchet owner per #126: `utils/pdda/check_banned_imports.py`
- Related: [#126](https://github.com/HiQS-Labs/rebalanceOS/issues/126) (wider
  banned-import ratchet — its Phase 2/3 generalize what Phase 0 here landed for one
  rule), #27 (the closed cleanup this finishes)
