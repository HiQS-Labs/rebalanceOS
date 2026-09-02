---
title: "GH-150 Activity-Signal Read-Layer Consolidation — Audit"
status: "Queued (issue filed, not started)"
created: 2026-09-02
issue: "https://github.com/HiQS-Labs/rebalanceOS/issues/150"
parent_plan: "PROJECT/2-WORKING/BUILD-0.75.0-FLEET-ENGINE/SCOPE.md (phase fe1)"
trigger: "#147 — the org-mirror defect had to be hand-patched into three surfaces; this audit asked where else it lives"
effort: 3
complexity: 3
risk: 2
---

# GH-150 — Activity-signal audit: one pipeline, many read paths

## TOC

1. [Verdict up front](#verdict-up-front)
2. [The one pipeline (ingest) + two cataloged side-pipelines](#the-one-pipeline-ingest--two-cataloged-side-pipelines)
3. [Consumer catalog](#consumer-catalog)
4. [Findings F1–F7 (with evidence)](#findings)
5. [Phased plan](#phased-plan)
6. [Phase 0 spike (½ day max)](#phase-0-spike)
7. [What this audit deliberately does NOT propose](#what-this-audit-deliberately-does-not-propose)

---

## Verdict up front

- **Ingest is already one pipeline.** `refresh_index` + `COLLECTORS` (`src/rebalance/ingest/index_ops.py`) is the single data-plane spine; every scheduled writer dispatches through it. Two side-pipelines bypass SQLite by design and are cataloged, not condemned (§2).
- **The fragmentation is on the read side.** Five surfaces produce "today's activity" summaries; each carries its own collectors, window math, and repo grouping. The #147 org-mirror defect exists in **seven more places** because repo identity is re-derived per surface instead of once.
- **The fix direction already exists and is parked**: 0.75.0 Fleet Engine fe1 (`db/queries.py` shared read layer). This audit extends fe1's scope; it does not propose a competing plan.

## The one pipeline (ingest) + two cataloged side-pipelines

| Path | Writes | Status |
|---|---|---|
| `refresh_index` → raw tables (`vault`, `github`, `calendar`, `sleuth`, `email`, opt-in `figma`/`clio`) → `semantic` projection | SQLite `rebalance.db` | ✅ single pipeline, registry-driven |
| git-pulse fleet check-in (`experimental/git-pulse/`, device YAML/TSV in its own sync repo) | its own git store | by design (cross-device); should be *named* in the COLLECTORS taxonomy (F7) |
| Claude Cloud sessions API (Anthropic) | no store (read on demand) | signal implemented **twice** (F5) |

## Consumer catalog

| # | Surface | Cadence | Input path | Synthesis | Output channel |
|---|---|---|---|---|---|
| C1 | `utils/hiqs_digest.py` (GH-142) | 2×/day 13:05/17:05 | own SQL collectors (github tables, doctor subprocess, semantic query) | Gemini via `querier._synthesize_gemini` ✅ | pulse repo `digests/` → Slack relay |
| C2 | `utils/daily_synthesis.py` (GH-74) | daily 18:20 | `pulse.collect_pulse_snapshot` + `git-pulse view.sh` (device files) | Gemini ×2 via same primitive ✅ | Obsidian daily note + CLIO log |
| C3 | `pulse.py` (`pulse-sync` hourly; `pulse_web.py` every 30 min) | hourly / 30 min | `_query_day_activity` + `_query_watched_activity` | none (deterministic) | pulse repo README + `web/pulse.html` |
| C4 | `note_builder.py` dashboard note | on refresh | `github_activity` rollup + calendar | **own Gemini REST client** ❌ (F2) | vault dashboard note |
| C5 | `next_actions.py` | on refresh / MCP | reuses `pulse._query_day_activity` ✅ + own windows ❌ (F3) | Gemini via `querier` ✅ | MCP `get_next_actions` |
| C6 | `github_scan.get_github_balance` (MCP `github_balance` + `querier.ask()`) | on demand | `github_activity` GROUP BY raw repo ❌ (F1) | n/a (facts layer) | MCP |
| C7 | `daily_report.py` / `weekly_report.py` | on demand | `calendar_events` only (clean; weekly imports daily ✅) | none | vault notes |
| C8 | `utils/claude_cloud_daily_grade.py` (GH-128) | daily | `ingest/claude_cloud` sessions API | none | Obsidian block |
| C9 | `scripts/cc_cloud_jobs.py` (POC) | manual | Anthropic API directly ❌ duplicate of C8's source (F5) | none ("synthesize" is an f-string) | stdout + `temp/` |

## Findings

Evidence is file:line as of 2026-09-02 (commit on `fix/gh147-digest-mirrors-stale-repos`).

- [ ] **F1 — alias-blind repo identity, 7 surfaces.** `canonical_github_repo_name()` exists (#149, merged) but is used only by `get_watched_repos`, the digest SQL, and the watchlist guard. Alias-blind today: `get_github_balance` (github_scan.py:766–797 — raw GROUP BY + exact dict match against registry strings; 6 registry entries still name `HiQS-Suite/…` spellings and 3 repo names carry BOTH spellings in `github_activity`, so balance sums one spelling and silently drops the mirror — or double-counts when a registry entry lists both. Casing is NOT a live defect: the table stores GitHub-cased names (verified live, accuracy review 2026-09-02); only the watched-repo rollup path writes lowercase, so the exact match is fragile rather than wrong today), `note_builder.get_all_repo_activity_by_org` (62–81 — raw GROUP BY then org-prefix split: one project under two org headings), `pulse._query_day_activity` (raw repo strings; commit-dedupe anti-join at 258–261 keys on raw repo, so a mirrored sha counts twice — not theoretical: **2,513 shas** sit under both spellings in `github_direct_commits`), `pulse._query_watched_activity` (615–660, LOWER only), `next_actions` (1145–1167 LOWER-only project matching; 1086–1095 raw-lower), `diagnose.diagnose_repo` (LOWER-only), `github_readiness` (exact `=` everywhere → under-counts).
- [ ] **F2 — two Gemini REST clients.** `querier._synthesize_gemini` (379–437) vs `note_builder.synthesize_dashboard_narrative` (326–388, own urllib POST + parsing). C1/C2/C5 import querier's correctly.
- [ ] **F3 — day/window logic, 5+ flavors.** pulse `_local_day_bounds`/`_utc_iso_floor`/`_in_window` (105–139); digest `_utc_day_bounds` (DST-correct); verbatim-duplicated `scan_date` cutoff (github_scan.py:763 == note_builder.py:51); `next_actions._local_day_window` (962); querier vault cutoff (153). Plus naive `date.today()` in weekly_report (25, 153) and bare `astimezone()` in the Claude Cloud paths.
- [ ] **F4 — commit semantics differ per surface.** Both-tables dedupe: pulse `_query_day_activity` ✅ (raw key caveat), digest CTE ✅ (canonical key). PR-commits-only: `_query_watched_activity`. Window-total rollup: `get_github_balance` reads `github_activity`, the very table the digest documented as *not* a day total (hiqs_digest.py, by_repo design note). Three surfaces, three answers to "how many commits happened".
- [ ] **F5 — Claude Cloud signal implemented twice.** `scripts/cc_cloud_jobs.py` vs `src/rebalance/ingest/claude_cloud.py`: `norm()`≙`normalize()`, `enrich_pr_status()`/`_gh_pr_for_branch()` near-identical, token lookup + sessions fetch duplicated. POC is declared standalone-on-purpose; that declaration should expire.
- [ ] **F6 — per-job utility retyping.** `upsert_marked_block`/`build_marked_block`/`log`/time-format duplicated between `daily_synthesis.py` (95–139) and `claude_cloud_daily_grade.py` (34–107).
- [ ] **F7 — taxonomy bookkeeping.** git-pulse device files and the Claude Cloud API are legitimate side-sources; name them in the COLLECTORS taxonomy (ARCHITECTURE.md) so "one pipeline" stays a checkable claim.

## Phased plan

Each phase lands independently; F1 is sequenced first because it is the only finding producing wrong numbers today.

- [ ] **P1 (fe1 extension) — `db/queries.py` with canonical repo identity.** Move `get_github_balance` + `get_all_repo_activity_by_org` + the pulse day/watched aggregations behind one query module whose every GROUP BY / join / dict key routes through `canonical_github_repo_name().lower()`. Mirror-fixture test pattern: `tests/test_hiqs_digest.py::test_org_mirror_rows_collapse_into_one_repo`. Lands inside [BUILD-0.75.0-FLEET-ENGINE/phases-briefs/p1-shared-read-layer.md](../2-WORKING/BUILD-0.75.0-FLEET-ENGINE/phases-briefs/p1-shared-read-layer.md) — that brief is the executor-facing plan this audit feeds.
- [ ] **P2 — one synthesis primitive.** `note_builder` imports querier's; delete its client. Guard: grep-level CI check that exactly one Gemini endpoint implementation exists. Decision point (accuracy review): querier exposes TWO entry points — `_synthesize_gemini` (called directly by `hiqs_digest` and `daily_synthesis`, bypassing the fallback ladder) and `_synthesize_with_fallback` (used by `next_actions`). Pick one as the public surface before collapsing `note_builder` onto it, or the collapse preserves the bypass.
- [ ] **P3 — one day-bounds helper + one commit-dedupe definition.** Consolidate F3/F4 into the query layer (or `lib/time_ops`); fix weekly_report's naive week arithmetic while there.
- [ ] **P4 — deletes.** Retire `cc_cloud_jobs.py` (port any operator-facing output to `ingest/claude_cloud`), collapse F6 utilities into one `utils` helper module.
- [ ] **P5 — catalog.** ARCHITECTURE.md gains the Source→Consumer fanout table (§Consumer catalog above) + F7 taxonomy entries; contract test: no user-facing surface aggregates per-repo GitHub activity outside `db/queries.py`.

## Phase 0 spike

½ day, before P1: hand-run `db/queries.py`'s candidate API against a **copy of the live DB** and diff every affected surface's numbers before/after canonical keys (`github_balance` per project, dashboard org table, pulse watched section, digest by_repo). Any count that moves is either a mirror double being fixed or a regression — the diff makes each one explainable. Expected magnitudes (accuracy review, live DB 2026-09-02): the pulse day view should show a **visible** delta, not just balance — 2,513 shas sit under both org spellings in `github_direct_commits`, exactly the input its raw-key anti-join double-counts. Also measure `canonical_github_repo_name()` cost in the query hot path (config read per row would regress pulse render; likely needs a per-process cached alias map).

## What this audit deliberately does NOT propose

- No second pipeline, no new store — ingest stays `refresh_index`/COLLECTORS.
- No touching 3-Eyes (stood down per AGENTS.md).
- Not the API burn rate (#148) — collector-side, separate effort.
- Not merging git-pulse's device store into SQLite — cross-device by design; catalog only.
