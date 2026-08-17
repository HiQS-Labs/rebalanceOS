---
gh_issue: 32
source: https://github.com/HiQS-Suite/rebalanceOS/issues/32
title: "GH-32 Pre-embed secret redaction in vault ingest & regression test (known gap #5)"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: bugfix
goal: >
  Pin the pre-embed secret redaction in vault ingest with comprehensive regression tests,
  implement a re-index/purge command for existing secret-bearing chunks, and support frontmatter index: false.
effort: 2
complexity: 2
risk: 4
phases: 3
ratings_provisional: true
roadmap_exempt: true
---

# GH-32 — Pre-Embed Secret Redaction in Vault Ingest

## Status

| What was just completed | What's next |
|---|---|
| Redaction implementation exists in `note_ingester.py` (`_redact_secrets`), but currently has zero regression tests pinning it, and existing unchanged notes skip re-redaction. | Phase 0 verification of regex patterns, re-index purge mechanics, and fixture test design. |

## Why

A vault note containing a live API credential was previously indexed and returnable via `semantic_query()`, exposing credentials to any agent calling the tool (AGENTS.md Known Gap #5).

Current state:
1. `_redact_secrets()` is implemented in `src/rebalance/ingest/note_ingester.py:76-222` with `[REDACTED]` markers, covering GitHub PATs, OpenAI keys, AWS keys, Slack tokens, Google AI tokens, Bearer tokens, and long hex strings.
2. **Zero tests exist** to ensure secrets cannot leak into `chunks`, `embeddings`, `semantic_documents`, or `semantic_query`. A broken regex would slip through CI silently.
3. **Existing chunk vulnerability**: `note_ingester.py:165-182` skips unchanged notes based on hash matching, meaning previously indexed credentials remain in `chunks` and `semantic_documents` until explicitly purged or re-indexed.
4. Frontmatter `index: false` or path-exclusion list is not yet implemented.
5. Exposed credential rotation is tracked as part of upstream transition.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Regression test suite with planted secret fixtures](#phase-1--regression-test-suite-with-planted-secret-fixtures)
- [Phase 2 — Re-index & secret purge command](#phase-2--re-index--secret-purge-command)
- [Phase 3 — Frontmatter exclusion & semantic_index unification](#phase-3--frontmatter-exclusion--semantic_index-unification)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `src/rebalance/ingest/note_ingester.py:76`: `_redact_secrets(text: str) -> str`
- `src/rebalance/ingest/note_ingester.py:165-182`: hash-based note skip check.
- `src/rebalance/ingest/note_ingester.py:222`: chunk body redaction before storage/embedding.
- `src/rebalance/ingest/semantic_index.py`: unified cross-source semantic document indexing.
- `AGENTS.md`: Known MCP Tool Gap #5 ("Fix before next vault ingest").

**Research questions:**
1. List all pattern classes in `_SECRET_PATTERNS` (`ghp_`, `gho_`, `sk-`, `AKIA...`, `AIza...`, `xox[bap]-`, Bearer tokens, 40/64-char hex strings).
2. Design a clean re-scan / purge utility: e.g. `rebalance ingest vault --force-rechunk` to re-redact and re-embed existing vaults.
3. Ensure redaction produces predictable replacement text `[REDACTED:<type>]` or `[REDACTED]` without truncating surrounding prose.

**Acceptance criteria for Phase 0:**
- Test fixture with synthetic secret patterns created without using any real secret values.
- Re-index mechanism specified.

## Phase 1 — Regression test suite with planted secret fixtures

- [ ] Create `tests/test_secret_redaction.py`.
- [ ] Test `_redact_secrets()` against synthetic keys:
  - GitHub PATs (`ghp_...`, `gho_...`)
  - OpenAI / Anthropic keys (`sk-...`, `sk-ant-...`)
  - AWS access keys (`AKIA...`)
  - Google API keys (`AIza...`)
  - Slack tokens (`xoxb-...`, `xoxp-...`)
  - Bearer header values
- [ ] Assert that none of the planted raw secrets appear in `chunks.body`, `semantic_documents.content`, or `semantic_query` results.

**QA gate:**
- `pytest tests/test_secret_redaction.py -v` green; zero secret pattern regressions.

## Phase 2 — Re-index & secret purge command

- [ ] Add support for `--force-rechunk` or `--reindex-secrets` in `note_ingester.py` to reprocess all existing notes and sanitize already-stored chunk bodies in `rebalance.db`.
- [ ] Update `semantic_documents` projection to synchronize with newly redacted chunk text.

**QA gate:**
- Running re-index against existing DB cleans all legacy un-redacted chunks.

## Phase 3 — Frontmatter exclusion & semantic_index unification

- [ ] Support `index: false` or `semantic_index: false` in note YAML frontmatter to completely skip indexing sensitive notes.
- [ ] Support folder/path exclusion in vault configuration (e.g. `Private/`, `Archive/`).
- [ ] Verify `semantic_index.py` enforces redaction consistently across all document types.

**QA gate:**
- Notes marked `index: false` produce 0 rows in `chunks` and `semantic_documents`.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
