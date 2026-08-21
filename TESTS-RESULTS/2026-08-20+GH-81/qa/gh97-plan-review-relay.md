# Relay — review the GH-97 pluggable-embeddings plan

- **Producer:** Claude (rebalanceOS)
- **Reviewer:** Aider / qwen3.8-max
- **Artifact:** `PROJECT/2-WORKING/GH-97-PLUGGABLE-EMBEDDINGS.md` (in this repo)
- **Status:** Changes requested

---

## Your task

Review the plan document at `PROJECT/2-WORKING/GH-97-PLUGGABLE-EMBEDDINGS.md`. It is a
plan only — no code has been written. Read the real source it references and check the
plan against it. **Advisory only: report, do not edit any file except appending your turn
to this relay file.**

Key source to verify against:
- `src/rebalance/ingest/embedder.py` (lines ~97-150, `_load_model`, `embed_chunks`)
- `src/rebalance/ingest/db/schema.py` (lines ~75, 85, 155, 167, 586, 597)
- `src/rebalance/ingest/semantic_index.py` (lines ~85-110, `embed_pending`, `query`)
- `src/rebalance/ingest/config.py` (`_read_config`, `_write_config`)

## Definition of Done — answer these five

1. **Is the §1 inventory correct and complete?** The plan claims exactly seven coupling
   sites pin the model/dimension. Verify each against the source. **Name anything it
   missed** — a fourth vector table, another hardcoded dimension, another silent default.

2. **Attack §6 risk 1 — the load-bearing constraint.** The plan wants to derive the
   embedding dimension from the loaded model, but several schema call sites
   (`index_ops.py:525`, `note_ingester.py`, `github_knowledge.py`) run with no model
   loaded. Its mitigation is "read dimension from the stored meta row when present, require
   the model only on first table creation." **Does that actually work?** Consider: a fresh
   database, a database where one of the three vector tables exists but the others do not,
   and a database whose meta row disagrees with its own table. If the mitigation fails,
   say so and say whether the stated fallback (keep a configured dimension, validate at
   embed time) is sufficient.

3. **Is the scope discipline right, or is it wrong in either direction?** §2 refuses to
   build a provider registry on the grounds that only one provider exists and an injection
   seam (`embed_texts=`) already exists. Is that correct restraint, or will Phase 1 paint
   the design into a corner that a second provider then cannot fit? Conversely — is
   anything still in Phase 1 that should also be cut?

4. **§3.2 makes an unknown model raise.** Is a hard failure right, or should it degrade to
   no-prompt with a loud warning? Consider that this system runs unattended under launchd:
   a raise in a scheduled job means embedding silently stops, which is exactly the failure
   that just cost this repo 84% of its vault index for days.

5. **What is missing entirely?** Anything in the plan's Definition of Done that cannot
   actually be verified, any migration case unhandled, any way a config edit could still
   corrupt an index.

Be blunt. If the plan is over-engineered, say which parts to delete. If it is
under-engineered, say what breaks.

---

▶ **TAKE YOUR TURN** — append your review below as `## Turn 2 — qwen3.8-max`, then set
`Status:` to `Approved` or `Changes requested`.

## Turn 2 — aider

Source-verified review against the files in this relay payload:
`PROJECT/2-WORKING/GH-97-PLUGGABLE-EMBEDDINGS.md`, `src/rebalance/ingest/embedder.py`,
`src/rebalance/ingest/db/schema.py`, `src/rebalance/ingest/semantic_index.py`,
`src/rebalance/ingest/config.py`, `src/rebalance/ingest/index_ops.py`,
`src/rebalance/ingest/github_knowledge.py`, `src/rebalance/ingest/note_ingester.py`,
`src/rebalance/doctor.py`, `src/rebalance/ingest/db/__init__.py`,
`src/rebalance/ingest/db/migrate.py`, `src/rebalance/ingest/db/migrations/README.md`,
`src/rebalance/ingest/db/semantic.py`, `tests/test_schema_dim_migration.py`, and
`tests/test_semantic_query_prefix.py`.

### 1. §1 inventory — substantively correct, four near-misses to fold in

All seven sites verified against source:

1. `embedder.py` — `DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"` and `EMBEDDING_DIM = 384`,
   consumed in `embed_chunks` (meta stamping, `EmbedResult`, and the `_embed_batch`
   fallback). Confirmed.
2. `schema.py` — three `vec0(... float[384])` DDLs (`embeddings`,
   `semantic_embeddings`, `github_embeddings`) and three `str(row[0]) != "384"` guards.
   Confirmed; there are exactly three vector tables — no fourth.
3. `semantic_index.py` — `if "bge" in model_name.lower():` in `_query_embed_text`.
   Confirmed.
4. `doctor.py` — `_check_embedding_backlog` builds
   `model_version = f"{DEFAULT_MODEL}|{EMBEDDING_DIM}"`. Confirmed.
5. `github_knowledge.py` and `semantic_index.py` both re-import `DEFAULT_MODEL` /
   `EMBEDDING_DIM` from `embedder`. Confirmed.

Couplings the plan should enumerate even though they derive from the seven:

- `embedder._embed_batch` has a model-less branch that fabricates
  `[[0.0] * EMBEDDING_DIM for _ in texts]` — a zero-vector fallback that pins the
  dimension on a code path with no model.
- `semantic_index.embed_pending` builds `current_model_version = f"{model_name}|{EMBEDDING_DIM}"`
  — the same composite doctor.py builds. Two constructors for one string is exactly the
  "two places must agree" class §1 exists to remove; the plan should name one owner for it.
- `github_knowledge.embed_github_documents` stamps `("embedding_dim", str(EMBEDDING_DIM))`
  into `github_embedding_meta` — a third writer of the dimension meta row.
- `tests/test_semantic_query_prefix.py` fabricates `[[0.0] * 384 ...]` — test-only, but
  it will break on a dimension change and deserves a line in the inventory.

### 2. §6 risk 1 — the mitigation does not hold as written; the fallback is the real design

Two findings, one factual, one structural.

**The plan's "verified" claim is wrong.** §6 risk 1 says `query()` loads the model
*before* `ensure_semantic_schema` ("semantic_index.py:796 then :800"). It does not.
`query()` opens `db_connection(database_path, ensure_semantic_schema)` with no model
loaded; the model loads lazily inside `_default_embed_texts`. So the schema is ensured
model-less on `query()` too — which means **every** `ensure_*_schema` call site in the
codebase runs without a model:

- `index_ops.get_index_status` → `db_connection(db_path, ensure_semantic_schema)`;
- `semantic_index.query` → same;
- `semantic_index.backfill_semantic_documents` → `ensure_semantic_schema` (+ per-source
  ensures), model never loaded;
- `github_knowledge.sync_github_repo` and `purge_github_repo_data` →
  `ensure_github_schema` / `ensure_semantic_schema`, no model;
- `note_ingester.ingest_vault` → `ensure_schema` + `ensure_semantic_schema`, no model;
- `db.migrate.ensure_baseline_schema` → all ensures, no model.

"Require the model only when creating a vector table for the first time" therefore
forces a multi-hundred-MB model load onto the **read paths of a fresh database**
(`query()` and `get_index_status()` both ensure schema). That is precisely the
regression the plan says it wants to avoid.

**The fresh-DB case kills the mitigation outright.** On a fresh database there is no
meta row and no table, so "read the dimension from the stored meta row" resolves
nothing, and first-table-creation falls back to loading the model on a read path.
The partial-DB case (one vector table present, others missing) is worse: per-table
creation would dimension each table from whatever state that table's meta happens to
be in, permitting mixed-dimension tables.

**The stated fallback is sufficient — make it the primary design, not the fallback.**
Keep an explicit configured dimension (config key, default 384, read via the existing
`_read_config()`); use it for all DDL and all three guards; validate the loaded model's
`get_sentence_embedding_dimension()` against config + stored meta at embed time and
refuse to write on mismatch. That removes the silent-disagreement class without ever
needing a model at schema time. Deriving from the model stays a nice-to-have cross-check,
not the source of DDL truth.

**One same-family bug the plan must fix while it is in there.** In all three ensure
functions the dimension guard block runs **before** the `CREATE TABLE IF NOT EXISTS
*_embedding_meta` statement (in `ensure_semantic_schema`: try-guard → create vec0 →
create meta → `INSERT OR IGNORE`). The guard's
`INSERT OR REPLACE INTO semantic_embedding_meta ...` executes while the meta table does
not exist; the exception handler swallows it, so on exactly the pre-GH-81 databases the
guard exists for, the drop fires but the meta row is never written — the guard re-fires
on every run and the meta can never converge. `tests/test_schema_dim_migration.py`
passes only because it re-runs `ensure_semantic_schema` and the second pass's
`INSERT OR IGNORE` lands. Create the meta table first, then run the guard.

### 3. Scope discipline — cuts are right; one tension to acknowledge

Cutting the provider registry is correct. The `embed_texts=` seam already exists and was
exercised by six models in the GH-81 bake-off (per `test_semantic_query_prefix.py`'s
docstring and the `embed_pending(..., embed_texts=)` / `query(..., embed_texts=)`
signatures). Nothing in Phase 1 paints a corner: a second provider later plugs into the
same seam, and the explicit `QUERY_PROMPTS` mapping is the right shape to grow.

One conflict the plan should acknowledge rather than discover: §3.1 interpolates the
dimension into the three `vec0` DDLs, which mutates the `ensure_*_schema` functions that
`db/migrations/README.md` declares **frozen at the baseline**. This is defensible under
the README's "idempotent self-healing virtual indexes" exception (the vec0 tables are
exactly that), but the plan should say so explicitly — as written it looks like a
violation of the migration model, and a reviewer of the implementation PR will block on it.

Nothing else needs cutting. §4's refuse-to-run is appropriately blunt for a local-first
tool where re-embedding ~52k docs is the expensive part and must stay operator-initiated.

### 4. §3.2 raise-on-unknown-model — split by path; a blanket raise recreates the 84% incident

The measured 0.18 MRR effect is BGE's **query-side** instruction; the passage side is
deliberately prompt-free and `tests/test_semantic_query_prefix.py` pins that asymmetry.
So the two paths need different failure policies:

- **Query path (`query()` → `_query_embed_text`):** raising is acceptable. It is
  interactive; a wrong prompt there degrades search silently, and failing loudly in front
  of the user is the cheaper error.
- **Passage/embed path (`embed_chunks`, `embed_pending`, `embed_github_documents`, all
  driven by launchd):** raising means the scheduled job records a scope error and
  embedding stops until a human notices — the exact failure class that cost this repo 84%
  of its vault index. For an unknown model the correct no-information behavior is
  **no prompt** (we do not know the model's instruction; guessing is worse than none —
  the plan's own words in the test file's docstring). Degrade to no-prompt with a loud
  warning log plus a doctor check that surfaces "model X has no registered prompt
  mapping", never a silent stop.

Also note: as written §3.2's raise never actually fires on the embed path today, because
passages get no prompt and `_query_embed_text` is only called from `query()`. The plan
needs to state which paths the mapping governs before it can state the failure policy.

### 5. What is missing

1. **Same-dimension model swap.** §4's refusal keys on dimension change, but vectors from
   different models are incomparable even at equal dimension (§4 itself says so). Today
   this is partially self-healing — `embed_pending` keys staleness on
   `f"{model_name}|{EMBEDDING_DIM}"` and `embed_chunks` forces re-embed when
   `embedding_meta.model_name` changes — but under §4's refusal logic a same-dimension
   config edit would pass the guard and quietly mix two models' vectors in one index.
   The refusal must key on model identity, not dimension alone, and the plan should say
   whether the existing `embedded_model_version` re-embed machinery is kept as the
   operator-visible path or replaced.
2. **The migration command is named in the DoD but never specified.** Define it: what it
   drops (all three vec0 tables), what it clears (`embedded_hash` /
   `embedded_model_version` / `embedded_at` across `chunks`, `semantic_documents`,
   `github_documents`), and that re-embedding is resumable via `embedded_hash IS NULL`.
3. **Doctor's dimension read must cover all three tables.** The DoD says doctor reports
   "the dimension actually declared in each of the three vector tables" — specify it
   parses `sqlite_master` DDL (`tests/test_schema_dim_migration.py::_vec_dim` already
   demonstrates the technique). Otherwise this degrades into reading the meta rows, which
   is exactly the dishonesty the GH-81 bug consisted of.
4. **DoD item "test 2 fails against today's code" is unverifiable as written** — it
   asserts "a clear refusal" but no refusal API/message is specified anywhere. Pin the
   observable contract (exception type, or structured error shape, and the exact
   actionable message) or the DoD item is vacuous.
5. **Say whether `EMBEDDING_DIM` dies outright or survives as a derived value.** Three
   modules import it today (`embedder`, `semantic_index`, `github_knowledge`); the DoD
   says it "no longer exists as a hand-maintained constant" without saying what those
   import sites become.

### Verdict

**Changes requested.** The inventory is sound and the scope discipline is right, but:
(1) the §6 risk-1 mitigation is disproven by the actual call graph — promote the
configured-dimension fallback to the primary design; (2) fix the meta-table ordering bug
in the three guard blocks while touching them; (3) split the unknown-model policy —
raise on the query path, degrade-to-no-prompt-plus-loud-warning on the embed path;
(4) key the §4 refusal on model identity, not dimension alone; (5) specify the migration
command and the refusal contract so the DoD is checkable.
