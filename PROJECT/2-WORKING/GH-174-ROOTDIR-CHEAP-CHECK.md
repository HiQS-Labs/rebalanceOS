---
gh_issue: 174
source: https://github.com/HiQS-Labs/rebalanceOS/issues/174
title: "GH-174 — directory-independence: implement option 1, the seconds-long rootdir assertion"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). Option 1 of the three costed in the issue."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: hygiene
rating: "pri/sev/appeal/effort 55/45/65/90 · calc 255"
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
goal: >
  One test that runs `pytest --collect-only -q` from a foreign directory (outside the repo, and
  from a directory containing a stray conftest.py) and asserts the header reports the repo as
  rootdir and pyproject.toml as configfile. Seconds, not a doubled CI job.
non_goals:
  - Options 2 and 3 (subset differential; nightly full differential). If option 1 proves enough, the issue closes on that measurement.
---

# GH-174 — the cheap rootdir assertion

## Status

| What was just completed | What's next |
|---|---|
| Capture for the 2026-09-05 marathon; option 1 chosen per the issue's own cost ordering. | Builder lane: the test, plus the measured wall-clock cost stated in the PR. |

## Acceptance

Verbatim from #174:

Whatever lands should state, in the PR, which of the three options above it implements and what it costs in CI wall-clock — measured, not estimated. If the answer is "option 1 is enough", closing this issue with that measurement recorded is a valid outcome.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_pytest_rootdir_pinned.py -q",
  "fix_probes": [
    { "type": "path_absent", "path": "tests/test_pytest_rootdir_pinned.py" }
  ],
  "artifacts": [
    "tests/test_pytest_rootdir_pinned.py"
  ],
  "artifacts_new": [
    "tests/test_pytest_rootdir_pinned.py"
  ],
  "remediation": {
    "source": "issue#174",
    "criteria": "A single fast test asserts rootdir/configfile resolve to the repo from a foreign cwd and from a dir with a stray conftest.py; its wall-clock cost is measured and stated."
  },
  "lanes": { "agy_safe": ["tests/test_pytest_rootdir_pinned.py"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified.*

## Phase 1

- [ ] `tests/test_pytest_rootdir_pinned.py`: subprocess `pytest --collect-only -q <repo>/tests` with `cwd=` (a) a temp dir outside the repo, (b) a temp dir containing a stray `conftest.py` that would break collection if honoured; parse `rootdir:` and `configfile:` from the header.
- [ ] Measure the test's own wall-clock and state it in the PR body.

### QA checklist — Phase 1
- [ ] Witnessed red: temporarily point the subprocess at a copy of the repo with `[tool.pytest.ini_options]` removed and confirm the assertion fails.
- [ ] Test is hermetic — no dependency on the operator's machine paths.
