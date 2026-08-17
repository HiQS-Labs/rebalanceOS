---
gh_issue: 30
source: https://github.com/HiQS-Suite/rebalanceOS/issues/30
title: "GH-30 Remove dead code and correct stale architecture docs (ghost MCP tools)"
status: "Completed — shipped in the Build 0.73.0 Subsystem Unification marathon (phase su6) as PR #40 (0.73.0)"
created: 2026-08-16
updated: 2026-08-17
owner: noel
doc_type: hygiene
goal: >
  Remove dead functions/constants (_render_sleuth_groups, CSS composite) and update
  stale documentation references to removed legacy MCP tools (query_notes, query_github_context).
effort: 1
complexity: 1
risk: 1
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-30 — Remove Dead Code & Correct Stale Architecture Docs

## Status

| What was just completed | What's next |
|---|---|
| Issue intake confirming 5 stale references in `ARCHITECTURE.md`/`AGENTS.md` and unused code in `web.py:416` (tested only in `test_web_badges.py:42`). | Phase 0 verification of dead code consumers and documentation references. |

## Why

1. `src/rebalance/web.py:416`: `_render_sleuth_groups` (~59 LOC) is dead production code: defined, never called in the runtime app (only exercised in `tests/test_web_badges.py:42`).
2. `scripts/pulse_web.py`: dead `CSS` composite constant unreferenced.
3. `ARCHITECTURE.md`: lines ~198, ~385, ~510 still list `query_notes` and `query_github_context` as live MCP tools.
4. `src/rebalance/mcp/tools/index.py:286`: docstring incorrectly claims legacy per-source tools still exist.
5. `AGENTS.md`: mentions `query_notes`/`query_github_context` in older retrieval table.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Dead code removal & test alignment](#phase-1--dead-code-removal--test-alignment)
- [Phase 2 — Documentation & docstring reconciliation](#phase-2--documentation--docstring-reconciliation)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `src/rebalance/web.py:416`: `def _render_sleuth_groups() -> str:`
- `tests/test_web_badges.py:42`: test exercising `_render_sleuth_groups`.
- `src/rebalance/mcp/tools/index.py:280-290`: `semantic_query` tool definition.
- `ARCHITECTURE.md` & `AGENTS.md`: tool tables.

**Research / Inventory:**
1. Confirm `_render_sleuth_groups` has no runtime callers in `src/` or `scripts/`.
2. Search all references to `query_notes` and `query_github_context` across `.md` and `.py` files.

**Acceptance criteria for Phase 0:**
- Complete list of target lines in code and docs confirmed.

## Phase 1 — Dead code removal & test alignment

- [ ] Delete `_render_sleuth_groups` from `src/rebalance/web.py`.
- [ ] Clean up orphan test assertions in `tests/test_web_badges.py`.
- [ ] Delete unused `CSS` composite constant from `scripts/pulse_web.py`.
- [ ] Remove any leftover untracked test database artifacts (`tests/rebalance.db`).

**QA gate:**
- `ruff check .` and `pytest tests/test_web.py tests/test_web_badges.py` pass cleanly.

## Phase 2 — Documentation & docstring reconciliation

- [ ] Update `ARCHITECTURE.md` Tool Surface and Read-side tables to reflect `semantic_query` as canonical and remove ghost tools.
- [ ] Update `AGENTS.md` to note `query_notes`/`query_github_context` were unified into `semantic_query`.
- [ ] Update docstring in `src/rebalance/mcp/tools/index.py`.
- [ ] Run `utils/pdda/pdda.sh governance` to ensure zero dead references.

**QA gate:**
- `pdda.sh governance` and `pdda.sh run` pass with zero documentation errors.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
