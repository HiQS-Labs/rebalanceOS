---
gh_issue: 27
source: https://github.com/HiQS-Suite/rebalanceOS/issues/27
title: "GH-27 Deduplicate persistence/upsert paths across collectors"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: code-quality
goal: >
  Extract shared persistence helpers for SQLite upserts, readonly connections, and table existence checks,
  eliminating duplicate SQL execution loops across Gmail, GitHub knowledge, Sleuth, and Focus 5.
effort: 3
complexity: 2
risk: 2
phases: 3
ratings_provisional: true
roadmap_exempt: true
---

# GH-27 — Deduplicate Persistence/Upsert Paths Across Collectors

## Status

| What was just completed | What's next |
|---|---|
| Issue intake and verified duplicate persist loops in `gmail.py` and `github_knowledge.py`. | Phase 0 survey of upsert patterns and helper signatures in `src/rebalance/ingest/db/`. |

## Why

Collectors frequently copy-paste database persistence boilerplate:
1. `src/rebalance/ingest/gmail.py`: Pull path (258–308) and push path (384–409) duplicate the identical 9-column `INSERT OR REPLACE INTO email_messages`.
2. `src/rebalance/ingest/github_knowledge.py:537-730`: Issues and PRs persist loops share 24 identical columns in ~100-line blocks.
3. Generic upsert loops (`with db_connection → for item → INSERT OR REPLACE`) repeated across 8+ collectors.
4. `_table_exists()` defined in `pulse.py` and `sleuth_reminders.py`, plus inline checks in `apple_reminders.py`, `note_ingester.py`, `project_classifier.py`, and `doctor.py`.
5. `sqlite3.connect("file:...?mode=ro", uri=True)` repeated at 5 sites with duplicated file-exists checks.
6. `sleuth_reminders.py` opens raw `sqlite3.connect` instead of `db_connection()`.
7. `focus5_scan.py:734,810`: duplicate `focus5_roster` INSERT queries.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Core DB helpers: table_exists & readonly connection](#phase-1--core-db-helpers-table_exists--readonly-connection)
- [Phase 2 — Collector persist loop deduplication](#phase-2--collector-persist-loop-deduplication)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `src/rebalance/ingest/db/connection.py`: `db_connection(database_path, schema_fn)` context manager.
- `src/rebalance/ingest/db/`: module package for database interactions.
- `src/rebalance/ingest/gmail.py`: pull and push message writers.
- `src/rebalance/ingest/github_knowledge.py`: issue and PR sync loops.

**Research questions:**
1. Where should `table_exists(conn, table_name)` and `db_connection_readonly(path)` live? (In `src/rebalance/ingest/db/connection.py`).
2. Design a clean, generic batch upsert helper `upsert_rows(conn, table, columns, rows, conflict_key)` or record builder.

**Acceptance criteria for Phase 0:**
- Signatures and interfaces for shared persistence helpers drafted and verified against existing table schemas.

## Phase 1 — Core DB helpers: table_exists & readonly connection

- [ ] Add `table_exists(conn: sqlite3.Connection, table_name: str) -> bool` to `src/rebalance/ingest/db/connection.py`.
- [ ] Add `db_connection_readonly(database_path: Path | str)` context manager to `src/rebalance/ingest/db/connection.py`.
- [ ] Replace custom `_table_exists` implementations across `pulse.py`, `sleuth_reminders.py`, `apple_reminders.py`, `note_ingester.py`, `project_classifier.py`, and `doctor.py`.
- [ ] Replace raw `mode=ro` SQLite connections in `apple_reminders.py`, `ask_self_scan.py`, `doctor.py`.

**QA gate:**
- Unit tests in `tests/test_db_connection.py` verify helpers against in-memory and disk DBs.

## Phase 2 — Collector persist loop deduplication

- [ ] Deduplicate Gmail message persistence in `src/rebalance/ingest/gmail.py` into a single `_persist_email_message()` helper.
- [ ] Deduplicate `github_knowledge.py` issue/PR loops by extracting shared item record builder and upsert step.
- [ ] Route `sleuth_reminders.py` through standard `db_connection(..., ensure_sleuth_schema)`.
- [ ] Deduplicate `focus5_roster` INSERT in `focus5_scan.py`.

**QA gate:**
- `pytest tests/test_gmail.py tests/test_github_knowledge.py tests/test_sleuth_reminders.py tests/test_focus5_scan.py` all green.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
