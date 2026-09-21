# GH-236 — runtime interpreter diagnosis and local recovery

| | |
|---|---|
| **Ran** | 2026-09-21 |
| **Tracking issue** | [#236](https://github.com/HiQS-Labs/rebalanceOS/issues/236) |
| **Working doc** | [PROJECT/2-WORKING/GH-236-RUNTIME-VENV-DIAGNOSTICS.md](../../PROJECT/2-WORKING/GH-236-RUNTIME-VENV-DIAGNOSTICS.md) |
| **System under test** | GH-236 candidate source plus the declared local runtime checkout |
| **Environment** | macOS, Apple Silicon; Python 3.14.7; pytest 9.1.1 |
| **Primitive** | [`provenance.jsonl`](provenance.jsonl) |

## Outcome

The broken local interpreter was repaired without pulling or modifying the runtime checkout's
tracked files. The rebuilt ignored virtual environment contains the repository's canonical
`embeddings,calendar,server,dev` extras, `stack.sh verify` passes, pulse-server is running, and no
managed launchd job currently reports exit 78. Running the candidate Doctor code against the live
installed plists reports 12 jobs referencing a healthy declared runtime interpreter.

The public candidate adds the missing fleet-level diagnosis and read-only stack warning. The final
implementation review approved commit `ffe48ad74938494e12c62132ce3b3074a007f04b`. The next commit,
`4d02fa992501512cca323ce43253e7903ff34e53`, has that commit as its sole parent and changes only the
GH-236 working document; `git rev-list --count ffe48ad..4d02fa9` returned `1` and
`git diff --name-status ffe48ad..4d02fa9` returned only that document.

## Verification results

| Check | Result |
|---|---|
| Focused Doctor/launchd/stack/version and dependency regressions | 73 passed; Ruff passed |
| Focused tests after the final two policy-boundary fixes | 44 passed; Ruff passed |
| Version/front-door check after CI correction | Passed; package, project, and manifest are 0.88.4 |
| Full `pytest tests/ -q` at predecessor `4a9228a` | 2,418 passed, 17 failed, 20 skipped, 10 xfailed, 143 subtests passed |
| Canonical runtime extras import | FastAPI, Google auth, and sentence-transformers imported successfully |
| `bash scripts/stack.sh verify` in the runtime checkout | Passed all five displayed checks |
| Candidate Doctor check over live plists | OK: 12 installed jobs reference the healthy declared interpreter; overall Doctor exit was 1 because other checks remain non-OK |
| launchd status after repair | zero exit-78 jobs; pulse-server running; six managed jobs retain exit 75 |

Nine failures in the full run were missing-import consequences of the initially documented
`.[dev]` rebuild command: two credential-dedup tests, two embedder tests, two Metal-unavailable
embedder tests, two Gmail-keyring tests, and one OAuth JSON fallback test. After installing the
canonical four extras, all nine passed in the 73-test focused run.

The remaining eight last-failed entries were:

- `tests/test_github_commit_peeker.py::GitCommitPeekerTests::test_sync_github_repo_metadata_authoritative_fixture`
- four tests in `tests/test_hiqs_digest.py`
- three tests in `tests/test_queries_mirror_invariance.py`

Those files are untouched by GH-236. No same-environment baseline suite was run, so this receipt
does **not** classify the eight as pre-existing or prove their date sensitivity.

## Local-state preservation

The runtime checkout remained seven commits behind `origin/development`. The same five unrelated
paths were present before and after the virtualenv repair: modified
`src/rebalance/ingest/focus5_scan.py`, `utils/daily_work_synthesis.py`, and `uv.lock`; untracked
`.deploy-rollback.prev` and `.deploy-rollback.txt`. This proves the visible path set was preserved,
not byte identity. The virtual environment is ignored state and was rebuilt explicitly.

Six jobs currently show exit 75. Recent scheduler logs attribute exit 75 to the independent
memory-pressure guard; they are not EX_CONFIG and were not bypassed or repeatedly restarted.

## Hosted CI diagnostic

PR run `35644452332` found one GH-236-owned documentation failure: `manifest.json` remained at
0.88.3 after the package/project bump to 0.88.4. The exact `utils/frontdoor-check.sh` command failed
before the correction and passes afterward.

The same run's lint job reports eight Ruff errors, all in the untouched historical
`TESTS-RESULTS/2026-09-08+GH-199/scripts/mutation-check.py`. Development run `35266158410` at base
commit `c4fc5e2e75d259d5bf2c150f44e361900472c278` reports the same file and same eight-error count.
That is a public-repo baseline failure, not a GH-236 regression; it remains visible rather than being
folded into this runtime-diagnostics PR.

## Threats to validity

1. The full suite ran on predecessor `4a9228a`, before the final policy-membership and missing-policy
   guards. Those later changes were covered by focused tests and source review, not a second full run.
2. Raw console output from the full run was not retained. Counts came from the terminal result; the
   eight remaining test identities came from pytest's local `lastfailed` cache.
3. The local launchd and memory-pressure observations are a point-in-time device snapshot.
4. The runtime checkout is still behind public `development` and intentionally was not pulled over
   unrelated local work. This receipt proves local interpreter recovery, not deployment of GH-236.
5. Hosted lint remains red on an untouched historical evidence script that is also red on the exact
   base commit. This PR does not establish that any other base-branch CI failure is unrelated.
