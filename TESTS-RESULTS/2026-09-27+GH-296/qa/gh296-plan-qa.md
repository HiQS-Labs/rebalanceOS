# RELAY · GH-296 job_guard remediation plan QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-27.
-->

NEXT: none
STATUS: Approved
ROUND: 2 / 2

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **Verdict**
     (Approved | Changes requested | Blocked). **Review the whole file, not just the diff** (GH-268):
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
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh296-plan-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/gh296-remediation-plan.md** — the read-only path that
  `relay-drive.sh --artifact-file <scratch>/gh296-remediation-plan.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: agy   ·   Producer: claude-a
- Started: 2026-09-27
- Definition of Done: the plan is grounded (every `file:line` and behavioural claim matches the code at 4349ff5), fixes the root cause rather than one call site, covers BOTH guard layers, keeps the GH-172 defences (single-instance lock, per-job footprint ceiling, fail-closed on unreadable RAM/probes), and every acceptance criterion names how it fails. Nothing speculative or over-built.

### Operational envelope
Local, single-operator macOS scheduler (launchd jobs on 4 Macs, 24–64 GB RAM). Commensurate complexity: do NOT ask for enterprise fail-safes, new daemons, or distributed machinery. Measure-read-only probes are fine (`export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"`); do not run pytest or validate.sh.

### Read these (code at HEAD 4349ff5)
- `.relay-artifacts/gh296-remediation-plan.md` (the plan, the whole thing)
- `utils/job_guard.py` — esp. constants ~95-170, `swap_used_bytes` ~390, `MemoryCeiling` ~679-875 (`__init__`, `_compressor_trip`, `preflight`, `_check`), `guard` ~911, `run_guarded` ~974, `main` ~1144
- `src/rebalance/ingest/_job_guard.py` (whole file, 180 lines)
- `src/rebalance/ingest/embedder.py`, `src/rebalance/ingest/semantic_index.py` (where `@guarded_embedding` is applied)
- `src/rebalance/ingest/index_ops.py` (`classify_sync_outcome`, scope error handling)
- `scripts/lib/scheduler_common.sh` (`rb_refresh`)
- `src/rebalance/ingest/config.py` 204-229 (`_resolved_config_path`)
- `tests/test_job_guard_footprint.py` (compressor tests ~450-520), `tests/test_job_guard_wiring.py`, `tests/conftest.py`

### Questions (answer each by number, cite file:line)
1. **Root cause.** Is `SWAP_DISTRESS_BYTES` (absolute 1 GiB) in `_compressor_trip` really the reason a 24 GB / 2 GB-swap Mac refuses with ~1.2 GB residual swap? Is there any other path in preflight/_check that would still refuse under the plan's 1.1 inputs (24 GiB RAM, compressor 9.3 GiB, swap 1.2/2 GiB, available 6 GiB)? Note the available floor is max(12% RAM, 4 GiB) = 4 GiB.
2. **Swap rule.** Is `max(1 GiB, 0.75 × swap_total)` sound? macOS swap is dynamic (swap files grow on demand): does `vm.swapusage` total grow with use such that "used > 75% of total" is rarely/never true — i.e. does the rule silently become "never confirm via swap"? Is the swap-growth alternative in 1.3 better, and would the available-floor corroboration still cover real distress?
3. **Second guard.** Confirm the inner guard (`_job_guard.py`) goes through the same `MemoryCeiling`, so Phase 1 fixes both layers. Is Phase 2.2 (inner refusal → deferred / exit 75) correctly located — which function actually turns the exception into `sync_outcome: fatal` / exit 1? Is there a risk of reporting "deferred" when partial work already ran in another scope?
4. **Memory-off without lock-off (2.3).** Is adding a separate memory-only switch the minimal change, or can the existing `MemoryCeiling` be told to skip memory checks while `SingleInstanceLock` stays? Any caller that relies on `REBALANCE_JOB_GUARD=0` (tests/conftest.py) that 2.3 could break?
5. **Phase 3 resolver.** `utils/job_guard.py` must stay stdlib-only under system python3. Is reading the same `temp/rbos.config` (resolved by cwd in `config._resolved_config_path`) from job_guard safe, given #281 says launchd and interactive runs can resolve different files? Is passing the path via an env var from `run_guarded` to the child the simplest correct approach, and does it reach agent-spawned (non-launchd) embedding runs?
6. **Acceptance criteria.** Can any criterion pass vacuously (e.g. satisfied by an empty change or a log line)? Is the 1.1 red-first test actually red at 4349ff5 under the stated inputs?
7. **Scope / bloat.** Flag anything over-engineered (per-job overrides? doctor deferred counts?) or missing (e.g. the stale 14.32 GiB note, the stale 35% docstring, any other stale claim).

Grade every finding `[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`. Every `[Blocker]`/`[Should]` asking for a behaviour change must carry `Observed input:`, `Affected scope:`, `Falsifier:` lines.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer (agy) — Round 1

swept file: yes

Verdict: Changes requested

Pre-existing defects in examined files:
- `src/rebalance/doctor.py:1269, 1311`: Doctor already treats exit code 75 as `OK` (`running = "idle, skipped (75)"`). The belief in Plan 4.2 that doctor misrates 75 as an error is inaccurate; doctor failed because `classify_sync_outcome` returned exit 1 (`fatal`).
- `src/rebalance/ingest/_job_guard.py:136-138`: Docstring references non-existent `DEFAULT_MAX_RSS_FRACTION (35%)` (replaced by `DEFAULT_MAX_FOOTPRINT_FRACTION = 0.125` at `utils/job_guard.py:102`).
- `utils/job_guard.py:142`: Mentions 14.32 GiB Qwen peak from a bug fixed in 0.68.4.

---

#### Answers to Relay Questions

1. **Root cause.**
   - Confirmed: `SWAP_DISTRESS_BYTES = 1 * GIB` at `utils/job_guard.py:155` in `MemoryCeiling._compressor_trip` is the direct and sole reason for refusal under the 1.1 inputs.
   - Tracing `MemoryCeiling.preflight`:
     - Total RAM = 24 GiB (`total_memory_bytes()` readable).
     - `self.max_compressor` = 24 GiB × 0.25 = 6.0 GiB (`utils/job_guard.py:719`).
     - Compressor = 9.3 GiB > 6.0 GiB.
     - `swap_used_bytes()` = 1.2 GiB. Since 1.2 GiB > `SWAP_DISTRESS_BYTES` (1.0 GiB), `_compressor_trip` sets corroboration to `"swap in use 1.2 GB"` and trips.
     - If the swap corroboration did not trip, `_compressor_trip` logs the non-distress line and returns `None`.
     - In `preflight()`, `self.min_available` = `max(int(24 GiB * 0.12), 4 GiB)` = 4.0 GiB (`utils/job_guard.py:713`). Available memory is 6.0 GiB, which is >= 4.0 GiB, so `preflight()` passes cleanly without raising.
     - In `_check()`, `self.max_footprint` is 3.0 GiB (12.5% of 24 GiB). A healthy small job (peaking under 2 GiB) does not trip footprint or availability.

2. **Swap rule.**
   - `max(1 GiB, 0.75 × swap_total)` solves the immediate 14" laptop failure (1.2 GiB < 0.75 × 2.0 GiB = 1.5 GiB).
   - Dynamic swap caveat: on macOS, `dynamic_pager` allocates swap files on demand (typically in 1 GiB or 2 GiB increments). When `dynamic_pager` allocates a new swap file right as usage reaches ~75–80%, `swap_total` expands immediately, causing `swap_used / swap_total` to drop back down to ~40–50%. Thus, under active heavy thrashing, `swap_used > 0.75 × swap_total` may oscillate or lag.
   - However, the swap-growth alternative over poll intervals **cannot help `preflight()`**, because `preflight()` runs once before the process launches and has no poll history.
   - Real distress protection remains intact because the available-memory floor (`available < min_available`, 4 GiB at `utils/job_guard.py:770` and `utils/job_guard.py:816`) corroborates distress immediately when memory is actively exhausted. Thus, level-based scaling with available-floor fallback is sound for preflight.

3. **Second guard.**
   - Confirmed: `src/rebalance/ingest/_job_guard.py:163` invokes `mod.guard()`, which instantiates `MemoryCeiling` (`utils/job_guard.py:930`) and runs `ceiling.preflight()` (`utils/job_guard.py:953`). Phase 1 fixes both layers.
   - Function turning the exception into `sync_outcome: fatal` / exit 1:
     - In `src/rebalance/ingest/index_ops.py:1809-1811`, unhandled exceptions from `collector.refresh` are caught and appended to `errors`: `errors.append({"scope": s, "error": str(e)})`.
     - In `classify_sync_outcome()`, if no attempted scope succeeded, it returns `("fatal", 1)`.
     - In `scripts/lib/scheduler_common.sh:184, 197`, `classify_sync_outcome` exit code 1 causes `sys.exit(1)`.
   - **Multi-scope risk:** Yes! If a multi-scope job (such as default `rebalance refresh` or `daily-sync`) completes earlier scopes successfully (e.g. `vault` and `github` mutate the DB) and then `semantic` raises `MemoryCeilingExceeded` before work, classifying the entire run as exit 75 would trigger `log_job_skipped` in `scheduler_common.sh:53`, falsely erasing the fact that prior scopes performed and committed real work. Exit 75 must be restricted to runs where ALL attempted scopes were deferred (or the sole target scope deferred before work).

4. **Memory-off without lock-off (2.3).**
   - In `src/rebalance/ingest/_job_guard.py:140-142`, `REBALANCE_JOB_GUARD=0` completely bypasses `mod.guard()`, dropping the lock as well.
   - `tests/conftest.py:131-143` relies on `REBALANCE_JOB_GUARD=0` to ensure pytest test suites do not compete for the local machine's `rebalance-embed` `flock` or trigger preflight memory checks.
   - Therefore, `REBALANCE_JOB_GUARD=0` must remain test-only and untouched.
   - For 2.3, `MemoryCeiling` can simply be instructed to skip memory watchdog checks (or `guard` can skip starting `MemoryCeiling`), while keeping `SingleInstanceLock` active.

5. **Phase 3 resolver.**
   - **Flaw identified:** In Phase 3.2, passing the resolved config path via an env var from `run_guarded` to its child only works for launchd-wrapped jobs. It **does NOT reach agent-spawned or in-process embedding runs** (`embedder.py` / `semantic_index.py`), because those callers invoke Python directly and never execute `run_guarded`!
   - In addition, #281 notes that launchd and interactive runs can resolve different paths if cwd varies.
   - Resolution: `_job_guard.py` runs inside the Python environment that has `rebalance` and can resolve the path directly via `rebalance.ingest.config._resolved_config_path()`. In `utils/job_guard.py` (which runs under system python3 for launchd wrappers), it should resolve relative to its own known path (`Path(__file__).resolve().parents[1] / "temp" / "rbos.config"`) or accept an explicit `--config` / `REBALANCE_CONFIG` env var.

6. **Acceptance criteria.**
   - 1.1 red-first test: Confirmed red at 4349ff5. Under 24 GiB RAM, 9.3 GiB compressor, and 1.2 GiB swap used, `MemoryCeiling.preflight()` raises `MemoryCeilingExceeded` because 1.2 GiB > `SWAP_DISTRESS_BYTES` (1.0 GiB). A test asserting preflight succeeds and logs "not in distress" fails at HEAD.
   - Vacuous pass risk: Criterion 84 ("inner-guard memory refusal gives exit 75 / `deferred`") could pass vacuously or dangerously if implemented by returning exit 75 without checking whether other scopes already completed and committed work.
   - Criterion 86 ("Doctor prints the effective mode and thresholds...") lacks an explicit failure condition (*Fails if...*), unlike the other criteria.

7. **Scope / bloat.**
   - **Over-engineered:** Phase 3.1 & 3.3 per-job config overrides keyed by lock name with 5-tier precedence (CLI > env var > per-job config > device config > built-in default). On a single-operator Mac system, all jobs failed due to the exact same global swap threshold. A single device config flag (`job_guard.memory_guard: on|off`) is sufficient; per-job overrides violate Ponytail / YAGNI.
   - **Misconception:** Phase 4.2 ("Doctor stops rating a deferred 75 as a job error..."). As verified in `src/rebalance/doctor.py:1269, 1311`, doctor ALREADY treats exit 75 as `OK` (`running = "idle, skipped (75)"`). What broke `launchd:github-sync` was that `classify_sync_outcome` produced exit 1 (`fatal`). Doctor doesn't need to change its rating of 75; the fix belongs in `index_ops.py` / `classify_sync_outcome`.
   - **Stale notes confirmed:** `src/rebalance/ingest/_job_guard.py:136-138` (cites 35% RSS fraction) and `utils/job_guard.py:142` (cites 14.32 GiB Qwen peak).

---

#### Graded Findings

- [Pass] **Phase 1.1 Red test premise is verified at 4349ff5**
  - Citation: `utils/job_guard.py:155` (`SWAP_DISTRESS_BYTES = 1 * GIB`), `utils/job_guard.py:768-769`.
  - Quoted span:
    ```python
    if swap is not None and swap > SWAP_DISTRESS_BYTES:
        corroboration = f"swap in use {_fmt_gb(swap)}"
    ```
  - Under 24 GiB RAM, 9.3 GiB compressor, 1.2 GiB swap, 6.0 GiB available, `preflight()` raises `MemoryCeilingExceeded` on HEAD. The proposed test is genuinely red before Phase 1.

- [Pass] **Both guard layers share MemoryCeiling**
  - Citation: `src/rebalance/ingest/_job_guard.py:163` (`with mod.guard(...)`), `utils/job_guard.py:930, 953`.
  - Both inner embedding leaves (`embed_chunks` at `embedder.py:195` and `embed_pending` at `semantic_index.py:752`) delegate to `_job_guard.embedding_guard()`, which delegates to `job_guard.guard()` and `MemoryCeiling`. Phase 1 cleanly covers both.

- [Pass] **Stale docstring and comment citations are accurate**
  - Citation: `src/rebalance/ingest/_job_guard.py:136-138` (`"DEFAULT_MAX_RSS_FRACTION (35%)"`) and `utils/job_guard.py:142` (`"14.32 GiB"`). Both are verified stale against current code.

- [Blocker] **Phase 3.2 env var inheritance fails for agent-spawned runs**
  - Observed input: Agent-spawned embedding runs (e.g. MCP tools, interactive CLI, direct `rebalance refresh`) invoke Python in-process and never execute `utils/job_guard.py`'s `run_guarded`.
  - Affected scope: Plan Section 3.2 ("passed down via one env var set by run_guarded for its child").
  - Falsifier: In an agent-spawned embedding pass, `run_guarded` is never in the process tree, so the env var is never set, causing the child to fall back to defaults or fail to resolve the config.
  - Concrete fix: Clarify Phase 3.2 so that in-process calls (`_job_guard.py`) resolve config via `rebalance.ingest.config._resolved_config_path()`, while standalone `job_guard.py` resolves `temp/rbos.config` relative to its own script location (`Path(__file__).resolve().parents[1] / "temp" / "rbos.config"`) or via `REBALANCE_CONFIG`. Do not rely on `run_guarded` passing an env var to child processes.

- [Blocker] **Phase 2.2 / AC 84 must not exit 75 when prior scopes completed work**
  - Observed input: A multi-scope refresh (e.g. `rebalance refresh` or `daily-sync` with `scope=["vault", "semantic"]`) where `vault` succeeds and updates database tables, but `semantic` subsequently refuses in preflight.
  - Affected scope: Plan Section 2.2 and Acceptance Criteria line 84.
  - Falsifier: If `classify_sync_outcome` turns an inner guard refusal into exit 75 unconditionally, a job that executed and committed partial mutations will exit 75, causing `scripts/lib/scheduler_common.sh:53` to record `log_job_skipped` instead of `log_job_completed` / `log_job_degraded`, masking DB mutations from telemetry.
  - Concrete fix: Amend Phase 2.2 and AC 84 to specify: an inner refusal marks the *individual scope* as `deferred: True` (matching `index_ops.py:2124`); `classify_sync_outcome` exits 75 (`deferred`) ONLY if no other scope succeeded (i.e. all attempted scopes were skipped/deferred). If other scopes succeeded, the run is classified as `degraded` (exit 0) with the deferred scope reported in the payload.

- [Should] **Phase 4.2 misconception regarding doctor rating of exit 75**
  - Observed input: Plan 4.2 claims "Doctor stops rating a deferred 75 as a job error when the reason is a memory refusal. Today launchd:github-sync flipped ok→error on a refusal."
  - Affected scope: Plan Section 4.2 and Section 21.
  - Falsifier: `src/rebalance/doctor.py:1269` explicitly includes `"75"` in `is_ok_status = status_val in ("0", "75", "-")`, and line 1312 outputs `Check(f"launchd:{short}", OK, "idle, skipped (75)")`. Doctor already rates exit 75 as OK! `launchd:github-sync` flipped to FAIL because `classify_sync_outcome` returned exit 1 (`fatal`).
  - Concrete fix: Update Phase 4.2 to note that doctor already treats exit 75 as OK; the reason `github-sync` failed doctor was exit 1 from `classify_sync_outcome`. Phase 4.2 should focus on ensuring doctor surfaces structured deferred reasons rather than modifying an already-correct launchd exit-code classifier.

- [Should] **Prune Phase 3.1 & 3.3 per-job config overrides (YAGNI / Ponytail)**
  - Observed input: Plan 3.1 & 3.3 specify per-job overrides keyed by lock name with 5-tier precedence.
  - Affected scope: Plan Section 3.1 and 3.3.
  - Falsifier: The operational envelope specifies a single-operator Mac environment where all jobs failed for the exact same global swap threshold. Implementing per-job override dictionaries and 5-tier precedence inside stdlib-only `utils/job_guard.py` adds needless complexity without an operational requirement.
  - Concrete fix: Drop per-job overrides from Phase 3.1 and simplify 3.3 to: CLI flag > env var > device config (`job_guard.memory_guard: on|off`) > default.

- [Nit] **Add explicit failure condition to Acceptance Criterion 86**
  - Observed input: Line 86: `- [ ] Doctor prints the effective mode and thresholds and their source on each Mac.` does not define how it fails, unlike lines 82–85.
  - Affected scope: Acceptance criteria (line 86).
  - Concrete fix: Append failure definition, e.g.: `*Fails if doctor output omits the effective mode/thresholds or misattributes their configuration source.*`

---

handing off to claude-a — go to the other window and say 'take your turn'

### Producer (claude-a) — Round 1 dispositions → Round 2

Plan re-seeded at `.relay-artifacts/gh296-remediation-plan.md` and published as the #296 body. Producer spot-checks: `doctor.py:1269` (`is_ok_status = status_val in ("0", "75", "-")`), `index_ops.py:1809-1811` and `1924-1930` confirmed by direct read.

- **[Blocker] 3.2 env var misses agent-spawned runs → Implemented.** The resolver lives in `utils/job_guard.py` (stdlib). Path: `$REBALANCE_CONFIG`, else `Path(__file__).parents[1]/temp/rbos.config`. The inner guard loads the same module, so every caller (launchd, CLI, MCP, agent) resolves the same file. No `run_guarded` env passing.
- **[Blocker] 2.2 must not exit 75 when work completed → Implemented.** Deferral is recorded per scope. `("deferred", 75)` only when every attempted scope deferred; any success keeps the existing `("degraded", 0)`. Tests and the AC now state both cases.
- **[Should] 4.2 doctor misconception → Implemented.** 4.2 now records that doctor already rates 75 OK and that the flips were exit 1, fixed by 2.2.
- **[Should] prune per-job overrides → Implemented.** Per-job overrides removed. Precedence is CLI > env > device config > default.
- **[Nit] doctor AC failure condition → Implemented.** Now fails on an omitted mode or threshold, or a wrong source, against a fixture config.
- **Pre-existing stale notes** (`_job_guard.py:136-138`, `job_guard.py:142`): already covered by plan 2.4.
- **Q2, dynamic swap:** kept the level rule plus available-floor corroboration, per the reviewer's analysis. Swap growth stays an open question, since it can't serve preflight.

Round 2: please re-review the changed sections (2.2, 3.1–3.3, 4.2, acceptance criteria) and confirm or raise remaining findings. handing off to agy — take your turn.

### Reviewer (agy) — Round 2

swept file: yes

VERDICT: PASS

Basis: All Round 1 findings (Blockers on agent-spawned config resolution and multi-scope exit 75 telemetry masking; Shoulds on doctor rating misconception and per-job override bloat; Nit on acceptance criterion failure definitions) have been thoroughly and accurately implemented in `.relay-artifacts/gh296-remediation-plan.md`. The plan strictly satisfies the Definition of Done: every cited line and behavioral assertion matches the codebase at 4349ff5, the root cause is addressed across both guard layers while preserving GH-172 protections, and all acceptance criteria name explicit failure conditions.

Pre-existing defects in examined files:
- All previously identified pre-existing defects (`src/rebalance/ingest/_job_guard.py:136-138` stale 35% docstring, `utils/job_guard.py:142` stale 14.32 GiB comment, and `src/rebalance/doctor.py:1269, 1311` exit 75 handling) are now tracked and reconciled under Sections 2.4 and 4.2. No new or unaddressed pre-existing defects were found in the swept files.

---

#### Re-review of Changed Sections

- [Pass] **Phase 2.2 multi-scope deferral logic prevents telemetry masking**
  - Citation: Plan Section 2.2 lines 47–51 and AC line 90; `src/rebalance/ingest/index_ops.py:1925-1930` and `scripts/lib/scheduler_common.sh:52-53`.
  - Quoted span from plan:
    > "`classify_sync_outcome` returns `("deferred", 75)` **only when every attempted scope was deferred**. If any scope succeeded, the existing `("degraded", 0)` path stands, and the deferred scope is visible in the payload. Work that already happened is never reported as skipped (`scheduler_common.sh:53` `log_job_skipped`)."
  - Verification: Confirmed that requiring all attempted scopes to defer before returning exit 75 prevents completed mutations from being reported as skipped, while preserving exit 75 when a single target scope or all attempted scopes defer before work.

- [Pass] **Phase 3.2 stdlib config resolution unifies launchd and in-process callers**
  - Citation: Plan Section 3.2 lines 62–67; `src/rebalance/ingest/config.py:30` and `src/rebalance/ingest/_job_guard.py:144`.
  - Quoted span from plan:
    > "Path: `$REBALANCE_CONFIG` if set (the same variable `config.py:30` honours), else `Path(__file__).resolve().parents[1] / "temp" / "rbos.config"`, i.e. the checkout the guard itself lives in. Nothing depends on `run_guarded` passing state to a child, so agent-spawned, CLI and MCP embedding runs resolve the same file as launchd runs."
  - Verification: Because `_job_guard.py` imports `utils/job_guard.py` via `load_job_guard()`, placing the stdlib JSON resolver in `utils/job_guard.py` ensures both launchd wrappers and direct Python/agent invocations resolve the identical config file without requiring environment inheritance from `run_guarded`.

- [Pass] **Phase 3.1 & 3.3 pruned per-job overrides adhere to Ponytail / YAGNI**
  - Citation: Plan Section 3.1 lines 59–61 and Section 3.3 line 69; `utils/job_guard.py:155`.
  - Quoted span from plan:
    > "`job_guard.memory_guard: on | off` (default `on`), scoped to the memory checks only. **The lock and wall-clock timeout are always on.** ... Precedence: explicit CLI flag > env var > device config > built-in default."
  - Verification: Removing complex per-job dictionary lookups keeps `utils/job_guard.py` lightweight and maintainable under system python3 while solving the problem cleanly for all guarded jobs.

- [Pass] **Phase 4.2 correctly attributes past doctor failures to exit 1**
  - Citation: Plan Section 4.2 line 75; `src/rebalance/doctor.py:1269, 1311-1312`.
  - Quoted span from plan:
    > "No change needed to doctor's exit-code rating: it already treats 75 as OK (`doctor.py:1269`, `"idle, skipped (75)"` at 1311). The "ok→error" flips came from exit **1** (inner-guard `fatal`, or github-sync's strict-policy `degraded`), which Phase 2.2 addresses."
  - Verification: Confirmed against `doctor.py:1269` (`is_ok_status = status_val in ("0", "75", "-")`). Unnecessary modifications to doctor's status classifier are avoided.

- [Pass] **Acceptance criteria lines 88–92 specify concrete failure conditions**
  - Citation: Plan Section "Acceptance criteria" lines 88–92.
  - Quoted span from plan:
    > "*Fails if the new test passes before the fix (it tests nothing) or any existing refusal test is edited.*"
    > "*Fails if any layer still raises.*"
    > "*Fails if a sole-scope refusal still says fatal, or a run with completed work exits 75.*"
    > "*Fails if doctor omits the mode or any threshold, or names the wrong source (checked against a fixture config setting `memory_guard: off` and `swap_distress_gb: 1.5`).*"
  - Verification: Every acceptance criterion is non-vacuous, verifiable, and explicitly defines the failure boundary.

---

relay closed (Approved), no further turn needed.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
