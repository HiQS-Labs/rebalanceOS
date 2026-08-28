---
gh_issue: 67
source: https://github.com/HiQS-Labs/rebalanceOS/issues/67
title: "GH-67 pytest results depend on the invoking directory"
status: "Done (0.70.0 Green Board quick win)"
created: 2026-08-27
updated: 2026-08-27
owner: noel
doc_type: hygiene
goal: >
  The test suite's result must not depend on the directory pytest is invoked from.
  14 tests in test_uninstall_rebalance.py + 1 in test_doctor_json.py failed only
  when pytest ran from outside the repo root.
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
roadmap_exempt: true
---

# GH-67 — pytest results depend on the invoking directory

## Status

| What was just completed | What's next |
|---|---|
| Pinned the sandbox repo as the default `cwd` in `tests/test_uninstall_rebalance.py`'s `_run()` helper. Verified 0 failures from both the repo root and `/tmp`. | None — closed as a Green Board quick win. |

## Why

`scripts/uninstall_rebalance.sh` resolves relative operands with `os.path.realpath()`
against its own process CWD (a documented, deliberate ownership-safety choice — see the
"QA r10 Blocker" comment in that script). The test suite's `_run()` helper passed that CWD
straight through from whichever caller invoked it; 14 of its 15 callers never set `cwd=`
explicitly, so they silently inherited **pytest's own invocation directory** rather than the
sandbox fixture's repo path. CI always runs from the repo root, so this was invisible there —
but it meant a green CI run was evidence the code worked from one particular directory, not
that it worked at all.

## Reproduction (before fix)

```
cd /tmp && <repo>/.venv/bin/python -m pytest <repo>/tests/ -q
# 14 failed, 2022 passed (matches the issue's original 14-test list exactly)
```

## What changed

- `tests/test_uninstall_rebalance.py::_run()`: `cwd=cwd` → `cwd=cwd or str(repo)`. A caller
  that needs a different directory can still pass one explicitly (as
  `test_apply_removes_a_job_this_repo_owns` already does); every other caller now states its
  intended directory instead of inheriting an accidental one.
- `tests/test_doctor_json.py::test_suppressed_warn_yields_ok_verdict_but_stays_diagnosable`:
  did not reproduce in isolation or as part of the full suite after the `_run()` fix; not
  independently CWD-dependent as far as this pass could determine. Left as-is — re-open a
  fresh issue if it resurfaces.

## Verification

- `cd /tmp && .venv/bin/python -m pytest <repo>/tests/test_uninstall_rebalance.py <repo>/tests/test_doctor_json.py -q` → 64 passed
- `.venv/bin/python -m pytest tests/test_uninstall_rebalance.py tests/test_doctor_json.py -q` (repo root) → 64 passed
- Full suite from repo root → 2044 passed, 16 skipped, 10 xfailed (no regressions)

## Lessons Learned (For Future Agents)

A test helper with an optional `cwd=` parameter that defaults to `None` is not neutral —
`subprocess.run(cwd=None)` inherits the *caller's* process CWD, which for a test suite is
wherever the operator happened to type `pytest` from. If the code under test is
CWD-sensitive by design, the test harness must pin a CWD by default, not merely allow one to
be set.
