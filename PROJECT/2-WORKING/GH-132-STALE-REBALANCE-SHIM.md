---
gh_issue: 132
source: https://github.com/HiQS-Labs/rebalanceOS/issues/132
title: "GH-132 stale rebalance shim on PATH (ported from legacy #261)"
status: "Done (0.70.0 Green Board quick win)"
created: 2026-08-27
updated: 2026-08-27
owner: noel
doc_type: hygiene
goal: >
  Detect, rather than let the operator debug cold, a stale `rebalance` shim earlier
  on PATH than the working install — the class of defect the retiring repo tracked
  as #261, ported here since it's a general ergonomics gap, not a fixed-repo bug.
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
roadmap_exempt: true
---

# GH-132 — Stale `rebalance` shim on PATH (ported from legacy #261)

## Status

| What was just completed | What's next |
|---|---|
| Added `_check_rebalance_shim()` to `rebalance doctor`, wired into `run_doctor()`; revised after an agy QA pass (see below); 8 regression tests. | None — closed as a Green Board quick win. |

## Revision (agy QA pass, 2026-08-27)

An `/relay-xyz` review with agy on the initial version (anchored on `sys.argv[0]`) found it would
false-positive under `python -m rebalance doctor` — this repo ships a real
`src/rebalance/__main__.py`, so that invocation is genuine, and argv[0] there is `__main__.py`'s
path, not the console script's. Also flagged: `#!/usr/bin/env python3` shebangs extracted `/usr/bin/env`
itself as "the interpreter" rather than resolving `python3`.

Fixed by anchoring on `sys.executable` (invariant across invocation shape) instead of `sys.argv[0]`,
and resolving an `env`-form shebang's target name via `shutil.which()`. **While verifying that fix
live**, a second, more severe false positive turned up that agy's review never touched: a normal
`python3 -m venv` layout symlinks `.venv/bin/python3` to a base interpreter (Homebrew's, here) —
`.resolve()`-ing `sys.executable` walks straight out of the venv, so the check false-positived on
this repo's own correctly-invoked `.venv/bin/rebalance doctor`. Fixed by comparing normalized
(`os.path.abspath`) paths instead of symlink-resolved ones — "same script path" is the right
invariant, not "same real file". Confirmed OK against `.venv/bin/rebalance doctor --json` directly.

Also applied agy's minor GH-67 finding in the same pass: `tests/test_uninstall_rebalance.py`'s
`_run()` used `cwd=cwd or str(repo)`, which would silently misbehave if a caller ever passed
`cwd=""`. Changed to `cwd=str(repo) if cwd is None else cwd`.

## Why

Legacy #261 documented a real operator incident: a leftover `.venv-py314-backup/bin/rebalance`
shim was first on PATH, its shebang pointing at a `python3.14` that no longer existed after
the venv moved to 3.13. A bare `rebalance ...` then failed with `command not found` naming
the dead interpreter path — nothing pointed at the actual cause (a stale venv shadowing the
working one). Not reproducible in this repo's checkout (no stale venv present here), but the
failure class is general: any operator who regenerates a venv accumulates this risk, and the
error message actively misleads whoever hits it.

## What changed

- `src/rebalance/doctor.py`: new `_check_rebalance_shim()` check.
  - Compares `shutil.which("rebalance")` (first PATH match) against the running script
    (`sys.argv[0]`, resolved).
  - Match → OK. No PATH entry → OK (nothing to compare).
  - Mismatch + shadowing shim's shebang interpreter doesn't exist → WARN, names both paths
    and the dead interpreter, hints `which -a rebalance`.
  - Mismatch + shim otherwise readable → WARN (generic shadow warning; still actionable).
  - Wired into `run_doctor()` alongside the other lightweight standalone checks.
- `tests/test_doctor_rebalance_shim.py`: 4 hermetic tests (match, no-PATH-entry, dead
  interpreter, live-interpreter shadow) — all monkeypatch `doctor.sys.argv` /
  `doctor.shutil.which`, no real PATH state involved.

## Why a doctor check, not a repo-level fix

There is no stale venv *in this repository* to delete — #261's root cause lived entirely on
the reporting operator's machine, outside version control. A one-off `rm -rf` there would fix
one person's PATH and nothing else. The doctor check generalizes: it catches this exact
failure class for any operator, on any machine, the next time it recurs — which is the actual
ask behind "closes it" in the original issue's suggested fix list (option 3, generalized).

## Verification

- `.venv/bin/python -m pytest tests/test_doctor_rebalance_shim.py -q` → 8 passed
- `.venv/bin/ruff check src/rebalance/doctor.py tests/test_doctor_rebalance_shim.py tests/test_uninstall_rebalance.py` → clean
- `.venv/bin/mypy src/rebalance/doctor.py` → clean
- Full suite (`tests/`) → 2048 passed, 16 skipped, 10 xfailed, no regressions
- Live: `.venv/bin/rebalance doctor --json` → `rebalance shim` check reports `ok` against this
  repo's real venv (previously false-positived `warning` before the abspath fix)

## Lessons Learned (For Future Agents)

A "local machine" bug report is not automatically out of repo scope. The specific stale venv
was local; the failure mode it exposed (PATH shadowing with an opaque error) is a defect
class the code can detect for everyone. Look for the general check hiding inside a
one-machine incident before dismissing it as non-actionable.
