# GH-282 verification — 2026-10-02

Baseline: 2804 passed, 143 subtests. Final candidate: 2807 passed, 146 subtests, 21 skipped, 11 known xfails.
Final code identity is pinned in source-manifest.json. Tests run only in a disposable full clone;
Git identity checked (non-bare, expected local origin and HEAD) before attributing results.

The four-clone real-Git probe exercises simultaneous collectors, commit-only Python publishers,
per-device pages/sync, no latest pointer, canonical owner-only CLIO export (including a DB with
imported foreign history), derived fleet view, delivered/queued failure health, foreign dirty refusal,
busy lock 75, stale index lock and timed-out push 2 with pending working blobs/watermark preserved.
These are synthetic records; no operator prompt text or private DB is committed.

Red control witnessed: at 16a0115 the forced failed renderer still classified ALIVE because only the
migration metadata carried fleet_mode. The regular metadata marker fix in 54f82f1 changed that same
check to ALIVE_NOT_PUBLISHING. A stale-index failure may leave newer generated output dirty; the
next PREPARE correctly preserves it as a commit. The timeout oracle compares those pending bytes,
not old heartbeat/manifest timestamps. Initial whole-HEAD/timestamp assertions were corrected.

Local static gates: ruff check/format, mypy (117 source files), SQLite gateway/banned-import,
script inventory, machine paths, read-layer, near-duplicates and all 626 documentation links pass.

Plan review: actual claude-fable-5-1 high-effort rounds 1/2; findings then PASS. Plan driver's final
attestation commit failed on the ignored relay folder (exit 4), so that is explicitly not counted as
implementation attestation. Final implementation QA uses this tracked evidence directory instead.

Still open: real four-Mac rollout, shared-note recovery/source inventory/archive capacity pilot,
three actual Pulse intervals including disconnected/rejoin, external hook/PDDA lock participation,
and seven-day failure-rate qualification. Other Macs remain disabled. No source-gap recovery required.

Implementation review round 1 found premature overnight aging and ambiguous queue/failure output. Fixed scheduled silence allowance to 10 hours (including DST and existing delivery budgets); explicit failures and pending work still warn immediately. Three added methods in the existing health suite went red against the old source (five failures including subtests), then all 54 focused cases and three subtests passed. Status commit errors and failed delivery proof now return Git exit 2; CLIO failure conservatively stops before a new heartbeat. A pre-existing text-mode CR normalization edge remains unobserved and is not redesigned.

Final independent implementation approval: Claude Fable 5.1 high, round 2, native driver exit 0, reviewed head 9719f95. All round-1 findings dispositioned; round-2 queue-warning documentation added, stale plan count corrected; text-only health wording/docstring nits deferred. QA receipt: QA/gh282-implementation-fable-r2.md.
