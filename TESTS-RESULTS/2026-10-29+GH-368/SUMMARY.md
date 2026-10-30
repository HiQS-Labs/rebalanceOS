# Codex capture repair verification

Date: 2026-10-29 · Tracking: [Rebalance #368](https://github.com/HiQS-Labs/rebalanceOS/issues/368), [Forge #1255](https://github.com/HiQS-Labs/XYZ-forge/issues/1255).

## Result

Modern and legacy capture, durable replay after a failed second write, SQLite stable IDs, live IDE request extraction, child/response-item exclusion, normal retries and warning threshold/reset pass in the existing Codex suite. Existing capture, exporter, Agy and runtime suites pass; the store suite passes all 17 cases after the one-line fixture correction described below. Source code tested at 4d8bbc9; earlier adjacent passes at 728db07 cover unchanged relevant components. Static push gate passes (Ruff/format and existing ratchets).

## Controls and correction

- Unchanged base parser extracts zero rows from a complete synthetic modern event without reporting malformed input (base-red.txt).
- Updated fixture against base tailer fails: expected two prompts, delivered one (red-base-modern.txt).
- Removing the durable replay checkpoint fails the pending-rewind assertion (red-lost-replay-checkpoint.txt).
- Disabling the warning fails its threshold assertion (red-disabled-canary.txt).
- One added deferred-write assertion initially reused the accepted prompt's timestamp and hit legacy dedup. Give the deferred fixture a distinct timestamp; keep the assertion. Its failure and corrected pass are retained.
- The existing store suite independently fails on unchanged development because a fixed September source row falls outside the rolling seven-day view (base-store-control.txt). Use the existing UTC helper only for that case's source row; preserve the five-row assertions. Production store code is unchanged.

## Boundaries

All CLIO suites ran in a disposable full clone using synthetic data/temporary homes; runtime installer tests stub launchctl. Repository identity checks remained intact. There are no new suites, registry entries, gates, storage schemas or services.

The synthetic SQLite capture plus ordinary retry and repeated replay are the main/adjacent smoke paths; nonempty rows and stable record IDs are asserted by the existing suite, rather than inferred from delivered counts. Live rollout text and databases were never committed. No installed hooks, schedules, SQLite history or remote runtime were modified.

Target-device live delivery within 120 seconds, requested-session backfill, upstream merge and standalone publication remain outstanding. Session 01a18930 has no submitted events in the inspected source; response-item fallback remains forbidden. This verification establishes implementation behavior, not fleet acceptance. Independent plan and final Codex reviews were each Approved in round 2; relay receipts are committed under relay-system/2026-10-29.

## Repository documentation hygiene

The repository-wide PDDA check is in observe mode and reports 25 existing frontmatter/status/roadmap findings. All affected project documents are unchanged from development; GH-368 has no finding. These are not a green full-repository hygiene result. The initial missing local checker environment was corrected, and the direct banned-import ratchet passes. See pdda-existing-findings.txt. No unrelated governance cleanup is included.

Final machine gate: the cross-repo transcript approval could not publish its machine record because its parent is ignored. The supported Forge external-artifact review supersedes that attempt: [round-3 final QA and driver attestation](https://github.com/HiQS-Labs/XYZ-forge/blob/126ccd2a/relay-system/2026-10-29/gh1255-publication.codex.md). relay-drive returned 0 and its receipt validated; capture code remains unchanged since the tested revision.
