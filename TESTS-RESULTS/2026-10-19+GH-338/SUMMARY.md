# GH-338 verification summary

| Check | Result |
|---|---|
| Plan QA, codex | **Approved** in round 2/3, attested against `28bfb7a` (`qa/gh338-plan-qa-relay.md`). Round 1 found a Blocker: the reporter files raw status only, so the row must be FAIL. |
| Focused suites | `tests/test_doctor_device_scope.py`, `test_doctor_exit_pins.py`, `test_doctor_pulse_severity.py` and `test_doctor.py`: **68 passed**, exit 0. The exit-pin AST enumeration is unchanged. Log: `tests-focused.log`. |
| Red control (tests) | With base `doctor.py` restored, the 4 new behavior tests **fail** (scoped >72h, the strict 72.0/72.1 boundary, the unscoped cap, the acknowledgement), and 7 pass, including the "unchanged" test. Exit 1, then the fix was re-applied. Log: `tests-red-control-base.log`. |
| Smoke, main path | Disposable `git clone --no-local` of the pulse clone, with one scoped laptop's `last_scan_utc` backdated 5 days. That row is **FAIL/ERROR**: "not collecting … 5d ago; silent >72h — reported from noels-mac-studio", and the hint holds a correctly shell-quoted `add-health-notice`. The doctor verdict is error. In the reporter probe (`_request` recorded, dry-run), it plans **1 filing** (`health: fleet:…`) with a label GET only and **0 mutating requests**. `smoke.log` |
| Smoke, adjacent 1: real fleet | Against the real pulse clone, no `fleet:` row is FAIL from the new rule (no device is past 72 h), and the reporter plans 0 filings: no false alarm. There was no base-code run on the real fleet, so this does not claim every row is byte-identical to base. |
| Smoke, adjacent 2: acknowledged | The exact command from the hint, run in the **task clone's** config, gives that row WARN/WARNING with disposition **notice**. The verdict drops from error to warning, and the reporter plans 0. The notice was removed afterwards. The runtime config was not touched (mtime is unchanged at 08:24). |
| Red control (smoke) | Base `doctor.py` (`3b31a67`) on the same disposable copy shows the backdated laptop as OK "not applicable", and the reporter plans 0. This is the bug. |
| Full suite (the CI pytest command with the `calendar,server,dev` extras) | **2798 passed**, 20 skipped, 10 xfailed (the GH-178 quarantine), 0 failed, exit 0, in 268 s, on implementation `f7729f1` (code identical to `305065f`). The one non-evidence worktree change noted at the end of the log is the docs-only `ROADMAP.md` wording fix, made during the run. Log: `tests-full-suite.log`. |

**Scope correction.** The quiet laptop originally cited is a **render** stall with a live collector (#333 shape), not a dead collector. That case is follow-up #340.

**Operator note.** The Mac Studio's runtime already has a health notice `"MacBook Pro"`. That substring also matches the 14" MacBook's row, so after this change the Studio shows a silent 14" as a notice and does not file it. Remove or narrow that notice if that is unintended.

Probe: `smoke-probe.py.txt`, run with `.venv/bin/python <file>` from the task clone; `SMOKE_SYNC_REPO` points it at the disposable copy.
