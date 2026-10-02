# GH-282 recon — 2026-10-02

Current origin development: 4349ff5. Installed runtime: 17e08c1, 14 commits behind.
Phase 1 merged via PR #283 (1b4d287). No remaining #282 PR or retained remote task branch.

## Writes and ownership
- pulse_sync.sh -> ingest/pulse.publish_pulse -> shared git_ops publisher; root live-pulse.md.
- daily_synthesis.py -> same publisher; shared CLIO daily log, hardcoded push=True.
- hiqs_digest.py -> same publisher; shared date/slot digest, default push=True.
- daily-sync -> sync_snapshot; per-host JSON plus contested latest.json pointers, always pushes.
- CLI refresh/MCP can also publish; policy must apply inside the shared producer boundary.
- collect.sh inherits rebalance-publish.lock, preserves dirty owned output, pulls/rebases, pushes,
  stages collector pulse/metadata/PDDA/snapshots and proves HEAD is upstream before watermark.
  Existing early push lacks a deadline/retry guard; namespace and sync payload staging are missing.
- collector device_id config and Python hostname slug can differ; CLIO owner UUID is a third,
  intentionally distinct identity and must be configured explicitly.

## Readers and reuse
view.sh and health-check.py read device YAML/pulse_file. pulse_health.py feeds doctor.
Daily synthesis already reads the device-attributed view. Dashboard renders its existing local DB.
read_latest_snapshot is pointer-only and can derive the freshest validated snapshot on read.
The existing semantic provider/database and readonly XYZ integration remain unchanged.
Canonical CLIO helper supplies owner export/reconcile/same-note recovery in PR #5; this repo has
only older mirrored collector/install assets, no canonical clio-store.py.

## Failure/rollback boundary
Common Git lock/exact publisher already exists; no replacement queue or push service required.
Foreign dirty files and malformed/conflicting origin data must refuse and preserve local history.
The installed git-pulse binary is a copied executable, not a source symlink. Deployment must update
that copy with a verified backup. Collector cadence 3600s and Markdown cadence 300s stay unchanged.
Three other Macs are disabled. Fleet live qualification is separate from local/synthetic proof.

## Evidence limits
Three bounded read-only source audits checked entries, writers/readers and CLIO seam. Knowledge
graph generation 2026-09-02 was stale; exact current source reads were used for changed/excluded
paths. No claim of exhaustive external snapshot producer coverage or current four-Mac operation.
