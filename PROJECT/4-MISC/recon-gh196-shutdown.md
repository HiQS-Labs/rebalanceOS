# Recon Map — shutdown beside daily

Commit: ed320289f78abe2e5f0228457a95b07a614c2d00 (fresh origin/development).
Mode: graph leads + direct source. Graph generation 2026-09-02T03:54:57Z is
older than this base; ignored skill/log paths are verified from source instead.
Lanes: primary A/D (entry/operations); read-only delegated B/C (state/boundaries).

## Subject and change class

Extend the existing daily conversational workflow and local loop scanner with an
on-demand end-of-day projection and reviewed handoff. No new canonical task store;
Git/GitHub/project plans retain authority. Action authority stays in merge-cleanup.

## Seams and current paths

| Seam | Location | Observed contract / consequence |
|---|---|---|
| Conversational entry | `.agents/skills/daily/SKILL.md:51-52,65-67,123` | Agent runs scanner, reads previous daily log, appends synthesis. Shutdown can reuse this consumer path. |
| Scanner discovery | `.agents/skills/daily/scripts/scan_unclosed_loops.py:23-85` | Hardcoded roots; directory-mtime admission; does not establish recent nested edits. |
| Git inspection | same scanner `:88-130` | Current branch upstream comparison; command failures are not consistently represented as unknown. Human worktree-list parsing; no active-process proof. |
| PR collection | same scanner `:133-154` | Hardcoded remote list; failed queries disappear; not an exhaustive paginated discovery contract. |
| Ledger writer | same scanner `:157-213,216-270` | Rewrites whole ledger; update flag defaults true. `--json` is not a no-write switch. |
| Branch classification | same scanner `:234-249` | Linked worktree branches count as un-PRed without joining to returned PRs. Dirty count is gated on HEAD age. |
| Duplicate compatibility copy | `.claude/skills/daily/scripts/scan_unclosed_loops.py` | Separate implementation, including timezone differences; preserve invocation via a thin forwarding shim rather than a third copy. |
| Broader device scanner | `.claude/skills/rebalance/collect.sh:33-59,79-105,122-152` | Read-only, configurable roots/window; groups by git-common-dir and parses porcelain. ACTIVE is commit-age-based, not evidence of a running process. Reuse semantics, not an unreviewed delete decision. |
| Existing EOD publisher | `utils/daily_synthesis.py:1-35,464-539` | Scheduled vault/CLIO writes and Gemini synthesis. Not the manual daily skill, and not an appropriate dependency for a no-publish MVP. Leave unchanged. |
| Canonical DB resolution | `src/rebalance/paths.py:506-513` | Existing resolver, not sibling-folder guessing. Runtime enrichment must not create a missing DB. |

## State and privacy

Existing daily output is `temp/daily-log/YYYY-MM-DD.log`; loop inventory is
`temp/close-the-loop.md`. These are gitignored, local, not proof of live Git/PR
state. Earlier local September 5-6 logs contain prior-day arcs and explicit pending
PR nudges; private contents are not copied into this public recon. The reviewed
September 7 local log ended at noon. This is sampled historical context, not a
claim of current fleet completeness or runtime DB freshness.

The scanner currently owns ledger replacement. Shutdown should keep reviewed human
decisions outside that regenerated file, in dated sibling handoffs under the same
daily output root. Runtime config/output-root selection must be explicit; dev and
runtime clones can hold different temp trees. No private state in disposable clones.

## Failure and rollback today

The scanner's JSON path still writes the ledger, so this recon did not execute it.
Tests/read-side code inspection are needed before treating observations as cleanup
clearance. A no-change snapshot does not prove absence of background agents; Git
fetch/checkout can change timestamps without new operator work. No current source
can recover every transient CRUD operation or reliably reconstruct file reads.

## Optional enrichment — confirmed B/C lane

`src/rebalance/ingest/db/connection.py:91` supplies an existing mode=ro gateway;
normal connections (`:20-33`) create parents/DB and request WAL mode. The
connection-taking `db/queries.py:389,497,563,776` readers are reusable, but their
fetchall paths are not inherently bounded. Add a narrow bound/deadline option at
that existing read seam, preserving default behavior and alias deduplication.

`ingest/registry.py:334-384` owns project decoding but initializes schema; a
read-only/connection-taking option can retain that one reader. Do not assume
`pulse.py:451-529` or `index_ops.py:508-527` are pure reads: they use the writable
gateway, and pulse can also query GitHub. No new raw SQL in the shutdown wrapper.

`ingest/config.py:204-229` can resolve config from the caller's CWD; explicitly pin
the intended config. `get_repo_scan_roots:752-785` can fall back to home; shutdown
must require bounded configured roots. `paths.py:201-246` resolves an existing DB,
which need not be in the runtime checkout. Runtime Python >=3.12 and dependencies
must remain optional to the stdlib-only basic scanner (`pyproject.toml:10-23`).

Freshness comes from source `fetched_at`/`scanned_at`, not DB mtime. Arc/phase
ownership is not established by the DB schema; resolve linked project plans or
record unknown. The live runtime/DB were intentionally not opened in this recon.

## Unknowns / bounded follow-up

| Unknown | Why it matters | Resolution before implementation |
|---|---|---|
| Optional enrichment helper integration | Existing pure connection and schema-ensuring wrappers differ | B/C lane identified the seams above; Phase 0 confirms adapter on immutable fixture. |
| Runtime-installed output/config identity | Dev logs need not live in runtime | Resolve explicit configured durable root, report provenance; no silent discovery of private config. |
| PR #195 landing order | Edits daily SKILL.md | Re-read remote before implementation; preserve its CPU-health additions. |
| Arbitrary IDE session liveness | No universal process ownership registry | Two-pass changes + available lock/CWD evidence; unknown is not safe, never kill processes. |
| Full historical CRUD | No ubiquitous filesystem event journal | Bound claim to observable evidence and current unresolved state; document missing reads/transient deletes. |

Current-state radius: the daily skill's users, its compatibility invocation, local
loop ledger and daily logs; optionally the existing read-only Rebalance data paths.
New radius: dated private handoff output plus an explicit, revalidated delegation
to the separately governed merge-cleanup workflow.
