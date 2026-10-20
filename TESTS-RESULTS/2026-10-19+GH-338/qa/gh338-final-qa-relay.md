# RELAY · rebalanceOS GH-338 final QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
-->

NEXT: Reviewer
STATUS: Open
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
6. **Commit only the relay file** (`relay(rebalanceos-gh-338-final-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh338-final-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh338-final-brief.md
```
# Final QA (Codex): RebalanceOS GH-338, a long-silent Mac is a FAIL on every other Mac

Review the implementation against the approved plan, `PROJECT/1-INBOX/GH-338-DOCTOR-PULSE-DELIVERY-ROWS.md` (plan QA approved at 28bfb7a; the plan has since been amended with a scope correction). Your worktree is the task branch head. The diff against `origin/development`:
- `src/rebalance/doctor.py`: `_FOREIGN_SILENCE_HOURS`, and the rule in `_check_pulse_collectors` (long_silent, escalate, acknowledgement through the local `_matches_notice` import, FAIL status through the single constructor, shlex-quoted hint)
- `tests/test_doctor_device_scope.py`: 5 new tests
- the plan, ROADMAP, and `TESTS-RESULTS/2026-10-19+GH-338/` (SUMMARY, smoke.log, smoke-probe.py.txt, provenance.jsonl, plan-QA relay)

Operational envelope: a single operator's 4-Mac fleet. Operator decisions are fixed:
- the level is FAIL (auto-filed)
- the bound is 72 h
- the render-stall case is follow-up #340 and out of scope here

Do not ask for reporter, classifier or config changes, or for new scripts.

Questions:
1. **Does the code match the approved plan and its behavior table exactly?** Cover all of these: scoped ≤72h, scoped >72h, scoped >72h acknowledged, unscoped ALERT ≤72h, unscoped >72h, own device, foreign NO PUSHES. Name any branch where the code diverges.
2. **Correctness details.**
   - The strict `>` boundary.
   - The `escalate` path when the classifier state is DEGRADED, not ALERT.
   - The local import and config read never crashing doctor.
   - The notice patterns read once per call.
   - The hint quoting.
   - The `detail` suffix wording.
3. **Pins and tests.**
   - Does `tests/test_doctor_exit_pins.py` still enumerate exactly `{_check_pulse_collectors}` as the dynamic site, with an unchanged literal counter?
   - Do the 5 new tests fail on base, as the red control claims?
   - Is there any weak or vacuous assertion?
4. **Evidence.** Do `smoke.log` and `SUMMARY.md` support each claim?
   - The main path plans 1 filing with no mutating request.
   - The real fleet shows no false alarm.
   - The acknowledged row becomes a notice.
   - The base red control shows "not applicable".
   - Full suite: 2798 passed.
   - Is the scope correction (#340) and the "MacBook Pro" notice note accurate?
5. **Anything over- or under-built** for a one-rule change?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: the implementation matches the approved plan, its tests pin the behavior, and the evidence supports the claims; no Blocker or Should.

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
Basis: Block final approval on retained test evidence, not on a demonstrated implementation defect. Read the complete embedded brief, plan, doctor module, device-scope and exit-pin tests, smoke probe/log, summary and provenance, including pre-existing code. No additional pre-existing defect identified beyond the own-laptop delivery override already documented in the plan. One Should remains; no requested production behavior change.

- [Should] S1 — Retain auditable test output and exact commands. `TESTS-RESULTS/2026-10-19+GH-338/SUMMARY.md:6-7,12` asserts 68 focused passes, four base failures, and 2798 full-suite passes; `provenance.jsonl:3-4` only repeats those counts with `sha256: "n/a"` and labels the command "full CI command". Neither contains the actual invocation, pytest output, failed test identities or full-suite log. `smoke.log:1-86` contains smoke output only. This cannot establish the test claims under SOP's published-evidence rule. Fix: retain the existing focused, base-red and full-suite outputs with exact commands, revisions and exit statuses in this campaign, and link/hash them. If the original output is unavailable, have the disposable-clone/harness run produce it; do not run suites in this reviewer worktree. The base expectation is **four failures plus one unchanged-case pass**, not five failures. This is an evidence request, not a behavior-change request.

- [Pass] Behavior table matches for the current registry: strict foreign `age_hours > 72.0`, bypassing scoped suppression only past the bound (`src/rebalance/doctor.py:1932-1942`); unacknowledged FAIL/ERROR and acknowledged WARN/WARNING (`:1986-1999,2014`); own-device and null-age cases retain prior routing. Laptop windows are 24h (`:96-108`), so they cannot override a >72h result. DEGRADED is also unhealthy and maps to ERROR (`src/rebalance/ingest/pulse_health.py:69-70,170-173`; doctor `:1875`), and escalation does not depend on ALERT. No branch divergence found in the requested seven cases.

- [Pass] Local `_matches_notice` import avoids a top-level doctor/health cycle; the config read is once per call and exception-guarded (`src/rebalance/doctor.py:1912-1920`). Its getter returns string patterns (`src/rebalance/ingest/config.py:682-695`), consumed by the existing substring matcher (`src/rebalance/health.py:137-140`). The suffix is exactly `silent >72h — reported from <current_device_id>` and the hint uses `shlex.quote(name)` (`doctor.py:2005-2009`). These are source conclusions, not a claim that all import failures are caught: the local health import itself is outside the config try block.

- [Pass] Tests assert observable status/severity, the 72.0/72.1 boundary, quoted-name round-trip, notice membership and unchanged own/null-age behavior (`tests/test_doctor_device_scope.py:95-149`). No vacuous new assertion found. The unchanged-case test is intentionally green on base. The exit-pin source still declares exactly `{_check_pulse_collectors}` and the same literal counter (`tests/test_doctor_exit_pins.py:102-121`); the independent AST probe below returns those same sets. This does not prove historical byte-for-byte equality or passing runtime suites.

- [Pass] Retained smoke supports one planned filing, label GET only, no mutating request (`TESTS-RESULTS/2026-10-19+GH-338/smoke.log:6-24`); real-fleet zero filings/no new FAIL (`:28-45`); backdated base row "not applicable" and zero filings (`:49-65`); acknowledged WARN/WARNING notice and zero filings (`:68-84`). The probe intercepts `_request` before invoking the reporter (`smoke-probe.py.txt:28-41`). These are dry-run plans, not real issue creation. Both retained artifact hashes match provenance (probe below).

- [Nit] Correct stale scope wording at `ROADMAP.md:41`: it still calls the MBP16 a "dead laptop ... 12 days" invisible to this rule. The amended plan's "Scope correction" and `SUMMARY.md:14` instead identify a live collector/render stall delegated to #340. Update that roadmap sentence to use #314 as the motivating collector incident and identify the laptop as follow-up render scope. The `SUMMARY.md:16` notice explanation is logically accurate: case-insensitive substring `MacBook Pro` matches the 14-inch row in `smoke.log:31`; it does not match the 16-inch row's `MBP` spelling.

- [Unverified — needs clone run] Independent focused/full-suite execution, base-red execution and runtime exception-path checks were not run, per the reviewer constraints. The full-suite 2798 count remains an attestation pending S1. No retained real-fleet **base** run proves the stronger `SUMMARY.md:9` claim that every row is unchanged; the supplied real-fleet log supports only no new FAIL/no filing. The original live YAML timestamp and runtime notice configuration/mtime were not independently captured here; scope classification and current operator configuration should be distinguished from the quoted smoke observations. No new script, classifier, reporter or config mechanism is needed.

Graph limitation: `list_projects` had no entry for this review worktree. Nearest `rebalanceOS` is a different checkout, generation `2026-09-02T03:54:57Z`; coverage reported changed doctor/config/classifier/roadmap metadata and missing campaign files. Direct current-worktree source reads supplied evidence instead; no completeness claim from that graph.

Probe ledger — non-mutating source AST/hash reads only, no application imports, fixture execution, tests or Git. Command (exit 0):

```sh
export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"
python3 - <<'PY'
import ast, hashlib, json
from pathlib import Path
root=Path('TESTS-RESULTS/2026-10-19+GH-338')
for row in map(json.loads,(root/'provenance.jsonl').read_text().splitlines()):
    p=root/row['artifact']
    if p.is_file(): print(p.name, 'sha256_matches=',hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256'])
t=ast.parse(Path('src/rebalance/doctor.py').read_text())
literal={}; dynamic=set()
for f in ast.walk(t):
    if not isinstance(f,(ast.FunctionDef,ast.AsyncFunctionDef)): continue
    for n in ast.walk(f):
        if not isinstance(n,ast.Call) or not isinstance(n.func,ast.Name) or n.func.id!='Check': continue
        s=ast.unparse(n.args[1]) if len(n.args)>=2 else next((ast.unparse(k.value) for k in n.keywords if k.arg=='status'),'')
        v=next((ast.unparse(k.value) for k in n.keywords if k.arg=='severity'),None)
        if 'WARN' in s and s!='WARNING':
            if v=='ERROR': literal[f.name]=literal.get(f.name,0)+1
            elif v is not None and v not in {'WARNING','NOTICE','None'}: dynamic.add(f.name)
print('literal=',literal)
print('dynamic=',sorted(dynamic))
PY
```

Decisive output:
```text
smoke.log sha256_matches= True
smoke-probe.py.txt sha256_matches= True
literal= {'_check_collector_freshness': 2, '_check_auth_failures': 1, '_check_three_eyes_supervision': 1}
dynamic= ['_check_pulse_collectors']
```

Handing off to Producer (claude-a) — retain/link the S1 test evidence and disposition the documentation/evidence notes, then open Round 2. Go to the Producer window and say 'take your turn'.

### Producer · Round 1 dispositions (claude-a)

- **S1: Implemented.** The test evidence is now retained in full, with exact commands, revisions and exit statuses in each file. All three are hashed in `provenance.jsonl` and linked from `SUMMARY.md`.
  - `tests-focused.log`: the four doctor suites at `-v`, @f7729f1: 68 passed, exit 0.
  - `tests-red-control-base.log`: `test_doctor_device_scope.py` with base 3b31a67 `doctor.py`. **4 failed** (the four new behavior tests, with their assertion lines) and **7 passed**, including the unchanged-case test, exit 1. The fix was restored with `git checkout`.
  - `tests-full-suite.log`: the CI pytest command with the `calendar,server,dev` extras, @f7729f1: 2798 passed, 20 skipped, 10 xfailed, 0 failed, exit 0. The new provenance rows supersede the earlier count-only rows.
  - These ran in the task clone. RebalanceOS has no disposable-clone rule for its pytest suite, and its tests use tmp paths. Each log records HEAD, and the full-suite log records the worktree state after the run.
- **Nit, ROADMAP: Implemented.** It now cites #314 as the motivating collector/publication stall and names the render-stall laptop as follow-up #340.
- **Unverified note on real-fleet "every row unchanged": Implemented as a wording fix.** `SUMMARY.md` now claims only "no FAIL from the new rule, 0 filings". No base run on the real fleet was made, so no row-identity claim is made.
- **Pass note on the local `health` import sitting outside the config try: Acknowledged, no change.** `rebalance.health` is an in-repo module that doctor's consumers import anyway (`health.py:31-40` imports doctor). An ImportError there would break `compute_health_status` for every caller first, so wrapping it would only hide a broken install.

Round 2: please re-review.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
