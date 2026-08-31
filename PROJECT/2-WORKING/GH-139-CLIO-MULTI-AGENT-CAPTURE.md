---
title: "CLIO multi-agent capture: ZCode, Codex, Agy alongside Claude Code"
status: "In progress"
created: 2026-08-31
updated: 2026-08-31
owner: noel
gh_issue: 139
branch: feat/gh139-clio-multi-agent
reviewed: "agy relay r1 2026-08-31: changes requested (1 Blocker / 2 Shoulds / 1 Nit) — all applied; agy r2 2026-08-31: Approved (5/5 confirmed)"
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
| Issue [#139](https://github.com/HiQS-Labs/rebalanceOS/issues/139) opened; surfaces scouted; plan drafted; **agy relay r1 reviewed — changes requested (1 Blocker / 2 Shoulds / 1 Nit), all applied** (Agy store corrected to JSONL transcripts; tailer JSONL-dedup requirement added; viewer-regression + tailer-restart gates added; timestamp-normalization spike item added) | Phase 0 spike: verify ZCode hook stdin shape, Codex prompt record source, Agy transcript `source`/`created_at` semantics; then agy r2 confirmation |

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
- [ ] **Timestamp normalization (all sources).** `clio:id` embeds the timestamp string verbatim, so
  every source must be normalized **at capture time** to UTC, second-precision ISO-8601
  (`YYYY-MM-DDTHH:MM:SSZ`, exactly what the Claude hook's `date -u` emits) — a source emitting local
  time, sub-second precision, or a raw epoch would destabilize IDs and break dedup. Verify each
  source's native timestamp format and pin the normalizer per agent. Findings:
- [ ] **Codex:** identify the canonical prompt record — a `history.jsonl` (absent on the scout
  machine; check the persistence setting that creates it) vs parsing session rollout JSONLs
  (`{"payload","timestamp","type"}` with `session_meta`/`event_msg` entries — verified present and
  current on the scout machine) vs the `state_*.sqlite` stores. Decide one source of record and
  confirm it covers VS Code extension sessions, not just CLI sessions. Findings:
- [ ] **Agy:** per-turn data lives in **JSONL transcripts** —
  `brain/<conversation-id>/.system_generated/logs/transcript.jsonl` with
  `content`/`created_at`/`source`/`type` keys (verified 2026-08-31; the `conversations/*.db`
  SQLite files are NOT the prompt record). Confirm the `source`/`type` values that identify a
  user-submitted prompt, whether `created_at` is UTC and stable, and the per-conversation file
  lifecycle (rotation, rename-on-complete). Findings:
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
- [ ] **Viewer regression check:** load a note rendered with the third metadata token in the
  sidebar extension (`vscode-extensions/clio`) and confirm it renders (rendered + source modes).
- [ ] Real-session verify: one ZCode prompt + one Claude Code prompt land in the JSONL with
  correct `agent` values and render once each in the note.
- [ ] `pytest tests/` full suite green.

## Phase 2 — Codex (VS Code agent) capture

- [ ] Implement a small idempotent tailer (per Phase 0's chosen source of record) that emits new
  Codex prompts as JSONL lines with `agent: "codex"`, `repo`/`branch` resolved from the session's
  project directory when derivable (empty otherwise), riding the existing capture filters.
- [ ] Cursor + delivery semantics mirror the exporter's discipline: cursor is an optimization,
  IDs are the dedup guarantee — the tailer **scans the existing JSONL ID set before every append**
  (see invariant 3), so a crash between append and cursor-advance can never double-write.
- [ ] Ship the launchd job (macOS) + install/uninstall lines in `utils/CLIO/INSTALL.md`; the job
  label follows the existing family naming, operator-facing copy uses the functional name.
- [ ] Backfill boundary decided explicitly: on first run the tailer starts **now** (no history
  import) unless the operator opts in — document whichever is chosen.

**QA gate (Phase 2):**

- [ ] Tailer tests (mock rollout/history fixtures under `test/fixtures/`): happy path, malformed
  line, mid-session resume, restart-no-duplicates, capture-filter interaction.
- [ ] **Restart-no-duplicates runs the tailer twice with NO exporter run in between** — the JSONL
  must contain zero duplicate IDs (guards the within-batch rendering gap).
- [ ] Real-session verify: a VS Code Codex prompt lands with `agent: "codex"` and renders once.
- [ ] `pytest tests/` + both CLIO test scripts green.

## Phase 3 — Agy (standalone app) capture

- [ ] Same tailer pattern over Agy's **JSONL transcripts**
  (`brain/<conversation-id>/.system_generated/logs/transcript.jsonl`, per Phase 0's `source`/`type`
  findings), strictly read-only; treat any companion SQLite stores as indexes, never as the prompt
  record. Dedup rides the ID machinery **plus the JSONL-scan-before-append rule** (invariant 3).
- [ ] Emit `agent: "agy"` lines with the same invariants.
- [ ] Install/uninstall documented in `utils/CLIO/INSTALL.md`; launchd job follows Phase 2's shape.

**QA gate (Phase 3):**

- [ ] Tailer tests with fixture transcript copies: new-turn detection, restart-no-duplicates
  (twice, no exporter in between), live-write safety (writer not blocked), capture filters.
- [ ] Real-session verify: an Agy prompt lands with `agent: "agy"` and renders once.
- [ ] Full suite green; exporter `--status` reports all four agents' IDs as delivered.

## Design invariants

1. **One JSONL, one note.** Every agent funnels into the same source file and the same rendered
   note; per-agent data never forks the pipeline (filters/transforms in sequence, per GUIDING).
2. **IDs are immutable.** `clio:id = session_id:timestamp` for every agent; the additive `agent`
   field never enters the ID. Collision across agents is theoretically possible and practically
   negligible (uuid session ids + second-precision UTC); covered by a test note, not a format change.
3. **Tailers dedup against the JSONL, not just the note.** The exporter renders each JSONL line
   independently and has **no within-batch ID dedup** (`prompt-log-to-md.sh` render step, ~lines
   496–503), so two same-ID lines that land in the JSONL between exporter runs both render. A tailer
   that crashes after appending but before advancing its cursor would re-append on restart — so every
   tailer must scan the existing JSONL ID set (its own agent's ids suffice) before appending, in
   addition to its cursor. The cursor is an optimization; the ID set is the guarantee.
4. **Capture stays best-effort and fast.** The hook never blocks prompt submission (exit 0, errors
   to the error log); tailers degrade to catch-up on next tick.
5. **The viewer extension must survive.** `vscode-extensions/clio` already tolerates `clio:id`
   comments and atomic saves; the only format delta it sees is the extra `· agent` token and
   (new notes only) the header wording.
6. **PII discipline.** Device names, usernames, and vault paths stay in per-device config/launchd
   plists — never in repo docs, issues, or fixtures (fixtures use synthetic values).

## Risks

- **ZCode hook payload drift** — if ZCode's stdin JSON differs from Claude Code's, the shared
  writer needs a small per-agent normalizer; Phase 0 pins this before any code. Most likely to
  bite first (internal tools evolve fast), and the spike-first mitigation covers it.
- **Codex VS Code sessions may not write the same files as CLI sessions** — Phase 0 must verify
  the IDE path specifically among the three candidates (history file, rollout JSONLs — verified
  present, `state_*.sqlite`); if the IDE writes nothing observable, fall back to the rollout
  session files and record that in the spike findings.
- **Agy storage layout is undocumented and can move between app updates** — the prompt record is
  the JSONL transcripts (initial scouting mistook the `conversations/*.db` SQLite files for it;
  corrected during the agy r1 review), and the tailer must fail soft (log + skip) on schema drift
  rather than crash-loop; consider a schema probe at startup.
- **Exporter legacy matching** — the `·`-token metadata line is load-bearing for
  `legacy-unlabelled` backfill matching; the agent token must append, never reorder. The agy r1
  review re-verified `split(" · ")[0]` machine isolation in `reconcile_status` and `backfill_plan`
  and found it safe for the added token.
- **Within-batch duplicate rendering** — duplicate same-ID JSONL lines land between exporter runs
  render twice (no within-batch dedup in the exporter); mitigated by invariant 3
  (tailers scan the JSONL ID set before append) and the restart-no-duplicates gates.

## Review

- **agy relay r1 — 2026-08-31 — Changes requested.** 1 Blocker, 2 Shoulds, 1 Nit; all applied:
  - [Blocker] Capture-strategy facts corrected (Agy = JSONL transcripts, not SQLite; Codex store
    candidates widened) and tailer dedup redesignated to the JSONL ID set with a restart gate.
  - [Should] Timestamp normalization (UTC, second-precision) added as an explicit Phase 0 spike
    item, since `clio:id` embeds the timestamp verbatim.
  - [Should] Viewer-regression step added to the Phase 1 gate; Phase 2 restart gate now runs the
    tailer twice with no exporter in between.
  - [Nit] Agy schema-drift risk rewritten to name the actual storage; ZCode drift called as
    first-to-bite.
  - Schema v2 / ID stability and scope/ordering passed unamended (`[Pass]` on Q2 and Q4).
- **agy r2 confirmation — 2026-08-31 — Approved.** All five confirmations returned
  `[Confirmed]` (Blocker application, timestamp spike item, viewer gate, risk wording, and the
  no-regression check on what passed r1). The plan is cleared for Phase 0.
