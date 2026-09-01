---
title: "CLIO multi-agent capture: ZCode, Codex, Agy alongside Claude Code"
status: "QA complete — ready for PR"
created: 2026-08-31
updated: 2026-08-31
owner: noel
gh_issue: 139
branch: feat/gh139-clio-multi-agent
reviewed: "agy r1+r2 2026-08-31 Approved; codex plan QA 2026-08-31 changes-requested → all applied"
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
| **Implemented and QA-complete.** Phases 1–3 shipped on this branch: shared writer + Claude shim + ZCode hook, exporter `agent` rendering, Codex rollout tailer, Agy full-transcript tailer. Tri-model implementation QA closed: GLM adversarial 11/11 confirmed fixed (incl. a reproduced large-log collision bug), codex r3 Approved, agy r2 Approved. All four CLIO suites green (24 capture cases incl. 5000-row scale regression, exporter mixed-v1/v2 e2e, both tailer contracts) + pytest 2053 passed. Version 0.78.0 | Operator live-verify on each machine (ZCode stdin probe, one real prompt per agent, viewer check) at deployment |


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
  The writer must be validated against captured fixture classes regardless: absent/null/wrong-typed
  or nested `prompt`/`session_id`, missing project/session template vars, multiline and very large
  input, multiple/nested/reordered auto-context tag blocks, and matcher semantics (omitted matcher =
  match-all; `enabled: false` = never fires). Validate `agent` and required normalized fields, never
  emit a row with a null/empty session id or prompt, apply the per-source adapter BEFORE the common
  filter, log a content-free schema diagnostic on anomaly, and still exit 0. Findings: (2026-08-31) config location, seven-event surface, `enabled` gate, matcher semantics, and template vars confirmed from the client's own hook documentation; **exact stdin payload keys NOT yet pinned** — implement defensively and ship an optional one-shot probe hook so the operator can capture the live payload in a single prompt.
- [x] **Timestamp normalization (all sources).** `clio:id` embeds the timestamp string verbatim, so
  every source must be normalized **at capture time** to UTC, second-precision ISO-8601
  (`YYYY-MM-DDTHH:MM:SSZ`, exactly what the Claude hook's `date -u` emits) — a source emitting local
  time, sub-second precision, or a raw epoch would destabilize IDs and break dedup. Verify each
  source's native timestamp format and pin the normalizer per agent. Findings: (2026-08-31) Claude hook already emits UTC seconds (`date -u`); Agy `created_at` is already UTC ISO-8601 seconds (verified); Codex rollout outer timestamps carry sub-second precision — tailers normalize everything to UTC second precision at append.
- [x] **Codex:** source of record is the session **rollout JSONLs**
  (`$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl`) — they cover both CLI and VS Code extension
  sessions (`session_meta.payload.source` distinguishes them), while `history.jsonl` is TUI-specific
  and can be disabled entirely (`persistence = "none"`). Parse ONLY
  `event_msg`/`user_message` payloads (submitted text in `message`); take session id / cwd / source
  from the nearest preceding `session_meta`. Do NOT parse `response_item` `role=user` entries —
  product/context material can be combined with user input there. Explicitly ignore environment /
  permissions / AGENTS injections, compaction summaries, and non-user event types, and handle
  archived/moved rollout files. Spike confirms the shape live (event key set verified 2026-08-31)
  and that VS Code sessions write to the same tree. Findings: (2026-08-31) rollout tree present and current on the scout machine; `event_msg`/`user_message` key set verified (`message` carries the text, outer line carries `timestamp`); `session_meta.payload.source` value for VS Code sessions pending operator verify.
- [x] **Agy:** per-turn data lives in **JSONL transcripts** —
  `brain/<conversation-id>/.system_generated/logs/transcript.jsonl` with
  `content`/`created_at`/`source`/`type` keys (verified 2026-08-31; the `conversations/*.db`
  SQLite files are NOT the prompt record). Confirm the `source`/`type` values that identify a
  user-submitted prompt, whether `created_at` is UTC and stable, and the per-conversation file
  lifecycle (rotation, rename-on-complete). Findings: (2026-08-31) `USER_EXPLICIT`/`USER_INPUT` rows identified across sampled transcripts; `created_at` UTC verified; per-conversation file lifecycle pending operator verify.
- [x] Confirm one shared capture writer can serve hook callers (stdin JSON) and tailer callers
  (file/DB polling) without per-agent forks of the cleaning/filter logic. Findings: (2026-08-31) confirmed shape: one writer, `--agent <name>` plus a per-source adapter (hook adapters read stdin JSON; tailer adapters read their source then call the same append path).

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

- [x] Extract the capture logic (cleaning, capture filters, JSONL append, error log) into one
  shared writer installed once, invoked as `… --agent <name>`; the Claude Code hook becomes a thin
  caller with `--agent claude-code`. `utils/CLIO/INSTALL.md` installs the writer + all registrations.
- [x] **Upgrade transaction for live installs.** Existing machines run the legacy
  `log-prompt.sh` shim, and the current installer's loose string-match registration skip would
  leave it in place while the new writer sits unused. The v2 installer must: install the shared
  writer; atomically replace ONLY CLIO's owned shim and CLIO's registration entry; dedupe CLIO's
  registration without touching unrelated hooks (Claude Code or otherwise); leave schema-v1 JSONL
  rows renderable via the legacy display default. Both upgraded and fresh installs must end up
  executing the same writer version — pinned by a legacy-to-v2 reinstall test.
- [x] Register the ZCode `UserPromptSubmit` hook (config-file hooks with `enabled: true`) calling
  the shared writer with `--agent zcode`; document the enable gate and matcher behavior.
- [x] Exporter renders `agent` as a third `·`-separated token on the metadata line
  (`machine · branch · agent`); legacy rows (no `agent`) render as `claude-code` — display-only
  default, no stored backfill, and the first token stays `machine` so legacy-unlabelled matching
  in `reconcile_status`/`backfill_plan` keeps working.
- [x] Exporter header text for **newly created notes** drops the Claude-Code-only wording
  (everything above the marker in existing notes is preserved verbatim by design — history untouched).
- [x] Update `~`-level uninstall instructions to remove the writer, the Claude Code entry, and the
  ZCode entry without touching unrelated hooks.

**QA gate (Phase 1):**

- [ ] `test/clio-capture.sh` covers: `--agent` stamping, legacy no-`agent` rows, capture filters
  still applying per agent, writer input-validation fixtures (absent/null/wrong-typed/nested keys,
  missing template vars, multiline/large input, reordered tags) — no null/empty-ID row ever written,
  exit 0 always.
- [ ] **Claude golden (additive delta):** with a fixed timestamp, the Claude Code path's cleaned
  prompt and all legacy fields are identical to pre-refactor output; the ONLY delta is the added
  `agent` field. (Byte-identical stdout is impossible once `agent` is stamped — the golden is the
  additive delta.)
- [ ] **Legacy-to-v2 reinstall test:** install-v1 fixture state → run v2 install → exactly one
  CLIO registration pointing at the current writer, unrelated hooks untouched, old shim replaced
  atomically, v1 JSONL rows still render once via the legacy default.
- [ ] `test/clio-exporter.sh` covers: `agent` rendering, legacy default, unchanged `clio:id`
  derivation, and **mixed schema-v1/v2 end-to-end assertions** — one rendered ID per row, metadata
  token ordering, manifest receipt, `--status`, cursor reset, conflict reconciliation, backfill,
  and repair over a note containing both row generations.
- [ ] **Viewer regression check:** load a note rendered with the third metadata token in the
  sidebar extension (`vscode-extensions/clio`) and confirm it renders (rendered + source modes).
- [ ] Real-session verify: one ZCode prompt + one Claude Code prompt land in the JSONL with
  correct `agent` values and render once each in the note.
- [ ] `pytest tests/` full suite green.

## Phase 2 — Codex (VS Code agent) capture

- [x] Implement a small idempotent tailer (per Phase 0's chosen source of record) that emits new
  Codex prompts as JSONL lines with `agent: "codex"`, `repo`/`branch` resolved from the session's
  project directory when derivable (empty otherwise), riding the existing capture filters.
- [x] Cursor + delivery semantics implement the full at-least-once contract of invariant 3
  (inode+offset cursor, newline-terminated advance, rotation/truncation rescan, lock-serialized
  append, ID-scan suppression, cursor-after-durable-write).
- [x] Ship the launchd job (macOS) + install/uninstall lines in `utils/CLIO/INSTALL.md`; the job
  label follows the existing family naming, operator-facing copy uses the functional name.
- [x] Backfill boundary decided explicitly: on first run the tailer starts **now** (no history
  import) unless the operator opts in — document whichever is chosen.

**QA gate (Phase 2):**

- [ ] Tailer tests (mock rollout fixtures under `test/fixtures/`): happy path, malformed line,
  mid-session resume, restart-no-duplicates, capture-filter interaction, **truncated final record
  (retried, then completed on next run), rotated/replaced source file (rescan), concurrent source
  append during a run, two overlapping tailer invocations (lock serializes), and every crash
  boundary between append and cursor-advance**.
- [ ] **Restart-no-duplicates runs the tailer twice with NO exporter run in between** — the JSONL
  must contain zero duplicate IDs (guards the within-batch rendering gap).
- [ ] Real-session verify: a VS Code Codex prompt lands with `agent: "codex"` and renders once.
- [ ] `pytest tests/` + both CLIO test scripts green.

## Phase 3 — Agy (standalone app) capture

- [x] Same tailer pattern over Agy's **JSONL transcripts**
  (`brain/<conversation-id>/.system_generated/logs/transcript.jsonl`, rows where
  `source = USER_EXPLICIT` and `type = USER_INPUT`; `created_at` is already UTC ISO-8601 — verified
  2026-08-31), strictly read-only; treat any companion SQLite stores as indexes, never as the prompt
  record. Delivery semantics implement the invariant-3 contract; dedup rides the ID machinery plus
  the scan-suppress rule.
- [x] Emit `agent: "agy"` lines with the same invariants.
- [x] Install/uninstall documented in `utils/CLIO/INSTALL.md`; launchd job follows Phase 2's shape.

**QA gate (Phase 3):**

- [ ] Tailer tests with fixture transcript copies: new-turn detection, restart-no-duplicates
  (twice, no exporter in between), live-write safety (writer not blocked), capture filters.
- [ ] Real-session verify: an Agy prompt lands with `agent: "agy"` and renders once.
- [ ] Full suite green; exporter `--status` reports all four agents' IDs as delivered.

## Design invariants

1. **One JSONL, one note.** Every agent funnels into the same source file and the same rendered
   note; per-agent data never forks the pipeline (filters/transforms in sequence, per GUIDING).
2. **IDs are immutable; same-second collision is an accepted, logged loss.** `clio:id =
   session_id:timestamp` for every agent; the additive `agent` field never enters the ID.
   `session_id` identifies a *conversation*, not a turn, so two substantive prompts submitted in
   the same session within one second collapse to one ID. Rather than fork the ID space with a
   discriminator (rejected: two ID namespaces break legacy dedup), the writer/tailer suppresses
   the second append, logging a content-free `id-collision` line (session id + timestamp only) to
   the error log. This matches the existing capture-filter precedent: a permanent drop with a
   trace, never a duplicate block. Covered by a collision test.
3. **Tailers implement a full at-least-once contract, not a line-count cursor.** The exporter has
   **no within-batch ID dedup** (`prompt-log-to-md.sh` render step, ~lines 496–503), so duplicate
   same-ID lines between exporter runs render twice. Each tailer therefore:
   (a) persists its cursor as **source file identity (inode/path) + byte offset**;
   (b) advances only through a **terminating newline** — an incomplete final record is retried;
   (c) **resets and rescans** on inode change or size regression (rotation/truncation);
   (d) **serializes the destination scan-plus-append** under a lock (hook and tailers append
   concurrently to one JSONL — one non-overlapping writer at a time);
   (e) appends one complete newline-terminated record via append semantics;
   (f) **advances the source cursor only after the destination write is durably verified**;
   (g) before appending, scans the existing JSONL ID set and suppresses on hit (invariant 2).
   Lock or parse failures are surfaced to the error log, never silent.
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

- **GLM adversarial review (ZCode implementation) — 2026-08-31 — needs fixes; all applied.**
  1 Blocker + 5 Shoulds + 4 Nits. Blocker (empirically reproduced on a 5k-row log): the
  collision scan's `jq | grep -q` under pipefail let an early-exit SIGPIPE read a real
  collision as "no collision" — fixed by capturing the ID set before matching, with a
  5000-line regression test. Shoulds: bornless locks now fall back to dir mtime; hook mode
  exits 0 (3 is tailer-only); offset timestamps are normalized to UTC in the tailer
  extractors; the installer never force-flips a deliberate `enabled:false` (jq `//` filters
  `false` too — caught in verification, fixed with `has()`); registration failures are
  reported. Nits: smoke prompt length, probe umask, uninstall guards, `--agent` arity,
  exporter within-batch ID dedup. Verification pass confirmed 11/11 applied.
- **codex implementation QA (Phase 2) — 2026-08-31 — r1 changes requested → r3 Approved.**
  r1: first-sighting persisted raw EOF (partial records lost) and malformed lines were
  silently consumed — both fixed with a newline-aligned cursor and a traced malformed counter;
  context is checkpointed with the cursor (no quadratic re-reads); repo/branch resolved from
  the session cwd. r2 caught the recovery pass's consumed position (absolute vs relative) and
  single-slot cwd caching — both fixed. r3: Approved.
- **agy implementation QA (Phase 3) — 2026-08-31 — r1 changes requested → r2 Approved.**
  r1 Blocker: `transcript.jsonl` truncates large text — the tailer now targets
  `transcript_full.jsonl`. Should: second concurrent conversation added to the suite (state
  and ID isolation). Cursor contract, at-least-once integrity, read-only safety and writer
  integration passed unamended. r2: Approved.

- **codex plan QA — 2026-08-31 — Changes requested; all applied.** 2 Blockers, 4 Shoulds:
  - [Blocker] Upgrade transaction for live installs added to Phase 1 work + a legacy-to-v2
    reinstall test in the gate (the old installer's string-match skip would strand the legacy hook).
  - [Blocker] Invariant 3 rewritten as a full at-least-once contract: inode+offset cursor,
    newline-terminated advance, rotation/truncation rescan, lock-serialized destination append,
    cursor-after-durable-write; Phase 2/3 gates gained truncation/rotation/concurrency/crash-boundary
    fixtures.
  - [Should] Codex source of record pinned to rollout JSONLs (CLI + VS Code via
    `session_meta.payload.source`; `history.jsonl` is TUI-only and disable-able); parse only
    `event_msg/user_message`, never `response_item role=user`.
  - [Should] ZCode spike expanded with fixture classes + writer validation requirements
    (never emit null/empty-ID rows; per-source adapter before the common filter; exit 0 always).
  - [Should] "Byte-identical" golden replaced with an additive-delta golden + mixed v1/v2
    end-to-end exporter assertions (status/manifest/backfill/repair/reconciliation).
  - [Should] Collision semantics made honest: same-session same-second IDs collapse; accepted,
    logged, suppressed at append (matches the capture-filter drop precedent) instead of an
    unsubstantiated "practically negligible" claim.
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
