---
gh_issue: 31
source: https://github.com/HiQS-Suite/rebalanceOS/issues/31
title: "GH-31 Close coverage gaps: md_parser, note_ingester, slack_users, and MCP tools"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: testing
goal: >
  Write direct unit and behavioral test suites for uncovered core modules (md_parser,
  note_ingester, slack_users, MCP tools, and querier local LLM synthesis path).
effort: 3
complexity: 2
risk: 1
phases: 3
ratings_provisional: true
roadmap_exempt: true
---

# GH-31 — Close Coverage Gaps Across Core Modules

## Status

| What was just completed | What's next |
|---|---|
| First item completed: `diagnose.py` now has 13 tests in `tests/test_diagnose.py`. | Phase 0 audit of remaining zero-direct-test modules: `md_parser.py`, `note_ingester.py`, `slack_users.py`, and MCP tools. |

## Why

While the test suite has 164+ test files, the 2026-08-15 review identified several modules with zero direct behavioral coverage:
1. `src/rebalance/ingest/md_parser.py` + `note_ingester.py`: frontmatter, wikilink, tag, chunking parsing, and hash-delta detection underpin all semantic search downstream.
2. `src/rebalance/ingest/slack_users.py` (214 LOC): 0 tests; mtime cache staleness logic unverified.
3. `src/rebalance/mcp/tools/*` (960 LOC): only `peek_source`/`get_next_actions` are behaviorally tested; `index.py`, `calendar.py`, `onboarding.py`, `hygiene.py` only have AST import guards.
4. `src/rebalance/querier.py`: local-LLM `_synthesize` / fallback path is never executed in tests.
5. `tests/test_web_surface.py`: `PulseWebHtmlContractTests._skip_if_no_html` silently skips assertions if render fails — make it loud / xfail.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Vault parser and ingester test suite](#phase-1--vault-parser-and-ingester-test-suite)
- [Phase 2 — Slack users and Querier synthesis tests](#phase-2--slack-users-and-querier-synthesis-tests)
- [Phase 3 — MCP tool behavioral tests](#phase-3--mcp-tool-behavioral-tests)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `src/rebalance/ingest/md_parser.py`: markdown frontmatter, wikilinks, tags, chunks.
- `src/rebalance/ingest/note_ingester.py`: vault chunking, delta detection, secret redaction.
- `src/rebalance/ingest/slack_users.py`: user mapping and cache management.
- `src/rebalance/mcp/tools/`: MCP tool implementations.
- `src/rebalance/querier.py`: retrieval + synthesis engine.

**Research / Fixture inventory:**
1. Design mock Obsidian vault fixtures (valid frontmatter, missing frontmatter, cyclic wikilinks, nested tags, large code fences).
2. Design mock Slack API / cached JSON fixtures.
3. Review mock LLM provider fixtures for `querier._synthesize`.

**Acceptance criteria for Phase 0:**
- Test plan and fixture structures outlined for each uncovered module.

## Phase 1 — Vault parser and ingester test suite

- [ ] Create `tests/test_md_parser.py`: test frontmatter parsing, wikilink extraction, chunk boundary splitting, and malformed markdown handling.
- [ ] Create `tests/test_note_ingester.py`: test vault scanning, hash delta detection, chunk upserts, and note deletion reconciliation.
- [ ] Coordinate with GH-32 for secret redaction tests in `note_ingester.py`.

**QA gate:**
- `pytest tests/test_md_parser.py tests/test_note_ingester.py` passes with >90% coverage.

## Phase 2 — Slack users and Querier synthesis tests

- [ ] Create `tests/test_slack_users.py`: test cache read/write, expired mtime refresh, and fallback behavior.
- [ ] Create `tests/test_querier_synthesis.py`: test `_synthesize()` with mock LLM responses and fallback triggers on timeout/failure.
- [ ] Update `tests/test_web_surface.py` to make skipped assertions explicit and informative.

**QA gate:**
- `pytest tests/test_slack_users.py tests/test_querier_synthesis.py tests/test_web_surface.py` green.

## Phase 3 — MCP tool behavioral tests

- [ ] Create `tests/test_mcp_tools.py`: behavioral invocation tests for `index.py`, `calendar.py`, `onboarding.py`, and `hygiene.py`.
- [ ] Assert tool JSON schemas match expected parameters and return types.

**QA gate:**
- All MCP tools tested behaviorally in addition to AST import checks.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
