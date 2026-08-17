---
title: "Build 0.74.0 Hardened Core Marathon Scope"
status: "Draft"
created: 2026-08-16
updated: 2026-08-16
owner: noel
goal: "Autonomous marathon execution plan for Release 0.74.0 Hardened Core"
effort: 3
complexity: 2
risk: 3
phases: 3
ratings_provisional: false
roadmap_exempt: false
---

# Build 0.74.0 — Hardened Core Scope

## Status

| What was just completed | What's next |
|---|---|
| Phase briefs and MARATHON.yaml generated following Relay XYZ consult with Codex. | Preflight and dry run validation of marathon plan. |

## Overview

Build 0.74.0 hardens security invariants, expands core behavioral test coverage, and enforces repository hygiene:
- Phase `hc1` (#31): Close coverage gaps with direct behavioral tests for `md_parser.py`, `note_ingester.py`, `slack_users.py`, MCP tools, and querier local LLM synthesis.
- Phase `hc2` (#32): Implement secret redaction regression test suite, chunk purge/re-index command for existing databases, and frontmatter `index: false` exclusion.
- Phase `hc3` (#33): Enforce gitignore rules for transcripts, add repo hygiene contract test, and verify upstream archival checklist.

## Execution

```bash
.xyz/relay-automation/marathon.sh \
  --plan PROJECT/2-WORKING/BUILD-0.74.0-HARDENED-CORE/MARATHON.yaml \
  --pre-advance-cmd "pytest tests/ -q" \
  --dry-run
```
