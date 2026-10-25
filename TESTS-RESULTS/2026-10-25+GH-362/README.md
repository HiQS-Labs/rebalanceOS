# GH-362 verification (2026-10-25)

Issue https://github.com/HiQS-Labs/rebalanceOS/issues/362. Implementation commit `1bf7ea8`, plus a follow-up that aligns the mode of two test scripts. Upstream reference: HiQS-Labs/XYZ-CLIO `bacd26f`.

| Check | Result | Evidence |
|---|---|---|
| Byte + mode identity of the synced `utils/CLIO` files, `test/clio-store.py` and the CLIO tests/fixtures vs XYZ-CLIO `bacd26f` | identical (the two test-script modes are aligned in the follow-up) | `suites.txt` |
| Red control: base `6672892` vs upstream | differs | `suites.txt` |
| CLIO suites in a disposable full clone (`…-verify`) | capture, exporter, codex-tail, agy-tail pass; store: 1 known pre-existing date-dependent failure | `suites.txt` |
| Script-inventory ratchet | red before the baseline grow (`NEW script detected` for `utils/CLIO/clio-store.py`); green after, baseline diff is exactly +1 line | `red-controls.txt`, `gates.txt` |
| Ruff check/format | red before the exclude (5 findings, 2 files to reformat); green after | `red-controls.txt`, `gates.txt` |
| `utils/pdda/pdda.sh run` | exit 0, observe mode; 26 errors, the same count as base `6672892`, none naming GH-362 or changed files | `gates.txt` |
| `rg -F 'prompt-log-to-md.sh:500' src/` | no match (change 8) | – |
| Smoke: `clio-store.py` help/init/query/re-init/missing-DB, legacy exporter render + `--status` | all as expected; a read-only query never creates a store | `smoke.txt` |
