---
gh_issue: 29
source: https://github.com/HiQS-Suite/rebalanceOS/issues/29
title: "GH-29 Mount web app in pulse server + extract the shared read layer"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: presentation
goal: >
  Extract the 6 duplicated SQL read queries into a single shared query layer,
  unify remaining unmounted routes between scripts/pulse_server.py and web.py, and deduplicate badge CSS.
effort: 3
complexity: 3
risk: 2
phases: 3
ratings_provisional: true
roadmap_exempt: true
---

# GH-29 — Mount Web App in Pulse Server + Shared Read Layer

## Status

| What was just completed | What's next |
|---|---|
| Issue intake clarifying that while `pulse_server.py:73-91,101-205` mounts a subset of routes, 6 duplicate SQL query families remain across surfaces, and full router unification is needed. | Phase 0 architecture review of router inclusion and shared read layer design. |

## Why

Seven separate presentation surfaces render the same underlying activity data (TUI `dashboard.py`, HTML `pulse_web.py`, markdown `pulse.py`, Obsidian note `note_builder.py`, web `/focus-5`, Focus5Float Swift app, Gemini daily synthesis).

Current issues:
1. `scripts/pulse_server.py` re-declares 20 route wrappers by hand with partial route coverage: `/settings` exists only on :8767, while `/api/zapier/*` and `/api/focus5/open` exist only on the web app.
2. Six duplicated SQL query families (org activity rollup, recent GitHub activity, recent vault notes, calendar today/upcoming, recent email, recent Figma) are forked between `scripts/dashboard.py`, `ingest/pulse.py`, and `ingest/note_builder.py`.
3. Badge CSS styling is duplicated and drifted (`web.py:253` solid vs `pulse_web.py:1914` tinted).
4. What's Next markup vocabulary is duplicated between `web.py` and `pulse_web.py`.
5. Duplicate navigation links in `web_components.render_sidebar`.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Extract shared SQL read layer](#phase-1--extract-shared-sql-read-layer)
- [Phase 2 — Route mount & parity in pulse_server.py](#phase-2--route-mount--parity-in-pulse_serverpy)
- [Phase 3 — UI component token & markup deduplication](#phase-3--ui-component-token--markup-deduplication)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `scripts/pulse_server.py:73-207`: router definitions and endpoints.
- `src/rebalance/web.py`: canonical FastAPI application with router definitions.
- `scripts/dashboard.py:fetch_*`: SQL query layer for TUI.
- `src/rebalance/ingest/pulse.py`: SQL query layer for pulse markdown.
- `src/rebalance/ingest/note_builder.py:get_all_repo_activity_by_org`: duplicate of `dashboard.fetch_org_activity`.

**Research questions:**
1. Design `src/rebalance/ingest/db/queries.py` (or `activity_queries.py`) as the single read interface.
2. How should `pulse_server.py` include `web.py` routers so that `/settings`, `/api/zapier/*`, and static assets are 100% symmetric?

**Acceptance criteria for Phase 0:**
- Signatures for shared query layer specified.
- Route parity inventory confirmed.

## Phase 1 — Extract shared SQL read layer

- [ ] Create `src/rebalance/ingest/db/queries.py` containing:
  - `fetch_org_activity(conn, ...)`
  - `fetch_recent_github_activity(conn, ...)`
  - `fetch_recent_vault_notes(conn, ...)`
  - `fetch_calendar_events(conn, ...)`
  - `fetch_recent_emails(conn, ...)`
  - `fetch_recent_figma(conn, ...)`
- [ ] Refactor `scripts/dashboard.py`, `src/rebalance/ingest/pulse.py`, and `src/rebalance/ingest/note_builder.py` to import from `queries.py`.

**QA gate:**
- Schema changes tested against single query layer; TUI and pulse outputs verified identical.

## Phase 2 — Route mount & parity in pulse_server.py

- [ ] Mount complete `src/rebalance/web.py` routers inside `scripts/pulse_server.py`.
- [ ] Ensure `/settings`, `/api/zapier/*`, `/focus-5.json`, and static asset routes are available symmetrically on both servers.

**QA gate:**
- `tests/test_web_surface.py` and `tests/test_pulse_server.py` pass; all endpoints return HTTP 200.

## Phase 3 — UI component token & markup deduplication

- [ ] Unify badge CSS into `RB_BADGE_CSS` in `src/rebalance/web_components.py`.
- [ ] Share What's Next row markup structure between `web.py` and `pulse_web.py`.
- [ ] Clean up duplicate sidebar navigation links.
- [ ] Remove dead `CSS` composite in `pulse_web.py`.

**QA gate:**
- Visual layout and HTML contracts verified via `test_web_surface.py`.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
