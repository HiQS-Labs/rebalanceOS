# T3 capture verification

Tracking: [GH-370](https://github.com/HiQS-Labs/rebalanceOS/issues/370).
Plan: [capture contract](../../PROJECT/2-WORKING/GH-370-T3-CLIO-CAPTURE.md).
Base: `f0819314c078f58e9d51b6ccd698c76b700ec1cc`.
Environment: macOS, Python 3.14; synthetic T3 sources and temporary CLIO homes.

The added store cases first failed on the base helper with AttributeError for
missing configure_t3/capture_t3. The implemented cases cover short/multiline
prompts, steering, multiple providers, fresh human input in imported and child
threads, version/creator/source filtering, page boundaries, missing project/run
metadata, changed projections, interrupted cursor publication, queued writes,
scheduled exports and idempotent rereads. Source bytes remain unchanged.

`clio-store.txt` retains the store suite output. Existing `test/clio-capture.sh`,
`test/clio-runtime.sh`, `test/clio-exporter.sh`, `test/clio-codex-tail.sh` and
`test/clio-agy-tail.sh` passed. SQLite/import and script-inventory ratchets passed;
documentation link checking found no broken links or machine-local paths.

`smoke.txt` records the real CLI configure/capture path on a disposable fixture,
then a second capture invocation. The setup reuses the existing acceptance
fixture, not a new runner: activate a temporary store, create its synthetic T3
source, register with configure-t3, append one `ok` human event, invoke capture-t3
twice, and assert one unchanged record with T3 provenance.

Independent plan QA round 1 requested steering attribution, event-level import
filtering, explicit frozen identity/retry policy and version boundaries. All four
were accepted; round 2 Approved implementation. Reviews ran through T3-managed
Codex delegation because host orchestration takes precedence over shell relay.

Runtime doctor ran and returned failure for an existing silent fleet device and
an existing scheduled digest failure, plus configuration/staleness warnings.
This change does not modify fleet or job configuration. No overall machine-health
claim is made. Full repository tests and final independent QA are pending.

## Threats to validity

The fixture matches the inspected unified V2 T3 event/projection contract; other
layouts deliberately refuse capture. No live installation or post-merge rollout
was performed. Native provider capture may independently retain the same input;
this proves T3 submission retry deduplication, not cross-harness reconciliation.
Metadata is observed from projections at capture time. Full machine health is
not qualified by these focused capture checks.
