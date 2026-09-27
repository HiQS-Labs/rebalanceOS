# RELAY · GH289 CI Python Seam Implementation QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
-->

NEXT: Producer
STATUS: Approved
ROUND: 2 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: CommandCode, Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). Review the whole file, not just the diff (GH-268).
     Declare it: every review block must contain a literal `swept file: yes` or `swept file: no` line.
     Any `[Pass]` or "verified"/"confirmed" finding MUST carry a quoted span or a `file:line` citation.
     Do **not** edit the artifact; only append findings here.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh289-impl-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first**. End your turn by naming who acts next.

## Setup
- Target code under review:
  - `scripts/lib/scheduler_common.sh` (`PYTHON` seam and `rb_run_python_stdin` guard)
  - `tests/test_daily_sync_exit.py` (`ShellExecutionTests._run_shell_refresh`, `SchedulerInterpreterSeamTests`)
  - `pyproject.toml`, `src/rebalance/__init__.py`, `manifest.json`, `CHANGELOG.md` (version 0.96.1 bump)
  - `TESTS-RESULTS/2026-09-27+GH-289/SUMMARY.md`
- Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/289
- Approved Plan: `PROJECT/1-INBOX/GH-289-CI-PYTHON-SEAM.md`
- Reviewer: codex · Producer: antigravity-gemini
- Started: 2026-09-27
- Definition of Done & QA Criteria:
  1. Scheduler Seam & Guard:
     - `PYTHON="${RB_PYTHON:-$REBALANCE_DIR/.venv/bin/python}"` at `scripts/lib/scheduler_common.sh:28`.
     - Invocation guard scoped strictly to `rb_run_python_stdin` before temporary allocation, returning exit code 127 and emitting diagnostic on stderr.
     - Best-effort lifecycle hooks (`rb_job_mark_started`, `_rb_job_exit`) remain untouched with `|| true`.
  2. Test Harness:
     - `ShellExecutionTests._run_shell_refresh` exports `RB_PYTHON="{sys.executable}"` before sourcing `scheduler_common.sh`.
     - Durable tests in `SchedulerInterpreterSeamTests` assert:
       - Default resolution when unset (`env -u RB_PYTHON`).
       - Default resolution when empty (`RB_PYTHON=""`).
       - Custom override resolution.
       - Direct `rb_run_python_stdin` failure on missing binary (exit 127 + stderr diagnostic).
       - Direct `rb_run_python_stdin` failure on non-executable binary (exit 127 + stderr diagnostic).
       - `rb_refresh` failure on non-executable binary with diagnostic captured in assigned `LOG_FILE`.
  3. Hygiene & Verification:
     - 100% pass on `tests/test_daily_sync_exit.py`, `tests/test_scheduler_policy.py`, `tests/test_script_inventory_ratchet.py`, `tests/test_stack_script.py` (96 tests).
     - Clean `ruff check`, `ruff format --check`, `utils/pdda/check_script_inventory.py --check`, and `bash -n`.
     - Version bumped to 0.96.1 across all 4 files with clean CHANGELOG entry.

## Ground rules
1. This file is the single source of truth.
2. Take a turn only if `NEXT` names your role.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. The Reviewer never edits the target codebase or artifact; only appends findings here.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Implementation Submission — antigravity-gemini · Round 1 · 2026-09-27

- Implemented `PYTHON="${RB_PYTHON:-$REBALANCE_DIR/.venv/bin/python}"` in `scripts/lib/scheduler_common.sh:28`.
- Added invocation-time guard in `rb_run_python_stdin` before `mktemp` allocation:
  ```bash
  if [ ! -x "$PYTHON" ]; then
      echo "[$(date '+%Y-%m-%d %H:%M:%S')] interpreter unavailable or not executable: $PYTHON" >&2
      return 127
  fi
  ```
- Lifecycle telemetry functions (`rb_job_mark_started`, `_rb_job_exit`) left untouched with `|| true` to guarantee zero disruptions to exit handling and no-venv policy tests.
- Updated `tests/test_daily_sync_exit.py`:
  - `ShellExecutionTests._run_shell_refresh` exports `RB_PYTHON="{sys.executable}"` before sourcing `scheduler_common.sh`.
  - Added 6 durable unit tests in `SchedulerInterpreterSeamTests` covering unset, empty, override, missing, non-executable (`chmod 0644`), and `rb_refresh` log diagnostic capture.
- Bumped version to `0.96.1` across `pyproject.toml`, `src/rebalance/__init__.py`, `manifest.json`, and added entry to `CHANGELOG.md`.
- Documented full campaign under `TESTS-RESULTS/2026-09-27+GH-289/SUMMARY.md`.
- All 96 tests pass in a clone lacking `.venv`; ruff, formatting, bash syntax, and script inventory ratchet are clean.

Next: **Reviewer** (codex) r1 — evaluate implementation vs Definition of Done.

### Review — codex · Round 1 · 2026-09-27

VERDICT: FAIL

Basis: The implementation matches the planned interpreter seam and guard by source inspection, but one explicit acceptance case is not exercised by its named test. This is a test-fixture correction, not a request to redesign the runtime.

swept file: no

Scope: Read the complete scheduler runtime, daily-sync test module, package metadata/version files, campaign summary, and approved plan; reviewed the current changelog entry, not its entire historical backlog. No source, tests, gates, or git commands were executed, per the operator's reviewer containment instruction. The reported 96 passing tests and hygiene checks remain producer-reported evidence, not independently reproduced results.

- [Should] **S1 — exercise the required non-executable file through `rb_refresh`.** `tests/test_daily_sync_exit.py:382` names `test_rb_refresh_non_executable_logs_diagnostic`, but line 383 supplies `/nonexistent/python/binary`. This covers missing-path logging, not the existing non-executable binary required by this relay's DoD §2. Create a separate temporary interpreter file, explicitly chmod it to `0o644`, point `RB_PYTHON` to it, and retain the exit-127 and `LOG_FILE` diagnostic assertions. Update `TESTS-RESULTS/2026-09-27+GH-289/SUMMARY.md` to describe the actual fixture and refresh the affected test result. The direct non-executable test at line 367 already supplies a suitable pattern.
- [Nit] **N1 — document the override beside the default.** `scripts/lib/scheduler_common.sh:14` still says “the project virtualenv python (never system python)”, whereas line 28 now accepts `RB_PYTHON`. Describe it as the explicit `RB_PYTHON` executable override with the repository virtualenv as the unset/empty default; this avoids misleading future callers.
- [Pass] **Runtime placement and error contract, by inspection.** `scripts/lib/scheduler_common.sh:28` uses `${RB_PYTHON:-$REBALANCE_DIR/.venv/bin/python}`; lines 110–117 place the stderr diagnostic and `return 127` before `mktemp`. Lifecycle calls at lines 44 and 51–55 retain `|| true`. No additional runtime fix requested.
- [Pass] **Harness injection and remaining seam cases, by inspection.** `tests/test_daily_sync_exit.py:268` exports the running test interpreter before sourcing at line 269. Lines 316–380 cover unset, empty, explicit override, direct missing-path failure, and direct `0o644` failure with diagnostic assertions. Retain these cases.
- [Pass] **Release metadata, by inspection.** `pyproject.toml:7`, `src/rebalance/__init__.py:31`, and `manifest.json:5` declare `0.96.1`; `CHANGELOG.md:13` has the dated release and lines 17–18 explain the change without file paths. No version correction requested.

Next: **Producer** (antigravity-gemini) — address S1, disposition N1, and submit the updated evidence for round 2. Harness owns the relay-file commit.

### R1 · Producer (antigravity-gemini)

Dispositions:
1. `[Should]` S1 — exercise the required non-executable file through `rb_refresh`:
   - **Disposition:** Implemented.
   - **Fix details:** Updated `tests/test_daily_sync_exit.py` to provide separate, dedicated test cases:
     - `test_rb_refresh_missing_interpreter_logs_diagnostic`: asserts missing binary path fails `rb_refresh` with exit code 127 and diagnostic in `LOG_FILE`.
     - `test_rb_refresh_non_executable_logs_diagnostic`: creates an explicit temporary interpreter file with `chmod 0o644`, asserts `rb_refresh` fails with exit code 127, and asserts diagnostic is captured in `LOG_FILE`.
     - Updated `TESTS-RESULTS/2026-09-27+GH-289/SUMMARY.md` documenting both tests and recording 24/24 passing tests in `tests/test_daily_sync_exit.py` (97 total).
2. `[Nit]` N1 — document the override beside the default:
   - **Disposition:** Implemented.
   - **Fix details:** Updated `scripts/lib/scheduler_common.sh:14` header comment to: `#   PYTHON        — explicit $RB_PYTHON override if set, else repo virtualenv python`.

Next: **Reviewer** (codex) r2 — re-evaluate implementation for final approval.

### Review — codex · Round 2 · 2026-09-27

VERDICT: PASS

Basis: S1 and N1 are resolved by source inspection. The interpreter seam, invocation guard, and revised fixtures match the approved plan. No remaining blocking findings. Execution evidence is producer-reported; this approval does not attest to a fresh test run or hosted CI success.

swept file: no

Scope: Read the complete scheduler runtime, daily-sync test module, package metadata/version files, campaign summary, and approved plan; reviewed the current changelog entry and adjacent releases, not the entire historical changelog. No source files, tests, gates, or git commands were executed, per the operator's reviewer containment instruction. Only this relay file was edited.

- [Pass] **S1 resolved — distinct non-executable fixture.** `tests/test_daily_sync_exit.py:400` creates separate interpreter and log files, explicitly applies `chmod(0o644)` at line 403, supplies that interpreter to `rb_refresh`, and asserts exit 127 and the path-specific log diagnostic at lines 415–417. The missing-path case remains separately covered at line 382. No further fixture change required.
- [Pass] **N1 resolved — override documented.** `scripts/lib/scheduler_common.sh:14` now describes the explicit `$RB_PYTHON` override and repository virtualenv fallback; line 28 retains the unset/empty fallback expansion. No further documentation change required for this scope.
- [Pass] **Runtime and harness contract retained, by inspection.** `scripts/lib/scheduler_common.sh:110` places the guard before allocation at line 116, returns 127, and writes the diagnostic to stderr. Lifecycle calls at lines 44 and 51–55 retain `|| true`; `rb_refresh` captures both streams at line 153 and returns the saved status at line 211. `tests/test_daily_sync_exit.py:268` injects `sys.executable` before sourcing, and lines 316–380 retain default, override, and direct invalid-interpreter cases. No runtime correction requested.
- [Pass] **Evidence and release consistency, by inspection.** `TESTS-RESULTS/2026-09-27+GH-289/SUMMARY.md:34` distinguishes missing and non-executable logging cases; lines 39–46 report 24 affected-file tests, 97 total tests, and clean hygiene checks. The extra missing-path case explains the increase from the DoD's original 96. Line 50 explicitly leaves hosted matrix verification pending. `pyproject.toml:7`, `src/rebalance/__init__.py:31`, `manifest.json:5`, and `CHANGELOG.md:13` agree on 0.96.1. No correction requested; harness retains responsibility for fresh gate execution.

Next: **Producer** (antigravity-gemini) / harness — implementation review approved; run the harness gate and continue the delivery workflow. Harness owns the relay-file commit.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
