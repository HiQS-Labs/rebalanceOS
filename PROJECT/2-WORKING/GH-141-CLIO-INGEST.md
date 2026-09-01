# GH-141: Ingest CLIO prompt logs into RebalanceOS semantic index

> QA adjudication 2026-08-31 (commandcode) — original stub was 3 lines; expanded here to satisfy AGENTS.md collector/semantic/one-writer contracts and to fix the global Issue/PR heuristic. Read `index_ops.py:COLLECTORS` and ARCHITECTURE.md before implementing.

## Goal
Project CLIO prompts from `~/.claude/prompt-log.jsonl` (and, after GH-139, the same JSONL fed by ZCode/Codex/Agy via the shared writer) into the unified semantic index so `semantic_query` / `ask` recall reflects what the operator actually asked agents to do. No new query surface.

## Non-goals
- No capture change — GH-139 owns `utils/CLIO/` capture, tailers, and `clio:id` stability. This issue reads the JSONL only.
- No Issue↔PR close-candidate inference (`github_reconciliation.py`); prompt→issue association is metadata only.
- No prompt-response pairing.

## Architecture — must satisfy AGENTS.md collector contracts

### 1. One Collector, registered in `index_ops.py` (the spine)

Follow Figma (`src/rebalance/ingest/figma.py:284` + `index_ops.py:2122`) as the worked SourceModule example:

```python
# src/rebalance/ingest/clio.py
def sync_clio_prompts(database_path: Path) -> ClioSyncResult: ...
def clio_semantic_docs(conn) -> Iterator[SemanticDoc]: ...

# src/rebalance/ingest/index_ops.py  (bottom, with figma/claude_cloud)
from rebalance.ingest.clio import clio_semantic_docs
register_collector(Collector(
    "clio",
    _clio_adapter,
    semantic_docs=clio_semantic_docs,
    # raw_source, included_in_all=True by default — no PAT, no file-key allow-list,
    # so it belongs in `all` (AGENTS.md scope taxonomy). If privacy review disagrees,
    # flip to included_in_all=False (opt-in) — one-line change, no dispatch edit.
))
```

- **Kind:** `raw_source` (default). It is incoming data, not a derived scan/projection/export. Only `raw_source` collectors are `all`-eligible (`index_ops.py:135`); derived/projection/export must never be peers in the registry.
- **Adapter:** `_clio_adapter = _dry_run_adapter(_refresh_clio)` (or bespoke if `since_days` is needed) — same 3-line shim as every other source (`index_ops.py:1825`).
- **`_refresh_clio`:** `sync_clio_prompts()` → return `{scope:"clio", ...}` envelope. No semantic work here; semantic stage owns that (below).
- **`get_index_status`:** add a `clio` block (counts, `last_synced_at`, `recent_row_count_7d`) and wire `_SIGNAL_HEALTH_RULES["clio"]` so the source is born observable — same pattern as `email`/`github` content-quality checks. Without this, drift/grade has no signal.
- **Shared resolvers:** resolve the JSONL path via `Path.home() / ".claude/prompt-log.jsonl"` through `src/rebalance/paths.py` helpers (not a bare `Path.home()` inline where a resolver exists), and `resolve_database_path()` for DB. No `parents[N]` walks.

### 2. One writer per table (ARCHITECTURE.md "Write discipline")

| Table | Writer | Notes |
|---|---|---|
| `clio_prompts` (new) | `src/rebalance/ingest/clio.py` only | `CREATE TABLE` lives in `ensure_clio_schema(conn)` in that module; promoted to `ingest/db/` only if a second module needs it. Key by `clio:id` (`session_id:timestamp`, UTC second-precision — GH-139 invariant 2) or a hash of `(session_id, timestamp, prompt)` if `session_id` can be empty. Upsert, never delete — JSONL is append-only. |
| `semantic_documents` / `semantic_embeddings` | `semantic` stage only (`index_ops.py:_refresh_semantic_only` → `semantic_index.py:backfill_semantic_documents(..., use_registry_providers=True)`) | `clio.py` never touches these tables. The projection is the registry-driven `semantic_docs` provider above, mapped in `semantic_index.py:_REGISTRY_SOURCE_TABLES = {"figma":"figma_comments", "clio":"clio_prompts"}`. Adding the entry is the only edit to `semantic_index.py` besides the provider. |
| `clio_prompts` → `semantic_documents` | `clio_semantic_docs(conn)` yields `SemanticDoc(source_pk=clio:id, doc_kind="prompt", title=prompt[:120], body=prompt, metadata={repo,branch,machine,agent,session_id,timestamp,clio_id}, created_at=timestamp, updated_at=timestamp)` | Mirrors `figma_semantic_docs` (`figma.py:284`) — function-local imports of `SemanticDoc`/`sem` so top-level stays `db`-only, no mlx. Skip empty prompts. |

Contract tests (AGENTS.md — ship mechanically, not as prose):
- `tests/test_collector_contracts.py`: single-writer on `semantic_documents`/`semantic_embeddings`, `all`-expansion includes `clio` iff `included_in_all=True`, no user-facing surface imports `sync_clio_prompts`/`clio_semantic_docs` directly — only `refresh_index`/source-owned helper.
- `tests/test_clio.py`: insert/unchanged/update per `clio:id`, malformed JSONL line skipped + counted, empty prompt skipped, idempotent re-ingest.

### 3. Route user-facing writes through the orchestrator

- **CLI/MCP/scheduler/web:** call `refresh_index(scope=["clio"])` or `refresh_index(scope=["all"])` — never `sync_clio_prompts()` / `backfill_semantic_documents()` / `embed_pending()` directly (`AGENTS.md:127-131` "Route user-facing writes through the orchestrator"). The existing `pdda-leaf-ingest-guard.py` already enforces this; the new collector must pass it.
- **Dry-run:** `_refresh_clio(..., dry_run=True)` returns planned steps without touching DB/network, mirroring every other `_refresh_*`.

### 4. Issue/PR heuristic — scoped, not global (fixes stub's underspecification)

**Do not extract bare `#123` globally.** A prompt containing `#5` almost never means issue 5 of a tracked repo; global extraction would tag every prompt mentioning a number as related to an unrelated issue, polluting `metadata` and any future `github_links`-style join with false positives.

Rules:
- **v1 — no heuristic at all is acceptable.** The prompt body already lands in the semantic index; vector + FTS recall will surface "fix #141" without an explicit tag. Ship without extraction and add it only if recall demonstrably needs it (Phase 0 spike: measure recall@k on 20 hand-curated prompt→issue pairs before building the extractor).
- **If extraction ships, scope it:**
  - Extract only **qualified** refs: `owner/repo#123` or `repo#123` where `repo` is in `list_watched_repos()` / `project_registry` (the same watched set `index_ops.py:get_watched_repos` computes). Bare `#123` is stored only when the prompt's own `repo` field matches a watched repo, and even then as a weak `suggested_refs` metadata array, never as a hard `github_links` row.
  - Store as `metadata.suggested_refs: ["owner/repo#123"]` on the `SemanticDoc` — informational, not a foreign key. No new table, no second writer.
  - Never infer `closes`/`fixes` semantics; that is `github_reconciliation.py`'s job over actual GitHub corpus rows.
- **Centralize parsing:** reuse `src/rebalance/lib/` string/regex helpers if they exist; do not duplicate Issue/PR regex across collectors (`AGENTS.md` Pre-flight Search Rule).

### 5. Other invariants
- **Vault optional:** `refresh_index(scope=["clio"])` must succeed with no vault present (`AGENTS.md` — Obsidian/vault is optional output, not control-plane dependency).
- **No parallel pipeline:** one logical pipeline per data flow (`AGENTS.md` Pipelines) — CLIO prompts flow `JSONL → clio_prompts → semantic_docs provider → semantic_documents → semantic_embeddings` in sequence, no forking.
- **lib reuse:** datetime parsing via `src/rebalance/lib/time_ops.py`, JSON via `src/rebalance/lib/json_ops.py`, no local helpers (`AGENTS.md` Centralization Rule).

## Phases
- **Phase 0 spike (1–2h max):** confirm `~/.claude/prompt-log.jsonl` exists and is valid JSONL on this machine; sample 20 rows for `timestamp` precision (UTC seconds), `session_id` stability, prompt length distribution, and malformed-line rate. If including Issue/PR heuristic, run the recall spike above. Write findings back here before Phase 1 QA gate.
- **Phase 1 — raw source:** `clio.py` + `ensure_clio_schema` + `_refresh_clio` + `register_collector("clio", ...)` + `get_index_status` block + migration. Tests: `test_clio.py` + collector-contract gate.
- **Phase 2 — semantic projection:** `clio_semantic_docs` + `_REGISTRY_SOURCE_TABLES["clio"]` + `backfill_semantic_documents(use_registry_providers=True)` path. Verify `semantic_query` returns prompt docs and `index_status` drift (`clio_prompts` missing from `semantic_documents`) clears after a `semantic` run. Optional scoped `suggested_refs` behind the Phase 0 measurement.
- **Phase 3 — polish:** `doctor` check for JSONL readability, dashboard/pulse read path if warranted (read-only, no new writer).

## Risks
- **JSONL not present on CI/secondary devices:** collector must return `{scope:"clio", skipped:True, reason:"no prompt-log found"}` rather than error — same honesty as `figma` missing PAT (`index_ops.py:1422`).
- **Prompt PII:** prompts stay in the local SQLite + sqlite-vec only; no new outbound. Document that `sync` export does not include `clio_prompts` unless explicitly added.
- **Large/promiscuous prompts:** cap `SemanticDoc.body` at the same 4000-char truncation `semantic_index.py:embed_pending` uses (or rely on that truncation at embed time); store full text in `clio_prompts.prompt`.

## QA verdict — 2026-08-31 (commandcode)

**Original stub:** 3 lines (goal + two-sentence description). Insufficient to judge Q1–Q3 against AGENTS.md.

### Q1 — Does the plan reuse Collector infrastructure without redundant parallel pipelines?
**Conditional pass, after this edit.** The stub named `via index_ops.py` but described no `register_collector` shape, `kind`, adapter, or how `clio_prompts` reaches `semantic_documents`. As hardened above: one `raw_source` Collector, one writer per table (`clio.py` owns `clio_prompts`, `semantic` stage owns `semantic_documents` via the `semantic_docs` provider seam), single logical pipeline `JSONL → clio_prompts → provider → semantic_documents → embeddings`. No parallel pipeline, no dispatch-chain edit, no second writer. Reuse `src/rebalance/lib/*` (`time_ops`, `json_ops`), shared resolvers, and `pdda-leaf-ingest-guard` enforcement.

### Q2 — Is global Issue/PR string extraction safe?
**No — and the stub's "PR/Issue heuristic matching" is underspecified.** Bare `#123` extraction against the prompt text is unsafe: `#5` in a prompt almost never means `HiQS-Suite/rebalanceOS#5`; it would create systematic false associations, violate the "label roles at point of action" principle by attaching wrong repo context, and pollute any future join. Fix: v1 ships with no heuristic (semantic recall suffices); if extraction ships, it must be scoped to qualified refs resolved against the watched-repo set (`get_watched_repos` / `project_registry`), stored as weak `metadata.suggested_refs`, gated behind a Phase 0 recall measurement, and centralized through `lib/` helpers.

### Q3 — Are "route through orchestrator" and "one writer per table" satisfied?
**Yes, after this edit.** Before: unclear — no table mentioned, no writer designated, no dry-run or `all`-scope story. After: `refresh_index` is the sole user-facing write path (CLI/MCP/scheduler all call it; leaf `sync_*`/`backfill_*` never called directly), `clio.py` is the sole writer of `clio_prompts`, `semantic` stage is the sole writer of `semantic_documents`/`semantic_embeddings` (via provider), and contract tests enforce `all`-expansion / leaf-import guard / single-writer invariants mechanically. `get_index_status` + `_SIGNAL_HEALTH_RULES["clio"]` makes the source observable from birth.

### Required line-level citations
- `src/rebalance/ingest/index_ops.py:35-94` — `Collector` dataclass and `COLLECTORS` registry (the spine); `kind` taxonomy `raw_source`/`derived_scan`/`projection`/`export`.
- `src/rebalance/ingest/index_ops.py:135-148` — `all` expands to raw sources only; `semantic`/`code`/`sync` attach as follow-on stages. New raw sources must choose `included_in_all` explicitly.
- `src/rebalance/ingest/index_ops.py:1825-1840` — `_dry_run_adapter` / 3-line adapter pattern.
- `src/rebalance/ingest/index_ops.py:2122-2132` — Figma as the worked SourceModule example (`sync_figma_comments` + `figma_semantic_docs` + `register_collector` + `requires` + `semantic_docs`).
- `src/rebalance/ingest/semantic_index.py:511-640` — `_REGISTRY_SOURCE_TABLES` + `backfill_semantic_documents(use_registry_providers=True)` provider path + `SemanticDoc`.
- `src/rebalance/ingest/figma.py:284-321` — `figma_semantic_docs` provider shape to mirror (function-local imports, no mlx at top).
- `ARCHITECTURE.md:268-273` — Storage write discipline: one writer per table, writes through orchestrator, known exceptions.
- `AGENTS.md:127-138` — collector contracts: classify before register, one writer per table, route user-facing writes through orchestrator, shared resolvers, vault optional, `all` = raw sources only.
- `utils/pdda/pdda-leaf-ingest-guard.py:1-45` — enforcement of "no leaf ingest import from user-facing surfaces".
- `utils/CLIO/INSTALL.md` and `utils/CLIO/prompt-log-to-md.sh` — CLIO capture/export machinery GH-139 owns; this issue must not fork it.
- `src/rebalance/ingest/index_ops.py:208-278` and `ARCHITECTURE.md:116-141` — signal health / source→table fanout patterns to extend for `clio`.

**Status of plan doc:** expanded from stub to a contract-compliant design; QA adjudication above flags all three questions as pass-after-fix (no open blockers). Implementer should treat the stub's underspecified "PR/Issue heuristic matching" as the only material change in scope, per Q2.
