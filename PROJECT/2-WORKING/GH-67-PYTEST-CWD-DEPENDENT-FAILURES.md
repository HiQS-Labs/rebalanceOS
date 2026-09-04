---
gh_issue: 67
source: https://github.com/HiQS-Labs/rebalanceOS/issues/67
title: "GH-67 pytest results depend on the invoking directory"
status: "Done (0.70.0 Green Board quick win)"
created: 2026-08-27
updated: 2026-09-04
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
| Pinned the sandbox repo as the default `cwd` in `tests/test_uninstall_rebalance.py`'s `_run()` helper. Verified 0 failures from both the repo root and `/tmp`. **2026-09-04:** independently re-verified still fixed, and the declared `[tool.pytest.ini_options]` guard landed via #162. | None — the fix and its guard are both in. |

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

## Independent re-verification, 2026-09-04

Re-checked from scratch in a fresh full clone of `development` at `6ceb02a`, with its own
virtualenv, by someone who had not seen the 2026-08-27 fix. Recorded here because a closed issue
with no re-measurement is a claim, not evidence.

| Invocation directory | Result |
|---|---|
| repo root | 10 failed, 2146 passed, 20 skipped, 10 xfailed |
| `/tmp` | 10 failed, 2146 passed, 20 skipped, 10 xfailed |

The two `FAILED` lists are **byte-identical**, and none of the 15 tests this issue named appear in
either — the 14 in `tests/test_uninstall_rebalance.py` and the one in `tests/test_doctor_json.py`
all pass from both directories. The `_run()` fix holds.

The 10 remaining failures are pre-existing and environmental on an Apple Silicon host: the
`sentence-transformers` embedder (not in the `dev` extra, and `--ignore`d by CI) and macOS
Keychain-backed credential paths. Under CI's exact command the count is 6 failed / 2142 passed,
all Keychain-bound. They are unrelated to invocation directory.

**On the guard.** This issue's real argument was that the suite's result depended on an input
nobody declared. That is now closed from the other direction: #162 added the
`[tool.pytest.ini_options]` block, so `pyproject.toml` is a pytest inifile and `rootdir` resolves
to the repo rather than being inferred per-invocation. Confirmed by running from `/tmp` and reading
back `rootdir: <repo>`, `configfile: pyproject.toml`. `--strict-config` was added alongside, so a
typo in that block is an error rather than a silently ignored line.

**Not built, deliberately.** This issue also suggested a check that fails when the suite's result
differs between two invocation directories. That means running the suite twice, doubling a
90-second job, and is a test-infrastructure decision worth taking on its own rather than folded in
here. Parked, not dropped.

**Retained evidence.** Raw transcripts, the rootdir proof, and a threats-to-validity section are
published at [TESTS-RESULTS/2026-09-04+GH-67/](../../TESTS-RESULTS/2026-09-04+GH-67/), per `SOP.md` §1
— a claim whose evidence is unpublished is an assertion.

**Caveat on the evidence above.** Two invocation directories is a two-point comparison, not a
proof. It falsifies the specific symptom this issue reported; it does not establish
directory-independence in general. A third point outside `$HOME`, or a directory containing a
stray `conftest.py`, would test it harder.

## Lessons Learned (For Future Agents)

A test helper with an optional `cwd=` parameter that defaults to `None` is not neutral —
`subprocess.run(cwd=None)` inherits the *caller's* process CWD, which for a test suite is
wherever the operator happened to type `pytest` from. If the code under test is
CWD-sensitive by design, the test harness must pin a CWD by default, not merely allow one to
be set.
