# GH-377 campaign: GH-178 quarantine expiry and fixture aging

Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/377 · Plan: [GH-377](../../PROJECT/2-WORKING/GH-377-AUTO-PROMOTE-FIXTURE-AGING.md) · Base `88a8972` · Fix `ae11876` (test-only)

| Acceptance | Result | Receipt |
|---|---|---|
| A1 red control → green | base: `10 failed`; fix: `10 passed` (PASSED, no XPASS) | [witnesses.txt](witnesses.txt) |
| A2 auto-promote decay witness | helper defaults −20d + sum dates −22/−21/−20 → exactly the 9 IDs fail; restored → `16 passed` | [witnesses.txt](witnesses.txt) |
| A3 project-inference decay witness | freeze removed → `1 failed`; freeze at 2030-01-01 → `'BetaReport' not found in ['Acme']`; restored → `1 passed` | [witnesses.txt](witnesses.txt) |
| A4 quarantine emptied | `KNOWN_FAILING_GH178 = set()`; `test_conftest_quarantine.py` `4 passed` | [witnesses.txt](witnesses.txt) |
| A5 full suite parity | base `10 failed, 2839 passed` (failures = the 10 GH-178 IDs exactly); fix `2849 passed, 0 failed` | [root-tests.txt](root-tests.txt) |
| A6 hosted `root-noembed` 3.12/3.13 | pending on PR head | PR checks |
| Smoke (main + adjacent) | main `23 passed`; adjacent: TZ=Pacific/Kiritimati and Pacific/Pago_Pago, and a second run, `19 passed` each | [smoke.txt](smoke.txt) |
| Static gates | ruff check/format, five PDDA ratchets, doc links, `pdda.sh run`: all exit 0. `mypy src/` not run (the only `src/` change is the version string) | [static-gates.txt](static-gates.txt) |

Disposable clone identity bracket: [identity.txt](identity.txt) (same HEAD and origin before and after, clean tree).
Plan QA: [qa/gh377-plan-codex.md](qa/gh377-plan-codex.md) (Codex, Approved R2, attested).

`rebalance doctor` was not run: the change touches test fixtures plus the version string and cannot affect the live runtime, DB or scheduler that doctor inspects.

## Threats to validity and deviations

- **Environment:** A1–A5 and smoke ran locally on macOS, Python 3.13.15, in one disposable clone with `PYTHONPATH=<clone>/src` over the primary checkout's virtualenv. Python 3.12 and Ubuntu are covered only by the hosted `root-noembed` lanes (A6, pending at the time of writing).
- **Not measured:** 21 tests skipped in both base and fix runs (Metal-only and optional-dependency paths). This campaign makes no claim about them. `mypy src/` was not run (the only `src/` change is the version string). `rebalance doctor` was not run (above).
- **Filtered output:** `witnesses.txt` keeps only the summary/PASSED/FAILED lines from each step plus one `--tb=line` assertion excerpt, not full pytest output. The script that produced it is retained, so a rerun reproduces the full output.
- **Clock coupling that remains:** auto-promote fixtures are relative to the real UTC date, not frozen (SQLite `date('now')` cannot be frozen from Python). They use −1 to −3 days inside a 14-day window, so a run crossing UTC midnight stays in the window. A2 shows the tests still detect a fixture outside the window.
- **Deviations from plan:** final QA R1 added the patch bump (0.107.1 + changelog) per AGENTS.md § Versioning. The plan had followed the #243 test-only precedent. The A4 probe was corrected once during the campaign: its first run imported the root `conftest.py`. The rerun asserts the import path. Both runs' A1–A3 results were identical.
