---
title: "Recon: fleet enrollment review follow-up"
status: "Completed; retained as historical recon"
created: 2026-10-14
updated: 2026-10-15
owner: agent
doc_type: audit
goal: "Trace PR 326 review findings before modifying its existing fleet/configuration seams."
roadmap_exempt: true
---

# Recon Map — fleet enrollment review follow-up

Contents: Subject · Seams · Calls/state · Contracts · Operations · Unknowns

Commit: `8ff740bff5e2e49bb70ab094e5d3810775450887`. Verify tier, graph plus current source reads. Lanes A/B/C delegated read-only; D (build/proof) in supervising context. Graph project rebalanceOS, generation 2026-09-02T03:54:57Z: stale primary checkout; fleet symbols missing, scripts excluded. Current task-clone reads replace those leads. No negative claim relies on graph absence.

## Status

| What was just completed | What's next |
|---|---|
| Recon informed independently reviewed safety fixes; follow-up landed in PR331 | Historical reference; no active recon work remains |

## Subject and change class

Resume PR #326 for issues #325 and #246; cross-module correction of the existing enrollment/configuration/upgrade path. No new authority, collector, database schema or fleet deployment.

## The seams

| Seam | Location | Crosses | Breaks if |
|---|---|---|---|
| Enrollment discovery | config_cmds.py:526 → config.py:1323/256 | CLI → shared config reader | Existing malformed JSON becomes defaults, allowing fallback or destructive rewrite |
| Pulse setter | config.py:1383/1400–1410 | CLI → existing canonical writer | The strict admission read is bypassed on the setter's reread |
| Timezone setting | config_cmds.py:499 → pulse.py:118/982; next_actions.py:1170 | Configuration → publisher and deep-work reader | Invalid IANA name is saved successfully |
| Collector backup/update | git_ops.py:93–108 | Shell-sourced collector config → enrollment | Incomplete first backup persists or file replacement widens permissions |
| Partial enrollment apply | config_cmds.py:561–567 | Collector file → Rebalance file → validation | Second write/validation fails after first file changed; exception has no recovery context |
| Upgrade refresh | UPGRADE.md:153 → setup_sleuth_file_source.sh:66 | Upgrade → live private checkout | Unlocked autostash pull races publisher or continues after failure |
| Shared writer lock | git_ops.py:245/591; collect.sh:391–410 | Python publishers ↔ collector | A setup pull avoids the existing lock/foreign-operation refusal |
| Reader retirement | SOP.md:382; pulseTreeProvider.ts:101–104 | Fleet output → configured VS Code sidebar | Root page removed while reader still points there |

## Calls and state

CLI pyproject entry → cli/__init__.py config registration → config_cmds fleet-enroll/set-pulse. Config resolver already centralizes explicit override/environment/project root. _read_config is tolerant by deliberate existing tests; strict admission must be opt-in. set_pulse_config owns pulse keys and uses _write_config. Enrollment invokes set_collector_values first, then setter, then optional fleet_settings postcondition. No atomic two-file transaction exists.

Installer and collector identity migration are separate legitimate config.sh writers (install.sh:56–145; collect.sh:113–138/325/654). Enrollment does not serialize those config writers. Completed independent backups and atomic replacement are narrower than a multiwriter transaction.

Existing reconcile_pulse_mirror (pulse.py:75–101) owns locked safe checkout refresh: shared git_publish_lock → git_pull_rebase_safe, with explicit failure. No current CLI caller found in the bounded src/cli scope. Sleuth's normal file reader already uses fetch+upstream blob (sleuth_reminders.py:181–207), not autostash. Removing setup's pull alone leaves its missing-local-export admission check unsatisfied.

Fleet rendered page already lives at devices/<canonical-device-id>/live-pulse.md (pulse.py:963, git_ops.py:230). VS Code selects an explicit file; its parser is filename-independent. Migrate settings and verify sections before deleting roots; do not change the parser.

## Contracts and prior art

lib/json_ops owns standard JSON dumping; lib/time_ops owns time helpers. Pulse's existing named-timezone helper can be promoted there rather than duplicated. Secret-store atomic writer has a different root/mode/nonoverwrite contract and cannot replace collector backup directly. Releases CLI here supports ROADMAP shadow sync/list, not modern roadmap rate/update/json verbs; use that existing owner, retain per-task ratings in the canonical plan/pointer and read back the shadow. No schema upgrade.

## Build, failure and rollback

Existing test_fleet_enroll, test_config_read_shape_guard, test_pulse_reconcile and test_git_publication_contract are the focused homes. No new suite, script, CI lane or daemon. Full root/HiQS suite baseline initially failed collection because NumPy was absent; raw output retained in temp until publication, dependency repaired through HiQS's declared dev install. Embeddings extras are absent; report skips honestly. 3-Eyes remains stood down.

Reverting code does not undo already-applied config. Existing named collector backup is a manual recovery aid, not automatic rollback of concurrent writes. Preserve config files and pending checkout state on failed refresh. No live configuration/database/lock file changes are authorized by this code task.

## Unknowns

| Unknown | Why it matters | What settles it |
|---|---|---|
| Actual other-Mac reader settings | Retirement cannot be qualified from fixtures | Operator verifies each configured reader before deletion |
| Legacy backup integrity | Previous writer may already have left a partial file | Operator inspects an existing backup; no invented retroactive integrity claim |
| Simultaneous config writers / two-file atomicity | Atomic replacement does not serialize enrollment/installer | Outside this narrow fix; no all-or-none/concurrency claim |
| Additional external root-page consumers | Sidebar is known, full fleet inventory is not | Operator inventory gate before retiring pages |

## Current-state radius

Configuration commands and tolerant getters, fleet check-in collector configuration, safe private checkout refresh, pulse/deep-work timezone readers, upgrade/Sleuth instructions and explicitly configured VS Code sidebar readers; no capture/history migration.

## Lessons Learned (For Future Agents)

This is the pre-change baseline map. GH-330 and PR331 own the subsequent strict-admission, backup and locked-refresh fixes; do not resume this historical fixture-reproduction step as unfinished work.
