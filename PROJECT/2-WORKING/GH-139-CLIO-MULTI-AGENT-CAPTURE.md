---
title: "CLIO multi-agent capture: ZCode, Codex, Agy alongside Claude Code"
status: "In progress"
created: 2026-08-31
updated: 2026-08-31
owner: noel
gh_issue: 139
branch: feat/gh139-clio-multi-agent
context_tags: [clio, capture, hooks, launchd, observability]
effort: 2
complexity: 3
risk: 2
phases: 4
goal: "Capture agent prompts from ZCode, Codex (VS Code), and Agy into the same CLIO JSONL and rendered note that Claude Code already feeds, tagging every entry with the agent app name alongside the device name."
non_goals: "No change to clio:id derivation; no rewrite of the exporter's delivery machinery; no capture of agent *responses*; no new log destinations beyond the existing note."
---

# GH-139 — CLIO multi-agent capture

## Table of contents

- [Phase 0 — Prior art review + capture-surface spike](#phase-0--prior-art-review--capture-surface-spike)
- [Phase 1 — Schema v2 (`agent` field) + shared writer + ZCode](#phase-1--schema-v2-agent-field--shared-writer--zcode)
- [Phase 2 — Codex (VS Code agent) capture](#phase-2--codex-vs-code-agent-capture)
- [Phase 3 — Agy (standalone app) capture](#phase-3--agy-standalone-app-capture)
- [Design invariants](#design-invariants)
- [Risks](#risks)

## Status

| What was just completed | What's next |
|---|---|
| Issue [#139](https://github.com/HiQS-Labs/rebalanceOS/issues/139) opened; capture surfaces scouted on one machine (findings below); plan drafted | Phase 0 spike: verify ZCode hook stdin shape, Codex prompt record source, Agy conversation DB schema |

## Background

CLIO is a Claude Code skill that installs a user-scope `UserPromptSubmit` hook appending every
submitted prompt to a centralized JSONL, plus an exporter that renders that JSONL as a
human-readable Markdown note (newest first, ID-deduplicated, conflict-reconciled). Today only
Claude Code feeds it, so prompts typed into the operator's other agent apps never reach the
"second brain" layer.

This effort extends the writer so one JSONL and one rendered note capture prompts from:

1. **ZCode app** (first),
2. **Codex VS Code agent**,
3. **Agy standalone app**,

while Claude Code capture keeps working unchanged — and every entry gains the **agent app name**
next to the **device name** it already records.

Key files today:

- `utils/CLIO/INSTALL.md` — the skill file; heredocs the capture hook and registers it.
- `utils/CLIO/prompt-log-to-md.sh` — the exporter (`clio:id` dedup, manifest receipt, reconciliation).
- `test/clio-capture.sh`, `test/clio-exporter.sh` — existing test surfaces.
- `vscode-extensions/clio` — the sidebar viewer that renders the exported note (downstream consumer; must keep working).

## Phase 0 — Prior art review + capture-surface spike

### Prior art review (why extend CLIO, not build alongside it)

- **CLIO is the canonical prompt-capture subsystem** — it was brought into `utils/CLIO/` as its
  canonical home (recorded in the GH-169 ledger line: *"bring CLIO into rebalanceOS as its
  canonical home"*). The durable-writes marathon (predecessor repo) and GH-156 reconciliation
  work invested the dedup/manifest machinery this plan rides on; duplicating capture elsewhere
  would fork that investment.
- **`vscode-extensions/clio`** is a *viewer* of the rendered note, not a capture path — no overlap.
- **Pulse / `agent_tags.py`** tags already-collected activity rows by source; it does not capture
  prompt text. `daily_synthesis` consumes CLIO's rendered note downstream. Neither competes.
- Conclusion: extend CLIO's writer. >50% overlap with any new subsystem by definition, so the
  deprecation rule in ROUTER.md is satisfied by extending in place.

### Spike checklist (1–2h, findings written back here before Phase 1's QA gate)

- [ ] **ZCode:** confirm the `UserPromptSubmit` hook stdin payload shape (is it the same
  `{"prompt","session_id"}` JSON Claude Code posts?), the exact config location and `enabled: true`
  gate, and that `${CLAUDE_PROJECT_DIR}`/session-id template vars populate for hook scripts.
  Findings:
- [ ] **Codex:** identify the canonical prompt record — a `history.jsonl` (absent on the scout
  machine; check the persistence setting that creates it) vs parsing session rollout JSONLs
  (`{"payload","timestamp","type"}` with `session_meta`/`event_msg` entries). Decide one source of
  record and confirm it covers VS Code extension sessions, not just CLI sessions. Findings:
- [ ] **Agy:** inspect a conversation database under the Agy app-data tree **read-only** (copy
  first if WAL makes live reads risky); confirm where the user's prompt text lives per turn and
  whether a stable per-session id + timestamp can be derived. Findings:
- [ ] Confirm one shared capture writer can serve hook callers (stdin JSON) and tailer callers
  (file/DB polling) without per-agent forks of the cleaning/filter logic. Findings:

**QA gate (Phase 0):** every checkbox above carries a written finding in this doc; any surface
that cannot deliver (stable id + timestamp + prompt text) is escalated before Phase 1 rather than
worked around silently.

## Phase 1 — Schema v2 (`agent` field) + shared writer + ZCode

**Schema v2 (additive only):**

```json
{"timestamp":"…","repo":"…","branch":"…","machine":"…","agent":"zcode","session_id":"…","prompt":"…"}
```

- `agent` ∈ `claude-code` | `zcode` | `codex` | `agy` (display labels stay lowercase-hyphenated).
- `clio:id` stays `session_id:timestamp` — **unchanged on purpose** (changing it re-renders the
  whole note as duplicates and orphans the manifest).

**Work:**

- [ ] Extract the capture logic (cleaning, capture filters, JSONL append, error log) into one
  shared writer installed once, invoked as `… --agent <name>`; the Claude Code hook becomes a thin
  caller with `--agent claude-code`. `utils/CLIO/INSTALL.md` installs the writer + all registrations.
- [ ] Register the ZCode `UserPromptSubmit` hook (config-file hooks with `enabled: true`) calling
  the shared writer with `--agent zcode`; document the enable gate and matcher behavior.
- [ ] Exporter renders `agent` as a third `·`-separated token on the metadata line
  (`machine · branch · agent`); legacy rows (no `agent`) render as `claude-code` — display-only
  default, no stored backfill, and the first token stays `machine` so legacy-unlabelled matching
  in `reconcile_status`/`backfill_plan` keeps working.
- [ ] Exporter header text for **newly created notes** drops the Claude-Code-only wording
  (everything above the marker in existing notes is preserved verbatim by design — history untouched).
- [ ] Update `~`-level uninstall instructions to remove the writer, the Claude Code entry, and the
  ZCode entry without touching unrelated hooks.

**QA gate (Phase 1):**

- [ ] `test/clio-capture.sh` covers: `--agent` stamping, legacy no-`agent` rows, capture filters
  still applying per agent, Claude Code path byte-identical output for the same input.
- [ ] `test/clio-exporter.sh` covers: `agent` rendering, legacy default, unchanged `clio:id`
  derivation, note re-run produces zero duplicates for pre-upgrade JSONL.
- [ ] Real-session verify: one ZCode prompt + one Claude Code prompt land in the JSONL with
  correct `agent` values and render once each in the note.
- [ ] `pytest tests/` full suite green.

## Phase 2 — Codex (VS Code agent) capture

- [ ] Implement a small idempotent tailer (per Phase 0's chosen source of record) that emits new
  Codex prompts as JSONL lines with `agent: "codex"`, `repo`/`branch` resolved from the session's
  project directory when derivable (empty otherwise), riding the existing capture filters.
- [ ] Cursor + delivery semantics mirror the exporter's discipline: cursor is an optimization,
  IDs are the dedup guarantee; a skipped or re-run tailer never duplicates an entry (IDs + note scan).
- [ ] Ship the launchd job (macOS) + install/uninstall lines in `utils/CLIO/INSTALL.md`; the job
  label follows the existing family naming, operator-facing copy uses the functional name.
- [ ] Backfill boundary decided explicitly: on first run the tailer starts **now** (no history
  import) unless the operator opts in — document whichever is chosen.

**QA gate (Phase 2):**

- [ ] Tailer tests (mock rollout/history fixtures under `test/fixtures/`): happy path, malformed
  line, mid-session resume, restart-no-duplicates, capture-filter interaction.
- [ ] Real-session verify: a VS Code Codex prompt lands with `agent: "codex"` and renders once.
- [ ] `pytest tests/` + both CLIO test scripts green.

## Phase 3 — Agy (standalone app) capture

- [ ] Same tailer pattern over Agy's conversation storage (per Phase 0 schema findings), strictly
  read-only: open databases copy-first or in read-only mode so a live Agy session is never
  blocked or corrupted (WAL-safe).
- [ ] Emit `agent: "agy"` lines with the same invariants; dedup rides the ID machinery.
- [ ] Install/uninstall documented in `utils/CLIO/INSTALL.md`; launchd job follows Phase 2's shape.

**QA gate (Phase 3):**

- [ ] Tailer tests with fixture DB copies: new-turn detection, restart-no-duplicates, live-write
  safety (writer not blocked), capture filters.
- [ ] Real-session verify: an Agy prompt lands with `agent: "agy"` and renders once.
- [ ] Full suite green; exporter `--status` reports all four agents' IDs as delivered.

## Design invariants

1. **One JSONL, one note.** Every agent funnels into the same source file and the same rendered
   note; per-agent data never forks the pipeline (filters/transforms in sequence, per GUIDING).
2. **IDs are immutable.** `clio:id = session_id:timestamp` for every agent; the additive `agent`
   field never enters the ID. Collision across agents is theoretically possible and practically
   negligible (uuid session ids + second-precision UTC); covered by a test note, not a format change.
3. **Capture stays best-effort and fast.** The hook never blocks prompt submission (exit 0, errors
   to the error log); tailers degrade to catch-up on next tick.
4. **The viewer extension must survive.** `vscode-extensions/clio` already tolerates `clio:id`
   comments and atomic saves; the only format delta it sees is the extra `· agent` token and
   (new notes only) the header wording.
5. **PII discipline.** Device names, usernames, and vault paths stay in per-device config/launchd
   plists — never in repo docs, issues, or fixtures (fixtures use synthetic values).

## Risks

- **ZCode hook payload drift** — if ZCode's stdin JSON differs from Claude Code's, the shared
  writer needs a small per-agent normalizer; Phase 0 pins this before any code.
- **Codex VS Code sessions may not write the same files as CLI sessions** — Phase 0 must verify
  the IDE path specifically; if the IDE writes nothing observable, fall back to the rollout
  session files and record that in the spike findings.
- **Agy DB schema is undocumented and can move between app updates** — the tailer must fail soft
  (log + skip) on schema drift rather than crash-loop; consider a schema-version probe at startup.
- **Exporter legacy matching** — the `·`-token metadata line is load-bearing for
  `legacy-unlabelled` backfill matching; the agent token must append, never reorder.
