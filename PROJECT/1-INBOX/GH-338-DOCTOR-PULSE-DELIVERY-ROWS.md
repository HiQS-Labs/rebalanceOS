---
gh_issue: 338
source: https://github.com/HiQS-Labs/rebalanceOS/issues/338
title: "doctor: a device silent for 72h is an error on every other Mac (fleet pulse freshness)"
status: "Captured — plan in QA on feat/rebalanceOS-gh338-doctor-pulse-delivery-rows-2026-10-19"
created: 2026-10-19
updated: 2026-10-19
owner: noel
doc_type: bugfix
goal: >
  A Mac whose pulse collector has been silent for more than 72 hours becomes a doctor error on
  every other Mac. The existing hourly health-check job then files it automatically. Today a
  device-scoped Mac is shown as "not applicable" everywhere except on itself, so a dead laptop is
  invisible to the fleet.
effort: 1
complexity: 2
risk: 2
phases: 1
ratings_provisional: false
roadmap_exempt: false
---

# GH-338: surface a long-silent Mac on every other Mac

## Status

| What was just completed | What's next |
|---|---|
| Plan QA **Approved** in round 2 (`28bfb7a`). Implemented (`305065f`): 68 focused tests pass, and the 4 new behavior tests fail on base. Scope correction: the render-stall case moved to #340. | Smoke on a disposable pulse copy, then final Codex QA and the PR. |

## Observed problem (2026-10-19, base `3b31a67`)

`rebalance doctor` shows every device-scoped Mac as `not applicable on <here>` on every other Mac, whatever its age. An unscoped Mac's ALERT is capped at WARNING there. The hourly reporter files only raw status `error`, so a Mac whose collector stops is never filed from the rest of the fleet. #314 is the observed case: the Mac Studio was "alive but not publishing" for about 16 days (Sep 16 → Oct 2), and its published YAML aged on every other Mac without a filed issue.

**Scope correction (smoke, 2026-10-19).** The quiet laptop first cited here (newest rendered pulse Oct 7) is **not** a dead collector: its `devices/<id>.yaml` `last_scan_utc` is `2026-10-18T08:13:01Z`, about 44 h old. What stopped is its pulse **render**, the #333 shape. #338 does not cover a render stall while the collector runs. Per the operator's decision that is follow-up #340, not added scope here.

## Recon (what already exists, and the exact gap)

- **Per-device freshness already exists.**
  - `src/rebalance/ingest/pulse_health.py`: `read_collector_health()` reads every `devices/*.yaml` in the local pulse clone, which is the pulled state. `classify()` sets ALIVE / STALE (>3h) / ALERT (>24h) / DEGRADED / NO PUSHES / ALIVE_NOT_PUBLISHING.
  - `src/rebalance/doctor.py`: `_check_pulse_collectors()` (~:1885) emits one `fleet:<device_name>` row per device.
- **Stuck delivery already exists.** `classify()` sets ALIVE_NOT_PUBLISHING for fleet-mode devices when the delivered upstream status differs from local (queued), the render failed, or the delivered render is older than 10h (`MAX_SCHEDULED_RENDER_AGE_HOURS`). #338's second proposed row would duplicate it, so it is dropped.
- **The gap, part 1** (`doctor.py` ~:1908-1915): for a device in `_DEVICE_SCOPE_REGISTRY` (both MacBooks and the Mac Studio), `_other_device_check()` returns `OK "not applicable on <here>"` on every other Mac, whatever the device's age. `tests/test_doctor_device_scope.py::test_foreign_pulse_collector_is_informational_not_a_warning` pins this at 48h ALERT.
- **The gap, part 2** (~:1960-1966, GH-5 Phase F): an *unscoped* foreign device (the Mac Mini) that goes ALERT is capped at WARNING on other Macs. `scripts/health_issue_reporter.py:739` files only on `error` by default (SCHEDULER.md:22, "FAIL-only"), so a foreign WARNING is never filed either.
- **Acknowledgement already exists for warnings.** `rebalance config add-health-notice <pattern>` (`cli/config_cmds.py:673`) demotes matching **warning**-severity checks to notices (`health.py:213-252`). Error severity is never demoted there.
- **Consumers** (corrected by Codex plan QA r1):
  - The CLI (`cli/__init__.py:158-159`) and the web dashboard (`scripts/pulse_web.py:3193,3223`) read the **reconciled severity**.
  - The hourly reporter reads the **raw row status** (`health_issue_reporter.py:519-526,739`). It does not read doctor's exit code.
  - The terminal dashboard renders index health only (`scripts/dashboard.py:1040,1212`).
  - `experimental/git-pulse/health-check.py:250-254,304-309` classifies independently.
  - Nothing in `scripts/*.sh`, `scripts/lib` or `.githooks` gates on doctor's exit.
- **Pre-existing limitation, not changed here:** on its own device inside the laptop window, a non-degraded `ALIVE_NOT_PUBLISHING` laptop is rewritten to healthy (`doctor.py:1928-1937`). So delivery problems on a laptop are not always visible in its own doctor. Stuck delivery is still covered fleet-wide by the >72h rule once the device's published YAML ages, as in #314.
- **Exit-pin tests:** `tests/test_doctor_exit_pins.py:112` lists `_check_pulse_collectors` as the one dynamic-severity site, and `:121-131` pins ALERT/DEGRADED/NO PUSHES as its WARN+ERROR states. The change must reuse the function's single `Check(...)` constructor so these pins stay valid.

## Operator decisions (2026-10-19)

1. When another Mac has been silent past the bound, **report an error (auto-file)**. This reverses GH-5 Phase F's foreign cap for this one case only.
2. The bound is **72 hours**. It tolerates a laptop closed over a weekend, and it would have caught #314 on about day 3.
3. A render stall while the collector runs is a follow-up (#340), not this PR.

## Sanity check / solution fit

- **Outcome sought:** a Mac whose collector stops, or whose published state stops reaching the fleet, reaches the operator within about 3 days, without anyone running a check by hand. Render stalls are #340.
- **Smallest bet:** one rule change inside `_check_pulse_collectors`, plus tests.
- **Alternatives rejected:**
  - a new doctor row: it would duplicate the existing `fleet:` rows
  - a standalone monitor script: rejected in #339
  - a reporter `--warn` flag: it would file every warning on every Mac
  - Grok's out-of-repo monitor only: no in-repo record, and it depends on one agent
- **Rollback:** revert one commit. The registry, classifier and reporter are untouched.

## Plan (one PR)

**Scope**, `src/rebalance/doctor.py` only:
1. Add the constant `_FOREIGN_SILENCE_HOURS = 72.0` next to `_DEVICE_SCOPE_REGISTRY`, with a comment citing #338 and the operator decision.
2. In `_check_pulse_collectors`, read the notice patterns once per call: `get_health_notice_patterns()`, plus `_matches_notice` imported **locally** inside the function (`health.py:31-40` imports doctor, so a top-level import would create a cycle). Then, per device:
   - `foreign = health.device_id != current_device_id`
   - `long_silent = foreign and health.age_hours is not None and health.age_hours > _FOREIGN_SILENCE_HOURS`
   - `acknowledged = _matches_notice(name, patterns)`
3. The `_other_device_check` short-circuit runs only when `not long_silent`. Inside 72h, a scoped foreign device keeps its exact current "not applicable" row.
4. When `long_silent and not acknowledged`, the row's **status is `FAIL`** and its severity `ERROR`. The status must be FAIL because `scripts/health_issue_reporter.py:519-526` forwards only `c.status`, and `:739` files only raw status `error` (Codex plan QA r1 B1, proven by its probe: status warning + severity error filed nothing). The GH-5 Phase F cap is skipped for that case. When acknowledged, the row stays WARN with the cap at WARNING, and the reconciler demotes it to a notice through the existing pattern. That is the operator's acknowledge path, with no new config. The constructor's status argument becomes `OK if healthy else (FAIL if escalate else WARN)`, so it is still the single dynamic-WARN site the AST walker in `tests/test_doctor_exit_pins.py:55-85` enumerates.
5. When `long_silent`:
   - the detail gains `; silent >72h — reported from <current_device_id>`
   - the hint names the repair skill and the acknowledgement command, built with `shlex.quote(name)` (already imported at `doctor.py:20`): `run git-pulse-sync-repair on <device_id>, or acknowledge with: rebalance config add-health-notice <shlex-quoted name>`. The real row name contains both an apostrophe and a double quote (Codex plan QA r1 S1).
   - all of this goes through the existing single `Check(...)` constructor
6. A NO PUSHES foreign device (`age_hours is None`) is unchanged; it cannot be measured.

**Behavior table** (viewed from another Mac):

| Device / state | Today | After |
|---|---|---|
| scoped, ≤72h (any state) | OK "not applicable" | unchanged |
| scoped, >72h | OK "not applicable" | **FAIL, severity ERROR**: auto-filed by the reporter, and that Mac's doctor exit is FAIL |
| scoped, >72h, acknowledged | OK "not applicable" | WARN, severity WARNING → a notice (muted) |
| unscoped, ALERT ≤72h | WARN, capped at WARNING | unchanged |
| unscoped, >72h | WARN, capped at WARNING | **FAIL, severity ERROR**: auto-filed |
| own device (any) | unchanged | unchanged |
| foreign NO PUSHES | unchanged | unchanged |

**Tests**, extending the existing `tests/test_doctor_device_scope.py`; this repo keeps pytest suites:
- scoped foreign at 80h → status FAIL and severity ERROR, detail contains "silent >72h", and `shlex.split` of the hint's command recovers the exact row name, including for a name with `'` and `"`
- scoped foreign at exactly 72.0h → still "not applicable"; at 72.1h → FAIL (the contract is strict `>`)
- scoped foreign at 48h → still OK "not applicable"; the existing test stays as written
- unscoped foreign at 80h → FAIL/ERROR, not capped
- scoped foreign at 80h with a matching notice pattern → WARN/WARNING, and `compute_health_status` puts it in `notices`, not `problems`
- own device at 80h → unchanged from today's local behavior
- foreign NO PUSHES → unchanged
- `tests/test_doctor_exit_pins.py` passes unchanged. That is the falsifier for "one constructor, no new literal ERROR site".

**Verification:**
- Focused suites: `tests/test_doctor_device_scope.py`, `tests/test_doctor_exit_pins.py`, `tests/test_doctor_pulse_severity.py`, `tests/test_doctor.py`. The full gate follows the repo's pre-push and CI.
- **Smoke, main path:**
  - Run `TESTS-RESULTS/2026-10-19+GH-338/smoke-probe.py.txt` from the task clone against a **disposable `git clone --no-local` copy** of the pulse clone. In the copy, one scoped laptop's `devices/<id>.yaml` `last_scan_utc` is backdated to 5 days ago. No real device is past 72 h today; see the scope correction.
  - Expect that row as FAIL/ERROR with "silent >72h" and a quoted acknowledgement hint, and the doctor verdict FAIL.
- **Smoke, adjacent path 1 (real fleet, no false alarm):** the same probe against the real pulse clone. No `fleet:` row may become FAIL from the new rule, and every row must match base behavior.
  - then a reporter probe, run from the task clone so its transition and run-log writes land in the clone's `temp/`. The probe imports `scripts/health_issue_reporter.py` from the task clone and replaces its `_request` with a recorder that returns `{}`, feeds it `run_doctor_checks()`, and calls `_run_github_sync(..., dry_run=True, warn=False)`.
  - Expect the recorder to show only the label `GET`, with **no mutating request**, and the result to plan one "health: fleet:…" filing. A stock `--dry-run` is not zero-API: `ensure_label` does a GET (`:317-320`) and needs a token (`:952`), per Codex plan QA r1 S2.
- **Smoke, adjacent path 2 (acknowledged):**
  - add a health notice for that row in the **task clone's** `temp/rbos.config`, using the exact command from the row's hint; never the runtime's config
  - expect a notice disposition and no FAIL from this row
  - the reporter probe plans nothing for it
- **Red control:** the same smoke on base `3b31a67` shows "not applicable", and the reporter probe plans nothing.
- Record the commands, output and provenance under `TESTS-RESULTS/2026-10-19+GH-338/`.

**Non-goals:**
- changing `pulse_health.classify` thresholds
- the scheduler-row scoping (`_other_device_check` for launchd jobs at ~:833 stays as is)
- reporter changes
- new config keys
- a new row for stuck delivery (ALIVE_NOT_PUBLISHING already covers it)
- per-device bounds

## Risks

- **Every awake Mac files or comments on the same issue.** The reporter dedups by row name, and later sightings add a "Recurrence detected · Device: …" comment, as #333 shows. Accepted.
- **Red doctor exit on healthy Macs while one Mac is off for more than 3 days.** This is the operator's choice. Mitigation: acknowledge with `add-health-notice`, which is named in the hint.
- **Scan age, not delivery age, drives the 72h bound.** On other Macs the device YAML arrives only through pushes, so a device that collects but cannot publish (as in #314) also ages there. That is intended.

## Ratings

`rated 65/55/50/80` (2026-10-19)
- **pri 65:** recurring, with one device invisible right now
- **sev 55:** fleet blindness for days; no data loss, the queued output is retained locally
- **appeal 50:** neutral
- **effort 80:** one function and its tests

Recurrence (issues plus live state):
- last 14 days (Oct 5–19): 1 ongoing incident, the MBP16, silent since Oct 7
- preceding 14 days (Sep 21–Oct 4): 1 incident, #314, a 16-day stall
- the trend is steady at about one per two weeks, but each lasts days because it is invisible

#333 is a different class (local scheduler unloaded); it was filed by the existing scheduler row the same day.
