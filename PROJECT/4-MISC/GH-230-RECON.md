# GH-230 Recon Map — CLIO journey replay

Source base: `57b6ea9bc37841440b8207d125d7812f770c36db`, RebalanceOS development.
Read-only source recon, 2026-09-16 UTC. Graph and Rebalance MCP tools unavailable in this session;
used source reads/search and two read-only recon lanes. Runtime coverage remains unverified.

## Trace and authority

| Seam | Observed contract | Consequence |
|---|---|---|
| `utils/CLIO/INSTALL.md:38` shared writer | IDE adapters append JSONL with timestamp/session/agent/repo/branch/machine | Preserve writer and raw history; no migration |
| `utils/CLIO/INSTALL.md:102` filtering | Short prompts, automation and same-session same-second duplicates can be dropped | Do not claim every prompt is captured |
| `src/rebalance/paths.py:101` | CLIO path resolver | No embedded device paths |
| `src/rebalance/ingest/index_ops.py:2276` | CLIO registered in existing collector registry | No second collector |
| `src/rebalance/ingest/clio.py:22` | SQLite projection already exists; omits branch/machine | Raw JSONL needed for available device metadata; no schema change in spike |
| `clio.py:44`, `:134` | Removes relay metadata; DB IDs include cleaned-text hash | Never infer relay success from prompt; never replace DB IDs |
| `clio.py:62` | Bounded reader omits session and swallows errors as empty | Do not interpret empty fallback as no activity |
| `src/rebalance/ingest/db/connection.py:92` | True read-only DB connection | No normal connection/schema initialization for replay |
| `utils/daily_work_synthesis.py:87`, `:116` | Bounded JSONL tail then SQLite; intent is unattested | Reuse source resolver, cleaning, evidence distinction; tail alone insufficient for seven days |
| `utils/daily_work_synthesis.py:416` | Guarded Terra runner owns budget/receipts and publication | Do not call unguarded invoke helper directly or reset budgets in a scratch log |
| `src/rebalance/ingest/db/schema.py:433` | Issues/PRs carry lifecycle timestamps | Facts are artifact creation/close/merge, not deployment |
| `schema.py:376` | Branch snapshot has fetched time, not creation time | Label observed branch only |
| `schema.py:543`, `github_knowledge.py:126` | Existing links are single-repo mentions/closes | Qualified identity required; no global bare-number joins |
| `github_reconciliation.py:49`, `:139` | Explicit links distinguished from similarity | Similarity is not verified membership |
| `utils/CLIO/prompt-log-to-md.sh:529` | Existing prompt-note exporter has its own cursor/atomic replacement | Leave it untouched; separate private preview |
| `utils/daily_synthesis.py:117`, `:340` | Marked-block preservation and zero-row non-clobber precedent | Preserve personal notes; do not repurpose daily writer |

## Existing failure and rollback paths

Capture and export cursors have retry/dedup contracts; replay must not touch them. CLIO ingest skips
malformed JSON and can fail on bad field types; existing recent reader returns empty on exceptions.
Source freshness, missing data, malformed records and cap truncation must be distinct report fields.
Repo basenames do not establish canonical identity; tail-time branch metadata is not historical proof.
Cross-device prompt history is not automatically consolidated into this database.
Rollback of derived preview is simply stopping its invocation; no source rollback is necessary.

## Tests and prior art

`tests/test_clio.py`, `test/clio-capture.sh`, `test/clio-codex-tail.sh`,
`test/clio-agy-tail.sh`, `test/clio-exporter.sh`, `tests/test_daily_work_synthesis.py`,
`tests/test_daily_synthesis.py`, `tests/test_github_reconciliation.py`, `tests/test_db_github.py`.
Historical plan `PROJECT/3-COMPLETED/GH-141-CLIO-INGEST.md` already proposed scoped issue references;
the current ingestion code does not implement that association. #150 owns broader read-layer
consolidation; #202 owns producer session identity. This spike does not replace either.

## Unknowns and how to settle them

| Unknown | Bounded verification before execution |
|---|---|
| Actual seven-day capture volume and device coverage | Resolve configured file; bounded scan with counters, metadata only in public receipts |
| DB availability/freshness | Read-only gateway, source fetched timestamps; no refresh without dry-run/scope review |
| Checkout aliases | Resolve explicit remote identities; unresolved basenames stay excluded/uncertain |
| XYZ relay/marathon authoritative export | Inspect XYZ artifact contracts before adding adapter; missing evidence stays a gap |
| Terra shared budget on this device | Inspect existing runner/config and receipt owner; absent safe seam blocks model phase |
| Human correctness labels | Operator review of private examples; do not substitute another model |

Current blast radius: read-side CLIO, GitHub artifact reads and Terra packet/output seam. No capture,
schema, schedules, ranker or provider changes justified. Runtime tests were not run during source recon.
