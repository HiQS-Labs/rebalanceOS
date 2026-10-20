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
| Recon re-scoped #338. Both proposed signals already exist; the gap is one scoping rule. Operator decisions recorded (error, 72h). | Codex plan QA, then implement. |

## Observed problem (2026-10-19, base `3b31a67`)

`rebalance doctor` on noels-mac-studio, run from the runtime root, reports:
```
fleet:Noel's MBP 16" M1 Pro | ok | not applicable on noels-mac-studio; owned by noels-mbp-16-m1-pro
```
That device's newest pulse on origin/main is **2026-10-07 11:00** (12 days old, `git log -1 origin/main -- live-pulse-noels-mbp-16-m1-pro.md` → 2ada78a7e). No Mac flags it.

The same blindness hid #314, where the Mac Studio was "alive but not publishing" for about 16 days (Sep 16 → Oct 2).

## Recon (what already exists, and the exact gap)

- **Per-device freshness already exists.**
  - `src/rebalance/ingest/pulse_health.py`: `read_collector_health()` reads every `devices/*.yaml` in the local pulse clone, which is the pulled state. `classify()` sets ALIVE / STALE (>3h) / ALERT (>24h) / DEGRADED / NO PUSHES / ALIVE_NOT_PUBLISHING.
  - `src/rebalance/doctor.py`: `_check_pulse_collectors()` (~:1885) emits one `fleet:<device_name>` row per device.
- **Stuck delivery already exists.** `classify()` sets ALIVE_NOT_PUBLISHING for fleet-mode devices when the delivered upstream status differs from local (queued), the render failed, or the delivered render is older than 10h (`MAX_SCHEDULED_RENDER_AGE_HOURS`). #338's second proposed row would duplicate it, so it is dropped.
- **The gap, part 1** (`doctor.py` ~:1908-1915): for a device in `_DEVICE_SCOPE_REGISTRY` (both MacBooks and the Mac Studio), `_other_device_check()` returns `OK "not applicable on <here>"` on every other Mac, whatever the device's age. `tests/test_doctor_device_scope.py::test_foreign_pulse_collector_is_informational_not_a_warning` pins this at 48h ALERT.
- **The gap, part 2** (~:1960-1966, GH-5 Phase F): an *unscoped* foreign device (the Mac Mini) that goes ALERT is capped at WARNING on other Macs. `scripts/health_issue_reporter.py:739` files only on `error` by default (SCHEDULER.md:22, "FAIL-only"), so a foreign WARNING is never filed either.
- **Acknowledgement already exists for warnings.** `rebalance config add-health-notice <pattern>` (`cli/config_cmds.py:673`) demotes matching **warning**-severity checks to notices (`health.py:213-252`). Error severity is never demoted there.
- **Consumers of doctor's exit code:** the CLI (`cli/__init__.py:136-211`) and the hourly `health-check` reporter. Nothing in `scripts/*.sh`, `scripts/lib`, `.githooks` or `experimental/git-pulse` gates on it (`git grep`).
- **Exit-pin tests:** `tests/test_doctor_exit_pins.py:112` lists `_check_pulse_collectors` as the one dynamic-severity site, and `:121-131` pins ALERT/DEGRADED/NO PUSHES as its WARN+ERROR states. The change must reuse the function's single `Check(...)` constructor so these pins stay valid.

## Operator decisions (2026-10-19)

1. When another Mac has been silent past the bound, **report an error (auto-file)**. This reverses GH-5 Phase F's foreign cap for this one case only.
2. The bound is **72 hours**. It tolerates a laptop closed over a weekend and would have caught the MBP16 on Oct 10 and #314 on about day 3.

## Sanity check / solution fit

- **Outcome sought:** a Mac that stops collecting reaches the operator within about 3 days, without anyone running a check by hand.
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
2. In `_check_pulse_collectors`, per device:
   - `foreign = health.device_id != current_device_id`
   - `long_silent = foreign and health.age_hours is not None and health.age_hours > _FOREIGN_SILENCE_HOURS`
   - `acknowledged = _matches_notice(name, get_health_notice_patterns())`, reusing the existing `health.py` helper and config reader
3. The `_other_device_check` short-circuit runs only when `not long_silent`. Inside 72h, a scoped foreign device keeps its exact current "not applicable" row.
4. The GH-5 Phase F cap (foreign ERROR → WARNING) is skipped when `long_silent and not acknowledged`. When acknowledged, the cap applies, and the reconciler then demotes the warning to a notice through the existing pattern. That is the operator's acknowledge path, with no new config.
5. When `long_silent`:
   - the detail gains `; silent >72h — reported from <current_device_id>`
   - the hint names the repair skill and the acknowledgement command: `run git-pulse-sync-repair on <device_id>, or acknowledge with: rebalance config add-health-notice '<name>'`
   - all of this goes through the existing single `Check(...)` constructor
6. A NO PUSHES foreign device (`age_hours is None`) is unchanged; it cannot be measured.

**Behavior table** (viewed from another Mac):

| Device / state | Today | After |
|---|---|---|
| scoped, ≤72h (any state) | OK "not applicable" | unchanged |
| scoped, >72h | OK "not applicable" | **WARN, severity ERROR**: auto-filed, and that Mac's doctor exit is FAIL |
| scoped, >72h, acknowledged | OK "not applicable" | WARN, severity WARNING → a notice (muted) |
| unscoped, ALERT ≤72h | WARN, capped at WARNING | unchanged |
| unscoped, >72h | WARN, capped at WARNING | **WARN, severity ERROR** |
| own device (any) | unchanged | unchanged |
| foreign NO PUSHES | unchanged | unchanged |

**Tests**, extending the existing `tests/test_doctor_device_scope.py`; this repo keeps pytest suites:
- scoped foreign at 80h → severity ERROR, detail contains "silent >72h"
- scoped foreign at 48h → still OK "not applicable"; the existing test stays as written
- unscoped foreign at 80h → ERROR, not capped
- scoped foreign at 80h with a matching notice pattern → WARNING
- own device at 80h → unchanged from today's local behavior
- foreign NO PUSHES → unchanged
- `tests/test_doctor_exit_pins.py` passes unchanged. That is the falsifier for "one constructor, no new literal ERROR site".

**Verification:**
- Focused suites: `tests/test_doctor_device_scope.py`, `tests/test_doctor_exit_pins.py`, `tests/test_doctor_pulse_severity.py`, `tests/test_doctor.py`. The full gate follows the repo's pre-push and CI.
- **Smoke, main path:**
  - run `.venv/bin/rebalance doctor --json` from the task clone on noels-mac-studio, reading the real pulse clone (read-only)
  - expect `fleet:Noel's MBP 16" M1 Pro` with severity error and the "silent >72h" detail, and verdict FAIL
  - then run `python scripts/health_issue_reporter.py --dry-run` and expect it to plan one "health: fleet:…" issue with no API call
- **Smoke, adjacent path:**
  - add a health notice for that row in the **task clone's** `temp/rbos.config`; never the runtime's
  - expect a notice disposition and no FAIL from this row
  - the reporter dry-run plans nothing for it
- **Red control:** the same smoke on base `3b31a67` shows "not applicable", and the reporter plans nothing.
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
