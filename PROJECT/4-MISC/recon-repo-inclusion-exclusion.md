# Recon Map — repository inclusion and exclusion

Commit: fdc94ed64d4ad30bf77a6eb3cb19897058ece03a · Date: 2026-09-06 · Mode: graph+read · Lanes: parent B/state and A/entry; independent A/C/D consumer review.

## Table of contents
- Subject and change class
- Seams and call paths
- State and contracts
- Build, failure and rollback
- Unknowns
- Current-state radius

## Subject and change class
Sizing only: consolidate explicit repo inclusion/exclusion into one file, or move exclusions into the current project registry. State/authority and serialized-contract change. No implementation approved or performed.
Graph generation 2026-09-02 is stale: used as discovery leads, exact current source used for findings. Config/registry/index_ops coverage reports metadata_changed, no recorded parse gaps. Consumer lane used direct-source fallback. Recon references spike-360, but that skill was absent from the Codex/Agents/Claude skill roots searched; authority choice remains provisional. This does not prevent reporting the existing source dependencies.

## Seams and call paths
| Seam | Location | Crosses | Breaks if |
|---|---|---|---|
| Include confirmation | src/rebalance/mcp/tools/onboarding.py:120; src/rebalance/ingest/preflight.py:343 | MCP → vault registry → YAML projection → SQLite | New policy lost during confirmation or failed projection |
| Registry serialization | src/rebalance/ingest/registry.py:38,134,158,304 | Pydantic Registry → Markdown/YAML → projects.yaml → DB | Adding only a YAML key does not make it a supported round-tripping field |
| Exclusion commands | src/rebalance/cli/config_cmds.py:54,121,134 | CLI → config helpers; optional separate DB purge | Commands start requiring a vault/DB or lose normalization/purge behavior |
| Shared exclusion accessor | src/rebalance/ingest/config.py:1019 | no-argument config API → consumers | Readers require new runtime context or see different versions of policy |
| Effective membership | src/rebalance/ingest/index_ops.py:864,963 | active DB projects + activity/pushed/external − ignored | Registry and exclusion generations diverge; precedence changes |
| Direct collection | src/rebalance/ingest/github_knowledge.py:432; github_scan.py:478 | explicit sync and activity storage | Only changing watched selection leaves direct paths on old policy |
| Derived/display filters | src/rebalance/ingest/semantic_index.py:322; project_inference.py:198; note_builder.py:52; scripts/dashboard.py:346,397,482 | projection/inference/reporting | Historical stored content uses stale exclusion data |
| Coverage alarms | src/rebalance/ingest/watchlist_guard.py:153 | exclusions → removal classification | Deliberate exclusions produce false coverage-loss alarms |

## State and contracts
- Include is not a standalone whitelist: Project.repos in active registry rows is also project ownership metadata (registry.py:14). Machine inference/promotion can write DB project rows; moving all includes to a standalone file needs a decision about manual policy versus derived ownership.
- Registry.read/save and push/pull/check operate on a typed Registry. Projection currently returns only projects; sync_db upserts project rows (registry.py:158–261). Global exclusions need explicit preservation and projection semantics, not a fake excluded project.
- Exclusions are operator-local JSON config, normalized by config.py:1019–1069. Resolution honors test override/environment then checkout paths (config.py:204). _write_config writes the complete config and hardens permissions (config.py:284); this file can contain secrets. Do not move the complete config into a shareable registry.
- Effective selection reads active projects from SQLite, not directly from registry Markdown (index_ops.py:864). A single editable file would still have runtime projections.
- Canonical identity and blacklist-wins must survive migration (index_ops.py:981–1028). One file alone does not detect contradictions; explicit overlap validation still needed.
- Existing get_watched_repos response already includes project_repos and ignored, allowing a combined operator view without relocating authoritative state.
- AGENTS.md:153 explicitly requires vault-optional refresh. A direct mandatory vault read for exclusion conflicts with that contract.

## Build, failure and rollback
Existing test families include test_config_github_token.py (normalization), test_github_ignore_cli.py (commands and purge), test_watched_repos.py, test_github_knowledge.py, test_semantic_index.py, test_project_inference.py, test_auto_promote.py, test_watchlist_guard.py and test_dashboard_terminal_theme.py. Consumer lane read relevant test assertions; no tests run for this sizing-only task.

Current config missing/invalid read returns defaults with warnings for invalid content (config.py:256). Registry missing returns empty, malformed YAML raises RegistryLoadError (registry.py:110). Confirmation can save Markdown while projection reports sync_ok false (preflight.py:392–411). Any storage migration must define how exclusions remain effective across these failure modes.

Rollback requires retaining legacy exclusion data until conversion and runtime reads are verified. Permanent dual writes risk contradictory sources; old executables saving the typed registry may discard newly introduced fields. Existing ignore CLI can act without resolving a database unless purge requested (config_cmds.py:69–80). Preserve that independence or document an intentional breaking change.

## Unknowns
| Unknown | Why it matters | What settles it |
|---|---|---|
| Device-local versus shared exclusion policy desired | Moving to a synced registry can change who/devices an exclusion affects | Operator product decision |
| External consumers of config helpers/key | Local graph/source does not prove cross-repo completeness | Bounded dependent-repo/config consumer audit before implementation |
| Target authority and vault-free projection strategy | Determines actual migration size; no design selected | Short authority/portability spike; referenced spike-360 unavailable |
| Mixed-version rollout behavior | Older registry writers may erase a new field | Round-trip compatibility check with old/new writers |

## Current-state radius
CLI and MCP setup, registry serialization and SQLite projection, GitHub collection/direct sync, inference, semantic projection, dashboard/org summaries, diagnostics and coverage alarms. Shared accessor can contain most consumer code changes, but all listed behaviors need regression checks.

Qualitative sizing: combined view/conflict warning is low radius; one standalone explicit-policy file is medium with migration; placing exclusions in the existing vault registry is medium-to-high because of projection and vault-independence contracts. These are engineering judgments, not measured estimates.
