# GH-364 verification (2026-10-25)

Issue https://github.com/HiQS-Labs/rebalanceOS/issues/364. Commits: rename `9ba7283`, installer `b1f21ec`.

| Check | Result | Evidence |
|---|---|---|
| `test/clio-runtime.sh` (new; 8 cases: refusal outside the collection, fresh install with no ZCode side effects, converged rerun, repair of a deleted link, stale writer and upgrade, adoption with backup, receipt-scoped uninstall, drift-safe uninstall) | PASS under macOS `/bin/bash` 3.2 in a disposable full clone | `suites.txt` |
| Existing CLIO suites after the rename | capture, exporter, codex-tail, agy-tail pass; `clio-store.py` has 1 known date-dependent failure (also fails upstream and on base) | `suites.txt` |
| Red control: the installer stops backing up replaced files | suite fails: `hand-made file was not backed up` | `suites.txt` |
| Red control: uninstall ignores drift | suite fails: `uninstall with a drifted hook: expected exit 1, got 0` | `suites.txt` |
| Repo gates | ruff check/format clean; script-inventory baseline is the rename plus `clio-runtime.sh`; banned-import and SQLite gateway ratchets clean; consumer-catalog, gateway-ratchet and GitHub-fixture tests pass | commit gates; hosted CI on the PR |
| Smoke on this Mac's real HOME, read-only, from a temp collection copy | `status` exit 1, listing the hand-installed hooks as `foreign`, `log-prompt.sh`, registrations and tailer jobs `ok`, the exporter `present (not managed)`; the `install` preview names the five files it would back up; a rerun preview and the `uninstall` preview (no receipt) are no-ops; the live HOME fingerprint (hooks, plists, settings, ZCode config, launchd list) is unchanged | `smoke.txt` |

The smoke run shows the real adoption plan for this Mac: the installed writer predates the current INSTALL.md heredoc, and the four helpers are regular-file copies, so all five would be backed up and replaced by links or the regenerated writer. Nothing was applied here; the per-device rollout follows #52 after merge and HQ intake.

**Final QA R1 fix.** Codex found that registration checks matched a substring: a foreign `/foreign/hooks/log-prompt.sh` command counted as the managed registration, so install skipped adding it and `status` said `ok`. Claude and ZCode registrations now match the exact managed command with jq, and ZCode uninstall removes only that exact command. New suite case 9 covers look-alike Claude and ZCode commands. Red control: the previous installer fails case 9 (`look-alike Claude command counted as registered`); the fixed installer passes all 9 cases.
