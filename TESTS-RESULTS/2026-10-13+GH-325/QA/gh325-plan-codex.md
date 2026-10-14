---
Goal: Plan QA for GH-325 (fleet enrollment, doctor checks, self-repair on upgrade)
Date: 2026-10-13
NEXT: Reviewer
STATUS: Open
---

# Context

Review the plan in `PROJECT/1-INBOX/GH-325-FLEET-ENROLL-SELF-REPAIR.md` before any code is written.
Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/325 (also closes #246).

**Operational envelope:** a single operator's four personal Macs, each running a local Python CLI
(`rebalance`) and a bash collector (`experimental/git-pulse/collect.sh`). Config files are local and
owned by that operator. Grade against the stated requirements and commensurate complexity — do not
demand multi-tenant, distributed-locking or enterprise recovery machinery.

**Operator requirements (verbatim intent):**
1. The upgrade path must be agnostic to each Mac's pulse clone folder name. `UPGRADE.md:144-149`
   hardcodes `~/git-pulse-sync`; Mac Mini's clone is `~/Documents/GitHub/rebalance-git-pulse`.
2. A rollout plan for fleet mode across all four Macs and a retirement plan for old files.
3. An enroll helper, and doctor must warn when a Mac is not enrolled.
4. `pulse_filename` must not be silently ignored once fleet mode is on.
5. Document that `$HOME` paths are rejected in the pulse clone path.
6. Fixes must be durable and self-repair via AI orchestration on the next upgrade install
   (the agent running UPGRADE.md). Operator decision: drift is auto-repaired; enrolling a Mac that is
   not yet enrolled previews and asks first.

Read the plan in full, then these sources it cites:
- `UPGRADE.md` (lines 100-170), `SLEUTH_SYNC.md`, `SOP.md` § "GH-282 — fleet delivery deployment and lessons" (~line 317)
- `scripts/setup_sleuth_file_source.sh`
- `src/rebalance/lib/git_ops.py` (`fleet_settings`, `fleet_output_path`, lines 25-90, and ~505-520)
- `src/rebalance/ingest/config.py` (`get_pulse_config`, `set_pulse_config`, ~1323-1400)
- `src/rebalance/ingest/pulse.py` (~955-970, 1045-1100)
- `src/rebalance/doctor.py` (`_check_pulse` ~2155, `_check_pulse_collectors` ~1885, call sites ~2558-2567)
- `src/rebalance/cli/config_cmds.py` (`set-sleuth` ~482 as the CLI pattern)
- `experimental/git-pulse/install.sh` (`set_config_value` ~56) and `collect.sh` (fleet_mode ~20, 537-540, 735)
- `tests/test_doctor_pulse_severity.py`, `tests/test_pulse_health.py`

Questions:

1. Are the plan's factual claims about current behaviour correct? Check each cited file:line.
   In particular: does `fleet_settings()` reject `$` in `sync_repo_dir`, and does doctor today
   ever call it?
2. Is any of the six requirements missing or only partly covered? Is the UPGRADE.md self-repair
   step concrete enough for an agent to execute deterministically?
3. Does the plan extend existing code rather than build a parallel system? Judge specifically the
   new `set_collector_values()` writer next to `install.sh`'s `set_config_value` — is the disclosed
   second writer justified, or is there a simpler existing path?
4. Is the retirement scope right? The plan retires only root `live-pulse.md` and
   `live-pulse-<device>.md`, and keeps `pulse-<id>.md` / `devices/<id>.yaml` because the collector
   still writes them in fleet mode. Is that correct per `collect.sh`?
5. Are the doctor rows' severities sensible (WARN vs FAIL vs muted notice), and is the red control
   (new rows absent on the unmodified `_check_pulse`) a real falsifier?
6. Is `fleet-enroll --apply` safe when `sync_repo_dir` and `pulse_target_path` disagree, and
   idempotent on a re-run?
7. Is the rating `65/55/50/55` grounded in the evidence given? Appeal must stay 50 (no user value).
8. Flag anything over-engineered or that could be cut.

You may run narrow read-only probes (output under `.relay-scratch/` or `$TMPDIR`); do not run
pytest or test suites. Every [Blocker]/[Should] asking for a behaviour change must carry
`Observed input:`, `Affected scope:` and `Falsifier:` lines. Cite file:line.

Write your verdict below. Set STATUS to Approved if the plan can proceed as written (minor Nits
allowed); otherwise leave it Open with your findings and hand back.

<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->
▶ TAKE YOUR TURN (codex)
<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->
