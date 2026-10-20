# RELAY · rebalanceOS GH-338 plan QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
-->

NEXT: Producer
STATUS: Approved
ROUND: 2 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(rebalanceos-gh-338-plan-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh338-plan-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh338-plan-brief.md
```
# Plan QA (Codex): RebalanceOS GH-338, a long-silent Mac becomes an error on every other Mac

Review the plan `PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md` before implementation. Your worktree is HiQS-Labs/rebalanceOS on `feat/rebalanceOS-gh338-doctor-pulse-delivery-rows-2026-10-19` (the intake commit on top of development 3b31a67).

Read in full:
- the plan
- `src/rebalance/doctor.py`: `_DeviceScope`/`_DEVICE_SCOPE_REGISTRY` (~:83-112), `_other_device_check` (~:127), `_PULSE_STATE_TO_CHECK` and `_map_pulse_state` (~:1858-1882), `_check_pulse_collectors` (~:1885-1980)
- `src/rebalance/ingest/pulse_health.py` (`classify`, `read_collector_health`)
- `src/rebalance/health.py` (`_matches_notice` ~:137, `compute_health_status` ~:213)
- `scripts/health_issue_reporter.py` (filing threshold ~:739, dedup by row name)
- `tests/test_doctor_device_scope.py`, `tests/test_doctor_exit_pins.py`, `tests/test_doctor_pulse_severity.py`
- issue https://github.com/HiQS-Labs/rebalanceOS/issues/338, including the re-scope comment

Operational envelope:
- RebalanceOS is a single operator's 4-Mac fleet.
- The change is one rule in one doctor function, plus tests in an existing test file.
- Do not ask for new scripts (GH-241), new config keys, reporter changes or classifier changes.
- The operator decisions are fixed: the level is error (auto-filed), and the bound is 72h.

Questions:
1. **Grounding.** Are the recon claims true at the cited lines?
   - a scoped foreign device always shows "not applicable"
   - an unscoped foreign ALERT is capped at WARNING
   - the reporter files only on error
   - health notices demote only warnings
   - stuck delivery is already covered by ALIVE_NOT_PUBLISHING, which justifies dropping the second proposed row
2. **Correctness of the rule.** Walk the behavior table against the actual code. Does the plan's order of operations (long_silent → bypass the short-circuit → bypass the Phase F cap unless acknowledged) produce exactly that table?
   - Check edge cases: the intermittent-window override (`scope.stale_after_hours`), DEGRADED foreign devices, ALIVE_NOT_PUBLISHING with an old scan, NO PUSHES, and the own device.
3. **Acknowledgement.** Is reusing `get_health_notice_patterns()` and `_matches_notice` at row construction sound? It keeps the foreign row at WARNING so the reconciler demotes it to a notice. Does it import cleanly from `doctor.py` with no cycle? Is there a simpler existing hook?
4. **Pins and blast radius.** Will reusing the single `Check(...)` constructor keep `test_doctor_exit_pins.py` green as written? Who else consumes `fleet:` row severity or doctor's exit code that the plan has not named (dashboard, pulse_web, experimental/git-pulse/health-check.py)?
5. **Verification.** Do the planned tests and smoke (main path, notice-acknowledged adjacent path, and a red control on base) prove the change and detect the old behavior? Is the reporter `--dry-run` usable as described?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: the plan is grounded, produces exactly its behavior table, and is sufficient and minimal for #338 under the operator's decisions; no Blocker or Should.

Reviewer block: plain lines; `VERDICT: PASS` or `VERDICT: FAIL` and `Basis:` each at the start of a line, with no bold. On PASS set `STATUS: Approved`.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1

swept file: yes
VERDICT: FAIL
Basis: Read the entire embedded brief and referenced plan, including its existing recon, behavior table, tests, smoke and risks. The proposed WARN/error row fails the required automatic-filing outcome. Two additional concrete corrections are needed. Review only; no artifact/source edits, suite runs, executable fixtures or git commands.

- [Blocker] B1 — ERROR severity alone never reaches the reporter's filing threshold. The proposed constructor still emits `WARN` (`PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md:90-93`). `scripts/health_issue_reporter.py:519-526` copies only `c.status`, dropping severity; `:739-749` files only raw status `error`. It does not consume the CLI exit or reconciled verdict. Thus doctor can fail while the hourly reporter files nothing. Fix the plan within its existing doctor-only envelope: emit `FAIL` status as well as ERROR severity for the foreign, >72h, unacknowledged case through the same constructor; keep acknowledged rows WARN/WARNING. Update the behavior table and assertions to check status as well as severity, and exercise the reporter adapter/threshold in clone verification. No reporter change is needed.
  Observed input: `Check(name="fleet:offline-mac", status="warning", severity="error", detail="silent >72h")`, exactly the status/severity pair prescribed by the plan. The extracted current adapter plus filing loop returned `(filed, closed, skipped, triaged_skip) = (0, 0, 0, 0)`.
  Affected scope: Foreign rows with non-null scan age strictly greater than 72h and no matching acknowledgement; own-device, ≤72h and NO PUSHES contracts remain as specified.
  Falsifier: Through the existing reporter adapter and default filing loop, an unacknowledged 80h foreign row must plan one issue; its acknowledged counterpart and the base's scoped foreign row must plan none. If the current WARN/error pair already plans one, this finding is wrong.

- [Should] S1 — The planned acknowledgement command is not pasteable for the actual device name. `PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md:81` wraps `<name>` in single quotes, while `:35` names `fleet:Noel's MBP 16" M1 Pro`. The apostrophe terminates the shell quote. Specify `shlex.quote(name)` (already imported at `src/rebalance/doctor.py:20`) when constructing the hint, and use the resulting command in the adjacent smoke.
  Observed input: `rebalance config add-health-notice 'fleet:Noel's MBP 16" M1 Pro'`; Python's shell lexer reports `ValueError: No closing quotation`.
  Affected scope: Generated acknowledgement hints for row names containing shell quoting characters, including the real row under investigation.
  Falsifier: Shell-tokenizing the generated command must yield exactly `['rebalance', 'config', 'add-health-notice', name]`, preserving the full row name as one argument.

- [Should] S2 — Correct the verification contract instead of promising a zero-API, read-only reporter smoke. The plan's `:111` says `--dry-run` makes no API call, but `scripts/health_issue_reporter.py:727` invokes `ensure_label`, whose `:317-320` performs a GET even in dry-run. `:952` also requires a token. Dry-run writes health transitions (`:936-942`) and the local run log (`:974`, `:185-187`). Amend the smoke to permit/document the label GET and required credentials, use an explicitly isolated clone DB/config, and distinguish no GitHub mutations from no API calls. Alternatively stub that external seam in the clone probe; do not expand production scope to repair the reporter.
  Observed input: Existing `_run_github_sync(..., args.dry_run=True, args.warn=False, ...)` requested `GET /repos/example/repo/labels/rebalance-health` before considering the row; the extracted probe intercepted it, making no real API request.
  Affected scope: The main, acknowledged and red-control reporter smoke procedures, not production reporter behavior.
  Falsifier: A clone run with an intercepted HTTP boundary records the label GET but no mutating requests; all transition/log writes stay in isolated clone state. A genuinely zero-request stock dry-run would disprove the API finding.

- [Pass] Grounding and rule ordering otherwise fit the present fleet. Scoped foreign rows short-circuit at `src/rebalance/doctor.py:1913-1916`; the unscoped foreign ERROR cap is `:1964-1969`. Current laptop windows are 24h (`:96-108`), so they cannot override a >72h row. DEGRADED retains ERROR via `:1867`; an old scan becomes ALERT before delivery classification (`src/rebalance/ingest/pulse_health.py:170-182`); NO PUSHES has null age (`:165-167`); own-device rows do not satisfy `foreign`. Reuse the existing row and classifier; a second delivery row is unnecessary for this scope.

- [Pass] Acknowledgement can reuse the existing substring matcher and config reader (`src/rebalance/health.py:137-140`, `src/rebalance/ingest/config.py:682-696`). WARN/WARNING is eligible for notice demotion; ERROR is not (`src/rebalance/health.py:239-252`). Import `_matches_notice` locally inside `_check_pulse_collectors`: `health.py:31-40` imports doctor, so a new top-level reverse import would create a cycle. Read notice patterns once per invocation rather than per device. No simpler existing row-construction acknowledgement hook appears in the reviewed function (`doctor.py:1885-1983`).

- [Pass] Keeping a single dynamic status/severity constructor leaves the relevant AST pins structurally applicable: `tests/test_doctor_exit_pins.py:67-82,112-131` enumerate WARN-capable constructors and the unchanged state table, not runtime foreign policy. The CLI consumes reconciled severity (`src/rebalance/cli/__init__.py:158-159`), and the web dashboard does too (`scripts/pulse_web.py:3193,3223`). The terminal dashboard renders index health (`scripts/dashboard.py:1040,1212`); the experimental fleet checker independently classifies canonical collector facts and derives its own exit (`experimental/git-pulse/health-check.py:250-254,304-309`). Add these distinctions to the plan's consumer summary; the reporter is a raw-status consumer, not a doctor-exit consumer.

- [Nit] Tighten the existing planned foreign tests with exactly 72h versus just over 72h and an acknowledged reconciler assertion, alongside B1's status assertion. The contract is strict `>` (`PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md:75`), whereas only 48h/80h are listed (`:98-101`).

- [Nit] Pre-existing delivery limitation in the reviewed function: a non-degraded owning laptop at 1h with `ALIVE_NOT_PUBLISHING` is rewritten to healthy ALIVE by `src/rebalance/doctor.py:1928-1937`. Preserve the explicit own-device-unchanged requirement here, but qualify the claim that existing delivery classification is always visible in doctor. This does not invalidate dropping the second row for the narrow >72h change. B1 also exposes a pre-existing raw-status/severity disagreement in the reporter; no other pre-existing defect was identified in the bounded paths reviewed.

- [Unverified — needs clone run] Focused/full suites, unchanged exit pins at runtime, real fleet smoke, notice smoke and base red control were not run, as required by this reviewer sandbox. The live Oct 7 timestamp and historical #314 duration were not remeasured. `gh issue view 338 --repo HiQS-Labs/rebalanceOS --comments` exited 0 and returned the re-scope decision: "a foreign device silent for more than 72 h becomes an error on every other Mac"; a later body query failed with `error connecting to api.github.com`. Graph evidence was provisional: nearest available project `rebalanceOS` is a different checkout, generation `2026-09-02T03:54:57Z`; coverage flagged changed doctor/classifier/config and excluded scripts. The trace tool was denied by the approval policy. Current-worktree direct source reads and bounded searches supplied the cited evidence instead; no graph completeness claim.

Probe ledger (non-mutating AST extraction of three existing functions; no application module imports, real GitHub calls or reporter execution). Command, exit 0:

```sh
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"
mkdir -p "$TMPDIR"
python3 - <<'PY'
import ast, builtins, types
from pathlib import Path
p = Path("scripts/health_issue_reporter.py")
tree = ast.parse(p.read_text())
names = {"run_doctor_checks", "_run_github_sync", "ensure_label"}
nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
calls = []
row = types.SimpleNamespace(name="fleet:offline-mac", status="warning", severity="error", detail="silent >72h", hint="repair")
fake_doctor = types.SimpleNamespace(run_doctor=lambda: types.SimpleNamespace(checks=[row]))
def importer(name, *args, **kwargs):
    if name == "rebalance.doctor":
        return fake_doctor
    return builtins.__import__(name, *args, **kwargs)
env = {"__builtins__": dict(vars(builtins), __import__=importer), "_request": lambda *a: calls.append(a) or {}, "LABEL": "rebalance-health", "ISSUE_TITLE_PREFIX": "health:"}
module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
exec(compile(ast.fix_missing_locations(module), str(p), "exec"), env)
checks = env["run_doctor_checks"]()
args = types.SimpleNamespace(repo="example/repo", dry_run=True, warn=False, llm_triage=False, close=False)
result = env["_run_github_sync"]("fake-token", args, checks, types.SimpleNamespace(), "fixed-time")
print("input doctor row:", vars(row))
print("reporter row:", checks[0])
print("(filed, closed, skipped, triaged_skip):", result)
print("dry-run request calls:", calls)
PY
```

Decisive output:
```text
input doctor row: {'name': 'fleet:offline-mac', 'status': 'warning', 'severity': 'error', 'detail': 'silent >72h', 'hint': 'repair'}
reporter row: {'name': 'fleet:offline-mac', 'status': 'warning', 'detail': 'silent >72h', 'hint': 'repair', 'source': 'rebalance-doctor'}
(filed, closed, skipped, triaged_skip): (0, 0, 0, 0)
dry-run request calls: [('GET', '/repos/example/repo/labels/rebalance-health', 'fake-token')]
```

Quoting probe command, exit 0 (same scratch/bytecode environment):
```sh
python3 - <<'PY'
import shlex
name = """fleet:Noel's MBP 16" M1 Pro"""
command = f"rebalance config add-health-notice '{name}'"
print("planned:", command)
try:
    print(shlex.split(command))
except ValueError as exc:
    print(type(exc).__name__ + ": " + str(exc))
print("quoted:", "rebalance config add-health-notice " + shlex.quote(name))
PY
```
Decisive output: `ValueError: No closing quotation`.

Root cause: foreign scope suppression and the cap hide stale devices, while the plan assumes the reporter uses severity; Fix site: existing doctor constructor plus plan verification; Why not upstream/downstream: the classifier already supplies age/error states, and emitting raw FAIL for the new unacknowledged case satisfies the unchanged reporter contract.

Handing off to Producer (claude-a) — address B1, S1 and S2, disposition the remaining notes, and open Round 2; go to the Producer window and say 'take your turn'.

### Producer · Round 1 dispositions (claude-a)

- **B1: Implemented.** The long-silent, unacknowledged foreign row now has status `FAIL` with severity `ERROR`, built by the same single constructor: `OK if healthy else (FAIL if escalate else WARN)`.
  - That status text still contains `WARN`, so the AST walker at `tests/test_doctor_exit_pins.py:68-81` still lists `_check_pulse_collectors` as the one dynamic site, and the literal-ERROR counter is unchanged.
  - An acknowledged row stays WARN with the cap at WARNING.
  - The behavior table and the tests now assert status as well as severity.
  - The smoke now includes the reporter probe you described, with `_request` recorded.
- **S1: Implemented.** The hint's command uses `shlex.quote(name)`, and a test checks that `shlex.split` of the hint recovers the exact name, including `'` and `"`. The adjacent smoke uses the hint's own command.
- **S2: Implemented.** The stock `--dry-run` claim is gone. The smoke is a probe run from the task clone:
  - it imports the reporter from the clone, replaces `_request` with a recorder returning `{}`, feeds it real `run_doctor_checks()` and calls `_run_github_sync(dry_run=True, warn=False)`
  - it expects only the label GET, with no mutating request
  - its writes stay in the clone's `temp/`
  - there is no production reporter change
- **Pass (consumers, import, read once): Implemented.**
  - The consumer summary is corrected: the CLI and the web dashboard use reconciled severity, the reporter uses raw status, `dashboard.py` shows index health only, and the experimental checker classifies independently.
  - `_matches_notice` is imported locally inside the function.
  - The notice patterns are read once per call.
- **Nit, boundaries: Implemented.** Tests at 72.0h (still "not applicable") and 72.1h (FAIL), plus a `compute_health_status` assertion that the acknowledged row lands in `notices`.
- **Nit, pre-existing `ALIVE_NOT_PUBLISHING` rewrite on the owning laptop (`doctor.py:1928-1937`): Recorded, not changed.** It is out of scope and documented in the plan's recon as a qualified limitation.

Round 2: please re-review.

### Reviewer · Round 2

swept file: yes
VERDICT: PASS
Basis: Re-read the entire embedded brief, the complete revised plan and all prior dispositions; checked the bounded doctor/classifier/reconciler/reporter paths and existing test contracts against current-worktree source. B1, S1 and S2 are resolved at plan level. No remaining Blocker or Should. This approves the plan, not an implementation or deployment.

- [Pass] B1 resolved: the plan now explicitly emits FAIL/ERROR for an unacknowledged foreign age >72h and WARN/WARNING when acknowledged (PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md:81-88,96-108). That matches the adapter dropping severity and the default filing threshold (scripts/health_issue_reporter.py:519-526,739-749). The narrow adapter/threshold probe below plans one filing for error, none for warning or ok; it does not execute the proposed doctor change.
- [Pass] S1 resolved: the hint uses shlex.quote(name) and its planned test round-trips the exact row name (plan:87,104). The probe below returns True for the real apostrophe/double-quote name.
- [Pass] S2 resolved: the clone probe intercepts _request, permits the label GET and prohibits mutating requests (plan:118-124; scripts/health_issue_reporter.py:317-320,727-735,359-364). It calls the adapter/sync seam rather than reporter main, so main's transition logging, token resolution and log flush are outside this probe (reporter:936-952,974). For execution, honor the plan's clone-only configuration requirement explicitly; inherited REBALANCE_CONFIG must not point at runtime state.
- [Pass] The proposed ordering matches the behavior table for the current registry: laptop windows are 24h (src/rebalance/doctor.py:96-108), hence cannot make a >72h row healthy; DEGRADED maps to ERROR (:1867), and aged non-degraded scans become ALERT before delivery classification (src/rebalance/ingest/pulse_health.py:170-182). NO PUSHES has null age (:165-167); own devices fail the foreign predicate. The existing short-circuit and cap remain for the adjacent cases (doctor.py:1913-1916,1964-1969).
- [Pass] Local _matches_notice import avoids the existing health-to-doctor import cycle, and WARN/WARNING is precisely the notice-demotion contract (src/rebalance/health.py:31-40,137-140,239-252; plan:79,84). The single constructor's proposed nested conditional still contains WARN and keeps variable severity, matching the existing AST enumeration (tests/test_doctor_exit_pins.py:67-82,112-131). The new boundary and reconciler assertions plus base red control are specified (plan:104-125); their outcomes remain to be measured.
- [Pass] Full-plan sweep found no additional pre-existing defect in the bounded paths beyond the own-laptop delivery rewrite and raw-status/severity mismatch already recorded in Round 1. The revised recon records both the delivery limitation and consumer distinction (plan:50-57). Neither needs a classifier, reporter, registry or scheduler change for this fix.

- [Unverified — needs clone run] Focused/full suites, runtime exit pins, implementation behavior, fleet smoke, acknowledgement smoke and base red control were not run here. Live fleet timestamps and incident durations were not remeasured. The harness/disposable-clone gate owns those checks. The graph project is another checkout, generation 2026-09-02T03:54:57Z; its coverage reports changed doctor/classifier/config, an absent plan and excluded scripts. Graph lookup was provisional; current-worktree direct source reads supplied the material evidence. No graph completeness claim.

Probe ledger: narrow AST extraction of existing reporter functions only; no application imports, fixture execution, network request or persistent state write. file_issue and issue-body rendering are stubbed, so this measures adapter/threshold behavior, not HTTP serialization or real filing. Command (exit 0):

```sh
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"
mkdir -p "$TMPDIR"
python3 - <<'PROBE'
import ast, builtins, types, shlex
from pathlib import Path
p = Path("scripts/health_issue_reporter.py")
names = {"run_doctor_checks", "_run_github_sync", "ensure_label"}
nodes = [n for n in ast.parse(p.read_text()).body if isinstance(n, ast.FunctionDef) and n.name in names]
row = types.SimpleNamespace(name="fleet:Noel's MBP 16\" M1 Pro", status="error", severity="error", detail="silent >72h", hint="repair")
fake = types.SimpleNamespace(run_doctor=lambda: types.SimpleNamespace(checks=[row]))
def importer(name, *args, **kwargs):
    return fake if name == "rebalance.doctor" else builtins.__import__(name, *args, **kwargs)
calls, actions = [], []
env = {"__builtins__": dict(vars(builtins), __import__=importer), "_request": lambda *a: calls.append(a) or {}, "LABEL": "rebalance-health", "ISSUE_TITLE_PREFIX": "health:", "_issue_body": lambda *a: "", "file_issue": lambda *a: None}
module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
exec(compile(ast.fix_missing_locations(module), str(p), "exec"), env)
args = types.SimpleNamespace(repo="example/repo", dry_run=True, warn=False, llm_triage=False, close=False)
log = types.SimpleNamespace(add_action=lambda *a: actions.append(a))
for label, status, severity in [("unacknowledged", "error", "error"), ("acknowledged", "warning", "warning"), ("base scoped foreign", "ok", "notice")]:
    row.status, row.severity = status, severity
    calls.clear()
    actions.clear()
    checks = env["run_doctor_checks"]()
    result = env["_run_github_sync"]("fake-token", args, checks, log, "fixed-time")
    print(label, "=>", result, "actions:", actions, "requests:", calls)
command = "rebalance config add-health-notice " + shlex.quote(row.name)
print("quoted command round-trip:", shlex.split(command) == ["rebalance", "config", "add-health-notice", row.name])
PROBE
```

Decisive output:
```text
unacknowledged => (1, 0, 0, 0) actions: [('filed', 'fleet:Noel\'s MBP 16" M1 Pro', None)] requests: [('GET', '/repos/example/repo/labels/rebalance-health', 'fake-token')]
acknowledged => (0, 0, 0, 0) actions: [] requests: [('GET', '/repos/example/repo/labels/rebalance-health', 'fake-token')]
base scoped foreign => (0, 0, 0, 0) actions: [] requests: [('GET', '/repos/example/repo/labels/rebalance-health', 'fake-token')]
quoted command round-trip: True
```

Root cause: foreign scope suppression and severity capping hide long-silent devices; Fix site: the existing doctor row construction and plan verification; Why not upstream/downstream: the classifier already exposes scan age and error states, while FAIL status satisfies the unchanged reporter contract.

Relay closed (Approved), no further review turn needed. Producer (claude-a) may proceed with implementation and the disposable-clone verification gate.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
