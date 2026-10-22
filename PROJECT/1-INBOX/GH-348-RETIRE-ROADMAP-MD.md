---
gh_issue: 348
source: https://github.com/HiQS-Labs/rebalanceOS/issues/348
title: "Retire ROADMAP.md: make the RELEASES SQLite ledger the only work ledger (with #329 as phase 1)"
status: "Proposed (1-INBOX) — recon in progress"
created: 2026-10-21
updated: 2026-10-21
owner: noel
doc_type: refactor
goal: >
  Stop hand-editing ROADMAP.md. Install the current XYZ Forge RELEASES overlay (#329), migrate
  releases.db, import the final ROADMAP.md rows, and switch every reader/writer to the DB the way
  XYZ Forge already did for itself (GH-269), so the ledger can no longer drift from GitHub state.
---

# GH-348 — Retire ROADMAP.md for the RELEASES SQLite ledger

## Status

| What was just completed | What's next |
|---|---|
| Issue filed 2026-10-21 after #345 (four closed issues still "In progress"). Task clone provisioned off `origin/development` @ `44c318d`. | Recon (Forge GH-269 prior art, callers, schema gap), then the surgical plan and Codex plan QA. |

## Tracked issues

| Issue | Scope | Depends on | Rating (P/S/A/E) | State | PR |
|---|---|---|---|---|---|
| [#329](https://github.com/HiQS-Labs/rebalanceOS/issues/329) | Phase 1 — current Forge RELEASES overlay via the supported vendor path; `releases.db` migrate; `.xyz-pin` bump | — | 75/60/50/45 (provisional, from the issue, 2026-10-13) | recon | — |
| [#348](https://github.com/HiQS-Labs/rebalanceOS/issues/348) | Phase 2 — final import, flip readers/writers to the DB, rewrite governance docs, retire the file | #329 | 70/55/50/25 | recon | — |

## Why

`ROADMAP.md` is the source of truth; `releases.db` mirrors it one way (`releases roadmap sync`). Nothing
reconciles the markdown against GitHub, so it drifts (#345: #325/#334/#336/#338 listed "In progress"
after merge), and this repo's old `releases_app.py` lacks the verbs the governed workflows need (#329).

## Rating rationale (2026-10-21)

- **#348 — 70/55/50/25.** Severity 55: ledger drift misleads planning and agents (ROUTER step 4 sends
  every session to "In progress"), no data loss. Priority 70: user-requested now; every merge adds drift.
  Appeal 50 (neutral; no user score). Effort 25: ~10 tools/tests/CI plus ~8 governance docs plus a migration.
- **#329 — 75/60/50/45** kept as filed (provisional): blocks `/merge-cleanup` and `/start-task` ledger steps.
- **Recurrence (last 14 days vs prior 14):** 2026-10-07..21 — #345 roadmap drift (1 incident, 4 rows),
  #327 batch ledger-gate failure (1); 2026-09-23..10-06 — none found in issues. Trend: low count, unknown
  beyond issue search.

## Key concepts

- Forge prior art: `XYZ-forge` 9e5c79979 (GH-269) deleted its `ROADMAP.md` and made `pdda.sh`,
  `releases_app.py`, `wave_reconcile.py` and the marathon planner read `releases.db` when the file is absent.
- Writers after the flip: `releases roadmap add / update / move / rate / repoint` only.

## Plan

Pending recon.
