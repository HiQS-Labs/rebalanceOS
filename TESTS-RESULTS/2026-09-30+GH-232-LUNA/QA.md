# Verification receipt

Dataset preparation: three nonempty case packets, case hashes, GitHub observation timestamps and a redaction scan passed. The negative control rejected one mutated source ID and one removed required relationship. One synthetic probe and six real candidate calls completed; no output repair or retry. See the private Git Pulse Sync `RUNS.md`, `AUDIT.md` and `receipts/` for full raw event and claim audit.

Repository checks on the isolated trial checkout at base `4349ff5b`:

| Command | Current result |
|---|---|
| `PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_journey_replay.py tests/test_clio.py` (using the existing environment's interpreter) | 79 passed |
| `PYTHONPATH=src .venv/bin/python -m pytest -q tests/ HiQS/tests` | 2,804 passed, 21 skipped, 11 xfailed, 2 warnings, 143 subtests passed; exit 0 |
| Archived `test_saved_facts.py` included in the first focused command | Collection error: imports deleted `utils/CLIO/journey_replay.py` after the #249 relocation. This historical test was not claimed as passing. The current runtime test imports `rebalance.ingest.clio_journey` and passed. No runtime edit was made to hide the stale import. |
| `PYTHONPATH=src .venv/bin/python -m rebalance doctor` | Exit 1; existing unrelated health findings include four orphaned GitHub vectors and scheduler jobs bound to another checkout. Trial changed neither the database nor scheduled jobs. |

Historical September receipts are not counted as current tests. The full suite excludes deferred 3-Eyes per repository instructions.
