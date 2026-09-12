# GH-211 bounded runtime recovery — campaign record

Date: 2026-09-12  
Implementation commit: `ca798c0`  
Baseline commit: `3801fa5`

## Status

Code implementation and its preservation suite are complete. Live recovery and deployment have not
yet run. Observations below describe the pre-recovery Mac Studio state and must not be read as a
post-deployment health claim.

## Reproduction and red controls

The incident was reproduced with non-empty runtime evidence: an Apple M1 Max Mac Studio with 64 GiB
RAM had scheduled processes alive for roughly 2–26 hours, a roughly 4.93 GiB database with a large
WAL, 1,735 orphan semantic vectors, 4,472 pending embeddings, and a pulse artifact more than one day
old that still reported healthy. Sample stacks placed GitHub sync in SQLite commit/checkpoint work,
embedding and triage jobs in SQLite scans, and daily sync waiting on a subprocess. The shared Git
checkout was 112 commits behind and had a zero-byte, ownerless `.git/index.lock` plus unique tracked
and untracked work.

Before implementation, focused controls failed on all newly claimed behaviors:

- the guard rejected the new wall-clock argument and did not own a deadline;
- three pulse-health cases accepted missing schedule-aware staleness behavior;
- dirty-identical and committed-but-unpushed Git states produced two false-green failures;
- semantic orphan repair had no importable supported entry point.

Each control subsequently passed against the implementation. Fixtures asserted non-empty process,
Git, and SQLite state; their mutations were confined to temporary test locations.

## Completed verification

| Gate | Result |
| --- | --- |
| Focused integrated suite | 124 passed, 1 warning |
| Python 3.13 root suite | 2,347 passed, 20 skipped, 10 xfailed, 143 subtests passed, 1 warning |
| Python 3.13 HiQS suite | 163 passed, 1 skipped, 1 xfailed |
| Final Python 3.12 root non-seam lane | 2,349 passed, 20 skipped, 10 xfailed, 143 subtests passed, 2 warnings |
| Python 3.12 embedding seam | 8 passed |
| Python 3.12 HiQS suite | 163 passed, 1 skipped, 1 xfailed |
| Relay focused regression suites | 89 passed after round one; 8 passed after round two |
| Ruff lint | clean |
| Ruff format check | 620 files already formatted |
| mypy `src/` | success, 113 source files |
| Read-layer ratchet | clean, 52 baseline sites |
| Shell syntax | `stack.sh` and `scheduler_common.sh` clean |

Both supported Python lanes and the separately installed embedding seam completed. The independent
implementation relay found and closed publication, transaction, error-masking, exact-content, and
audit-order gaps, then approved the full branch in round three. The final full Python 3.12 run above
was executed after all review fixes.

## Recovery safeguards

No live operational state has been mutated yet. Before recovery, this record will be extended with
the resolved database and Git paths, PID and holder evidence, backup locations, integrity results,
every applied command, and exact restoration commands. Any live DB holder, failed exclusive
transaction/checkpoint, unpreserved Git state, or failed integrity check stops later mutation.

The full PDDA report also contains pre-existing repository debt outside GH-211 (frontmatter,
roadmap coverage, hardcoded-path, and issue-sync findings). Those findings are not attributed to
this change; GH-211's two plan documents are checked independently.
