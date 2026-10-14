---
Goal: Final QA for GH-325 implementation (fleet enrollment, doctor rows, self-repair on upgrade)
Date: 2026-10-13
NEXT: Reviewer
STATUS: Open
---

# Context

Review the committed implementation on this branch against its approved plan before a PR is opened.
Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/325 (also closes #246).

**Operational envelope:** one operator's four personal Macs; a local Python CLI plus a bash
collector; local config files. Grade against the approved plan and stated requirements with
commensurate complexity. Do not ask for multi-tenant, locking or recovery machinery. This repo
permits new tests.

Read in full:
- Plan (approved after 3 Codex rounds): `PROJECT/2-WORKING/GH-325-FLEET-ENROLL-SELF-REPAIR.md`
- Plan QA thread: `TESTS-RESULTS/2026-10-13+GH-325/QA/gh325-plan-codex.md`
- Evidence: `TESTS-RESULTS/2026-10-13+GH-325/SUMMARY.md` and the red-control `.py`/`.jsonl` files

The diff is `git diff 0589b44..HEAD`. Code: `src/rebalance/lib/git_ops.py`,
`src/rebalance/ingest/config.py`, `src/rebalance/doctor.py`, `src/rebalance/cli/config_cmds.py`,
`tests/test_fleet_enroll.py`. Docs/script: `UPGRADE.md`, `SOP.md`, `SLEUTH_SYNC.md`,
`scripts/setup_sleuth_file_source.sh`, `CHANGELOG.md`; version 0.99.0.

Requirement → acceptance map:
1. Clone folder agnostic per Mac → `--print-clone` (0/2/3) used by UPGRADE step 3, SLEUTH_SYNC and the setup script.
2. Rollout + retirement → SOP "Four-Mac rollout" and "Retire legacy shared pages".
3. Enroll helper + doctor warns when not enrolled → `fleet-enroll`, `set-pulse`, `_check_pulse_fleet`.
4. `pulse_filename` not silently ignored → `pulse fleet filename` WARN; `fleet-enroll` removes it.
5. `$HOME` rule documented → resolver accepts `$HOME`/`~`, SOP "Clone path rule".
6. Durable self-repair on upgrade → UPGRADE "Fleet self-repair" bounded procedure.

Questions:

1. Is each of the six requirements satisfied by the actual code and docs? Cite file:line.
2. Do the code paths match the approved plan (doctor table rows and hints, `--print-clone` exit
   semantics, validate-before-write, refusal on two clones, idempotent rerun, duplicate-safe
   writer)? Any deviation?
3. Did a duplicate subsystem or second writer slip in beyond the disclosed `set_collector_values`?
   (A third, pre-existing parser in `pulse_health.resolve_sync_repo_dir` was deliberately left
   alone and parked — judge whether that is acceptable.)
4. Do the tests and red controls substantiate the claims in SUMMARY.md? Is the red control a real
   falsifier through the public `run_doctor` path?
5. Behaviour change check: `fleet_settings()` now accepts `$HOME`/`${HOME}`. Any caller regression
   (`pulse.py`, `index_ops.py`, `sync_snapshot.py`, doctor `_local_device_id`)?
6. Is the UPGRADE self-repair procedure executable by an agent without guessing, and bounded?
7. Is the rating `65/55/50/55` still consistent with the delivered scope? Appeal stays 50.
8. Anything over-engineered to cut, or a bug a user would hit?

You may run narrow read-only probes (output under `.relay-scratch/` or `$TMPDIR`); do not run
pytest or test suites. Every [Blocker]/[Should] asking for a behaviour change must carry
`Observed input:`, `Affected scope:` and `Falsifier:` lines. Cite file:line.

Write your verdict below. Set STATUS to Approved if the implementation can ship as a PR (Nits
allowed); otherwise leave it Open with findings and hand back.

<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->
▶ TAKE YOUR TURN (codex)
<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->
