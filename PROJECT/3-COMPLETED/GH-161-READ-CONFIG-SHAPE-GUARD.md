---
gh_issue: 161
source: https://github.com/HiQS-Labs/rebalanceOS/issues/161
title: "GH-161 _read_config() returns non-dict for valid JSON of the wrong shape"
status: "Merged 2026-09-04 as 4b71033 via PR #164; shipped into 0.70.0 Green Board."
created: 2026-09-03
updated: 2026-09-04
owner: noelsaw1
doc_type: plan
goal: >
  Make _read_config() return a dict for any file contents, so a hand-edited
  config whose top level is a list, number, string, or null degrades loudly to
  defaults instead of raising AttributeError out of ~40 unrelated getters.
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
roadmap_exempt: false
---

# GH-161 — `_read_config()` shape guard

## Status

| What was just completed | What's next |
|---|---|
| Shape guard + loud-discard warning in `src/rebalance/ingest/config.py`; 19 regression tests in `tests/test_config_read_shape_guard.py`, witnessed 14-red pre-fix. | Merge into `development`. Then decide #161's sibling question: whether the same warn-on-discard treatment belongs in `paths.py::_load_user_config`, which guards the shape but discards silently. |

## Why

`_read_config()` returned whatever `json.loads` produced, with no check that it
was a `dict`. The `except (json.JSONDecodeError, IOError)` clause catches
*malformed* JSON; it cannot catch *well-formed* JSON of the wrong shape, and the
`-> dict[str, Any]` annotation is not enforced at runtime.

So a 7-byte file containing `[1,2,3]` — which parses perfectly — propagated a
list to roughly 40 getters that each call `.get(...)` on the result. The
operator saw:

```
AttributeError: 'list' object has no attribute 'get'
```

raised from `get_vault_path`, a frame that names nothing about the actual
problem (a hand-edited `temp/rbos.config`).

The sibling reader `rebalance.paths._load_user_config` has always had the
`isinstance(data, dict)` guard. This was an inconsistency between two config
readers, not an open design question.

## What changed

`src/rebalance/ingest/config.py`:

1. **Shape guard.** `_read_config()` now returns `{}` unless `json.loads`
   produced a `dict` — mirroring `paths.py`.
2. **`IOError` → `OSError`.** `IOError` is an alias; `paths.py` already spells
   it correctly. The two `except` arms are now split so each can name its own
   reason.
3. **Loud discard.** `_warn_discarded_config()` prints one line to stderr saying
   which file was ignored, why, and that every setting in it is being skipped.
   This is the #115/#116 failure mode — silent reversion to defaults — and it is
   the half of this fix that saves the *next* operator's afternoon.
4. **Warned once per path per process,** via `_WARNED_BAD_CONFIG`. `_read_config`
   is called by ~40 getters; forty identical warnings in one CLI run is
   operationally the same as none, and worse than one.

## Control

Both directions were measured, not asserted.

**Live repro, before the fix** — every payload is valid JSON, so the old
`except JSONDecodeError` could never have fired on any of them:

| Config contents | `get_vault_path()` before | after |
|---|---|---|
| `[1,2,3]` | `AttributeError: 'list' …` | `None` + one stderr warning |
| `42` | `AttributeError: 'int' …` | `None` + one stderr warning |
| `"x"` | `AttributeError: 'str' …` | `None` + one stderr warning |
| `null` | `AttributeError: 'NoneType' …` | `None` + one stderr warning |
| `{"vault_path":"/ok"}` | `/ok` | `/ok`, no warning |

**Suite control.** `tests/test_config_read_shape_guard.py` run against the
unmodified `config.py`: **14 failed, 5 passed**. The 5 that pass either way are
the deliberate negative controls — missing file, `{}`, malformed JSON, a real
config that must still resolve, and "a valid config warns about nothing". A
guard that discarded *everything* would satisfy the other 14 and fail those.
Post-fix: **19 passed**.

## Verification

- `pytest tests/test_config_read_shape_guard.py` — 19 passed.
- `pytest tests/ -k "config or doctor or paths or onboard"` — 299 passed.
- Full suite — 2178 passed, 1 failed. The single failure is
  `test_doc_links.py::test_repo_is_clean`, which scans `temp/claude-prompts.md`,
  a **gitignored symlink** to an operator's Obsidian prompt log. It is unrelated
  to this change (this branch adds no Markdown links) and reproduces on any
  branch where that symlink exists. Noted below rather than fixed here.

## Out of scope — recorded, not done

- **`test_doc_links` scans gitignored paths.** Any operator with a symlink under
  `temp/` gets a red suite locally while CI stays green. Real, small, and
  someone else's lane.
- **`paths.py::_load_user_config` discards silently.** It has the shape guard but
  no warning, so it still has the #115/#116 shape. Worth the same four-line
  treatment; deliberately not bundled into a fix that is otherwise one module.
- **The property-testing argument in #160/#162.** This defect is exactly the kind
  a property test finds on its first run. That is #162's scope, not this one's.
