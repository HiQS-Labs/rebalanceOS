# Daily recorded-status reader evidence

Original implementation head1f1f16b: 36 focused tests pass; changed product paths pass lint/format;
SQLite and import ratchets pass. Nine witnessed controls fail in a disposable
full clone (eight exit1; removed SQL progress callback exceeds external2s guard,
exit124). Every patch is restored; restored36-test run passes and tracked diff is
empty. Source bytes/sidecars, no-configuration/CLI sentinels, qualified identity,
native observation age/conflicts, quiet-work caps, closure precedence, minimized
egress and model/fact separation have nonempty fixture coverage.

Takeover qualification on rebased head b63ae90: 50 focused tests pass. Broad
supported core reports 2472 passed, eight failed,20 skipped,10 xfailed and143
subtests passed. The same eight failures reproduce on unchanged development
cf73f1a in a separate fresh full clone; failures remain failures, not a full-suite
pass. Separate HiQS163 pass,1 skipped,1 xfailed;
missing private-name scan is unknown. 3-Eyes remains stood down and wasn't run.
Complete diagnostic logs remain ignored in disposable-clone temp directories;
sanitized summaries and command/SHA provenance are retained here.

Takeover review resolved the WAL contract without adding a snapshot service or
changing journal mode: normal SQLite WAL/SHM coordination files are allowed, while
the native reader must preserve database bytes, logical records, schema and WAL
mode and reject UPDATE, DELETE and CREATE TABLE. A regression reads nonempty facts
from an active WAL database and proves those invariants. A second regression proves
that ledger repository aliases join the canonical native-cache identity rather than
degrading a valid active task to unknown. Final post-rebase qualification is recorded
on the pull request's exact head SHA.

Post-ready automated review exposed two boundedness regressions with witnessed red
controls: packet reduction retained only recorded-status evidence and displaced the
existing work evidence, while the 2,000 native-row ceiling applied once per alias
query chunk instead of to the whole read. Packet reduction now retains up to eight
status and eight non-status evidence items, truncates rendered status facts to eight
and marks the result partial. The native-row ceiling now rejects aggregate alias rows
above 2,000. The expanded focused set passes 52 tests; changed product and test paths
pass Ruff lint and format checks.

XYZ646 writer is unmerged: no deployed skill, real pilot, source label/status
writes, merge, passing broad gate or end-to-end qualification is claimed. PR234
is a concurrent Daily ownership/ledger-opt-in change to preserve on refresh.
