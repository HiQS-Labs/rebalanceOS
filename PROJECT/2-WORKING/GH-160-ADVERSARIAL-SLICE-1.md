---
gh_issue: 160
source: https://github.com/HiQS-Labs/rebalanceOS/issues/160
title: "GH-160 slice 1 — harden local_tz() and registry loading with property tests"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). Tier-1 targets 3 and 4 from the issue; the config guard (#161) and md_parser (#165) are already done."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: testing
rating: "pri/sev/appeal/effort 50/55/60/55 · calc 220"
effort: 2
complexity: 2
risk: 1
phases: 1
ratings_provisional: false
goal: >
  Two of the issue's enumerated Tier-1 parse-and-crash targets get Hypothesis-backed hardening:
  `local_tz()` must not raise on a malformed REBALANCE_TZ (verified: "/UTC" and "../.." currently
  crash), and registry loading must convert uncaught yaml.YAMLError / pydantic ValidationError into
  a diagnosable failure rather than a traceback.
non_goals:
  - Tier 2 (silent wrong answers) and the remaining Tier-1 targets (next_actions grammar) — later slices.
  - Porting the XYZ-forge ATE — the issue itself rejects that.
---

# GH-160 slice 1 — local_tz() and registry loading

## Status

| What was just completed | What's next |
|---|---|
| Capture for the 2026-09-05 marathon; Hypothesis is already in the dev extra (#165). | Builder lane. |

## Acceptance

From #160 §3, targets 3 and 4, verbatim:

3. **`src/rebalance/ingest/registry.py:73-79,94`** — uncaught `yaml.YAMLError` and uncaught pydantic `ValidationError` on the project registry.
4. **`src/rebalance/lib/time_ops.py:146-171` `local_tz()`** catches only `ZoneInfoNotFoundError`. **Verified by execution:** `REBALANCE_TZ="/UTC"` and `REBALANCE_TZ="../.."` crash.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_time_ops_consolidation.py tests/test_collector_registry.py tests/test_time_ops_property.py tests/test_registry_property.py -q",
  "fix_probes": [
    { "type": "path_absent", "path": "tests/test_time_ops_property.py" },
    { "type": "path_absent", "path": "tests/test_registry_property.py" }
  ],
  "artifacts": [
    "src/rebalance/lib/time_ops.py",
    "src/rebalance/ingest/registry.py",
    "tests/test_time_ops_property.py",
    "tests/test_registry_property.py"
  ],
  "artifacts_new": [
    "tests/test_time_ops_property.py",
    "tests/test_registry_property.py"
  ],
  "remediation": {
    "source": "issue#160",
    "criteria": "local_tz() never raises on malformed REBALANCE_TZ (falls back with a warning); registry loading turns YAML/pydantic errors into a named, tested failure; both pinned by Hypothesis tests."
  },
  "lanes": { "agy_safe": ["src/rebalance/lib/time_ops.py", "src/rebalance/ingest/registry.py", "tests/test_time_ops_property.py", "tests/test_registry_property.py"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified.*

## Phase 1

- [ ] Red controls first: `REBALANCE_TZ="/UTC"` and `"../.."` reproduce the crash on the current tree; a malformed registry YAML and a schema-violating project reproduce the tracebacks.
- [ ] `local_tz()`: catch the full failure surface (`ValueError`, `OSError`, `IsADirectoryError`, plus `ZoneInfoNotFoundError`), warn once, fall back to the existing default.
- [ ] Registry: wrap `yaml.safe_load` and the pydantic construction; raise one repo-defined error naming the file and the reason.
- [ ] Hypothesis: `st.text()` over `REBALANCE_TZ`; arbitrary YAML-ish text over the registry loader — neither may raise anything but the named error.

### QA checklist
- [ ] Every red control witnessed red before its fix.
- [ ] Existing time_ops and registry tests unchanged and green.
- [ ] No behaviour change for a VALID tz or registry.
