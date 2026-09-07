---
gh_issue: 194
source: https://github.com/HiQS-Labs/rebalanceOS/issues/194
title: "GH-194 — daily: machine CPU-health scanner (scan_runaway_cpu.py)"
status: "Active (2-WORKING — 2026-09-06). Implementation in flight on feat/daily-cpu-health-monitor."
created: 2026-09-06
updated: 2026-09-06
owner: noel
doc_type: bugfix
rating: "pri/sev/appeal/effort 70/60/50/70 · calc 250"
effort: 2
complexity: 2
risk: 1
phases: 1
ratings_provisional: false
goal: >
  A runaway process ran 2d21h at ~90-98% CPU on this machine and was found only by
  accident. Give the /daily cycle a deterministic, report-only runaway-CPU scanner so
  the next one is surfaced within two 15-minute cycles, with a falsifiable coaching
  trigger and the ready kill command.
non_goals:
  - Killing or signalling processes from the daily cycle (report-only, by operator decision and by the skill's read-only guardrail).
  - Doctor/health-check integration (doctor owns system health — GH-61's watchdog lane; /daily owns the operator work signal).
  - Generic process analytics (memory, network) — CPU pinned-core detection only, the observed failure mode.
---

# GH-194 — Daily machine CPU-health scanner

## Status

| What was just completed | What's next |
|---|---|
| Recon + intake 2026-09-06: incident evidence in #194; `scan_unclosed_loops.py` pattern reviewed; no prior art (no psutil dep, no existing ps-scanning code); ROADMAP queue row parked (rated 70/60/50/70); capture promoted to 2-WORKING. | Implement `scan_runaway_cpu.py` + tests + SKILL.md edits on `feat/daily-cpu-health-monitor`; pytest + pdda green; PR to `development` (closes #194). |

## Problem and evidence

2026-09-03 → 2026-09-06: an XYZ-forge ATE test snippet ran 2d21h at ~90–98% CPU
(~67.6 CPU-hours) on this machine, silently blocking its test chain, found only by a
chance process-table inspection. Rebalance operates this device's daily telemetry and
caught nothing. Measured duty cycles during the same sweep: `pulse_server` 0.1% over
4½ days; the four `mcp_server` processes ~0% — legitimate long-lived processes are
decisively separable from a pinned core.

## Design (extends the existing scanner pattern)

**Subsystem extended:** the `/daily` skill's deterministic scanner family —
`.agents/skills/daily/scripts/scan_unclosed_loops.py` (argparse `--json` /
`--summary-line`, deterministic one-line summary consumed by the SKILL.md template,
state under gitignored `temp/`). No new pipeline; the scanner is one more script in
that directory invoked by Step 3, exactly like its sibling.

**New:** `.agents/skills/daily/scripts/scan_runaway_cpu.py`

- Snapshot `ps -eo pid,ppid,%cpu,etime,time,lstart,command` once per cycle; parse
  `[[dd-]hh:]mm:ss` durations for both `etime` and `time`.
- Duty cycle = CPU time ÷ elapsed. Flag when **all** hold:
  `%CPU > 50` and `duty > 0.5` and `elapsed > 2h` and (same `(pid, lstart)` in the
  previous cycle's snapshot with growing CPU time **or** `elapsed > 24h`).
- Service exemptions (substring match, before eligibility): `rebalance.mcp_server`,
  `pulse_server.py`, `pet server`, `Code Helper`, `mem-watch`, `backupd`,
  `mds_stores`, `kernel_task`, `WindowServer`.
- State: `temp/daily-log/cpu-watch.json` — the previous cycle's eligible-process map
  is what makes the persistence signal possible; malformed/missing state degrades to
  "first sighting" (24h rule still applies).
- **Report-only.** Default `--summary-line` matches the sibling's shape:
  `- **Machine CPU Health**: clean` or the flagged form with pid, command, %CPU,
  elapsed, duty, cycles, and the ready `kill` command. `--json` carries the full
  payload. Exit code 0 either way (a finding is signal, not a scanner failure).
- State path default mirrors the sibling's operator-machine convention (the dev
  checkout), overridable via `--state-path` for tests and foreign clones.

**SKILL.md edits (3):** Step 3 gains the scanner invocation bullet; Step 4 gains one
falsifiable coaching rule — *Runaway Compute Alert*, trigger `≥ 2 consecutive cycles
flagging the same PID, or any candidate ≥ 24h`, citation
`[Trigger: PID <n> runaway for N cycles, duty <d>%]`; Step 5 template gains the
`**Machine CPU Health**` line.

## Acceptance (from #194, verified by tests)

- The 2026-09-06 incident profile (90.7% CPU, 2d20:57:35 elapsed, duty 0.98) is
  flagged; the summary line carries the kill command.
- `pulse_server` / `mcp_server` profiles (days elapsed, ~0 duty) are never flagged.
- A 100%-CPU 10-minute build is never flagged (elapsed gate).
- Service exemptions hold at pathological CPU levels.
- Persistence logic: second sighting with growing CPU flags with `cycles: 2`; no
  CPU growth and elapsed < 24h does not flag; malformed state tolerated.
- `pytest tests/` green; `utils/pdda/pdda.sh run` zero errors attributable to this
  change (development carries 5 pre-existing hardcoded-path errors in PROJECT docs —
  not touched here, none added).

## Implementation order

1. Write the scanner (pure functions: duration parsing, eligibility, persistence,
   exemptions; thin `ps`/state I/O shell) + `tests/test_scan_runaway_cpu.py`
   (importlib-loaded, deterministic fixtures — incident, servers, build, growth,
   24h-rule, malformed state, summary format).
2. SKILL.md three edits.
3. Version bump 0.84.1 → 0.85.0 (MINOR: new feature) in `pyproject.toml` +
   `src/rebalance/__init__.py`; CHANGELOG entry per the no-Unreleased contract.
4. Verify: `pytest tests/`; `utils/pdda/pdda.sh run`; LLM doc review
   (`pdda.sh doc-ready`, `PDDA_LLM_BIN=codex`) on the plan; push; PR to `development`
   (closes #194). Post-merge follow-up (not this PR): sync the second copy of the
   skill at `~/.agents/skills/daily/` from the merged tree.

## Risks / rollback

- False positives: the only true-positive class is a genuine multi-hour compute job,
  which the operator wants surfaced; the nudge reports and never acts. Exemption list
  is one constant — extendable without touching logic.
- The scanner only runs when a daily cycle runs (it is a skill, not a daemon) — the
  machine-wide gap while no cycle fires is accepted; the source-side watchdog is
  XYZ-forge#478's lane.
- Rollback: revert the branch; the script has no callers outside SKILL.md prose and
  writes only a gitignored state file.

## Rating rationale

`rated 70/60/50/70` — sev 60: an observability gap whose realized consequence was 3
days of silently blocked work on another repo and a pinned core; no data loss.
pri 70: the incident is fresh and the operator directed the work now, but nothing
current is blocked. appeal 50: neutral. effort 70: one script + tests + three SKILL.md
edits against an existing pattern.
