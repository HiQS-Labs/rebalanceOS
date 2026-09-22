---
gh_issue: 233
source: https://github.com/HiQS-Labs/rebalanceOS/issues/233
title: Daily established-work status reader
status: Reader built — review and producer landing required
created: 2026-09-17
updated: 2026-09-17
owner: Codex
goal: Display trustworthy task status without writing source statuses or adding a tracker.
doc_type: project
branch: feat/gh233-daily-status-reader
effort: 3
complexity: 3
risk: 2
phases: 1
---

# Daily established-work status reader

## Status

| What was just completed | What's next |
|---|---|
| Reader and Daily skill changes are rebased after PR234. Fifty-two focused tests and eleven witnessed red controls pass, including WAL preservation, canonical alias joins, aggregate native-row caps and mixed-evidence packet reduction. The same eight broader failures reproduce on unchanged development; standalone HiQS163 passes. | Complete final exact-head qualification and hosted review; producer646 landing remains an end-to-end release dependency. |

## Grounded recon and implementation gate

Existing `utils/daily_work_synthesis.py:116,358,445` owns packet, render and config
handoff. `src/rebalance/ingest/db/connection.py:91` is the true RO gateway;
`queries.py:192` resolves newest canonical issue copies before state filtering;
schema433 already owns labels/state/reason/fetch fields. `utils/py/releases_cycle.py`
is the existing separate-ledger read surface. `.xyz-pin` is not a runtime locator.

Use central explicit/env/user-config path resolution; default no ledger roots.
Extend the existing releases-cycle adapter with the same fixed isolated XYZ helper
invocation reviewed under XYZ673. Parent remains data-only: no external imports,
writer, migration, config dispatch or network refresh. Four roots,2MiB streamed
output,2000 issue cap; ledger window2s within whole adapter6s. Native queries share
that deadline with capped busy wait and progress interruption through the existing
gateway. Resolve newest canonical rows before state interpretation; reject native
host/type/number/owner disagreement or unproven aliases.

Preserve independent root diagnostics and issue facts. Exact in-progress label,
genuine unsuperseded start and native cached open-label agreement establish recorded
work, not execution. Default configurable native freshness7200s; read/fetch/start
clocks remain separate. Quiet old starts stay visible with caution. Fresh closure
wins with completed/cancelled distinction and cleanup warning. NULL, disappearance,
missing/stale/unsafe data, metadata or merged PRs cannot establish completion.

Add a backwards-compatible optional packet argument/config and deterministic
authoritative status block. Model prose stays labelled interpretation and receives
only scrubbed whitelisted facts, never raw payloads, cursors, paths, warnings or
GitHub bodies. Preserve status facts through packet ceiling reduction; do not alter
the output JSON schema, budgets, cadence or existing CPU-state writes. Update only
the relevant instructions in canonical Daily skill; deployment is separate.

Populated fixtures plus source-byte/WAL and no-writer/config sentinels prove
the added reader's preservation. Normal SQLite WAL/SHM coordination files are
allowed; the reader must not change database bytes, logical rows, schema or journal
mode, and write statements through the gateway must fail. Cover agreement, quiet work, closure/cancellation,
label-only/DB-only, unknown/stale/future/invalid timestamps, schema8/9/NULL, foreign
identity, PR exclusion, aliases/newest closure, failed/capped duplicate roots and
reversed order, deadline/output caps, privacy sentinels and adversarial model prose.
Synthetic receipts and witnessed red controls:
`TESTS-RESULTS/2026-09-17+GH-233/`. Private pilot logs stay ignored.

Independent final real-relay QA cap3; focused tests, then applicable supported-core
and HiQS gates in a disposable full clone (3-Eyes remains stood down). Separate
commit/push/PR; no merge or deployment. ProducerXYZ646 and proven end-to-end
comparison remain finish gates. Concurrent PR234 owns ledger opt-in/skill ownership;
its landed changes must remain intact after rebase. Easy rollback disables the additive reader,
without changing source ledgers or labels.

## Ranking rationale

2026-09-17 rated70/45/50/45; neutral appeal, operator-requested priority, incorrect
display costs attention without source mutation; moderate delivery effort, no
invented incident count/override. Existing roadmap remains the pointer ledger.
Plan QA: XYZ `relay-system/2026-09-17/flightdeck-reader-plan-qa.md`; source baseline
ef78114, approved reviewed-plan artifact retained in XYZ673 synthetic receipts.
