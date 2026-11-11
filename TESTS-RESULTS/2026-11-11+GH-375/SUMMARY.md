# GH-375 — T3 Code session activity collector: verification

| Field | Value |
|---|---|
| Date | 2026-11-11 |
| Tracking issue | [#375](https://github.com/HiQS-Labs/rebalanceOS/issues/375) |
| Working doc | [GH-375-T3-CODE-SESSION-STORE.md](../../PROJECT/2-WORKING/GH-375-T3-CODE-SESSION-STORE.md) |
| Base | `development@70ccfc0` |
| Code under test | `118653f` (implementation `218be7c` + dry-run test `560c4e0`) |
| Plan QA | Codex relay, Approved r2/3 — [relay-system/2026-11-11/gh375-plan-codex.md](../../relay-system/2026-11-11/gh375-plan-codex.md) |
| Final QA | Codex relay — [qa/gh375-final-codex.md](qa/gh375-final-codex.md) |

## Results

| Check | Result | Evidence |
|---|---|---|
| Red-first | new suite errors on import; 4 raw-source set expectations fail before implementation | [red-first.txt](red-first.txt) |
| `tests/test_t3_code.py` + collector contract/registry | 24 + 19 passed | [mutation-witnesses.txt](mutation-witnesses.txt) (control line) |
| Mutation witnesses | 9 guards removed one at a time; each turns its named test red; unmutated control 24 passed | [mutation-witnesses.txt](mutation-witnesses.txt), [scripts/witness.sh](scripts/witness.sh) |
| Root suite `pytest tests/` | 2836 passed, 20 skipped, **14 failed — the identical set fails on base 70ccfc0** (auto-promote ×9, embedder ×4, project inference ×1) | [root-tests.txt](root-tests.txt) |
| HiQS suite (own venv, as CI) | 163 passed, 1 skipped, 1 xfailed | [hiqs-tests.txt](hiqs-tests.txt) |
| ruff check / format, mypy `src/` | clean / 669 formatted / no issues in 119 files | console |
| Ratchets (banned imports, script inventory, machine paths, read layer, near duplicates) | all `--check` ok, no baseline change | console |
| Doc links | 513 links, none broken | console |
| `rebalance doctor` | new check `OK — not enabled (opt-in)`; exit 1 from a pre-existing `orphaned vectors:github` ERROR, identical on base | [doctor.txt](doctor.txt) |
| Live smoke (dry run, this Mac's T3 store, 14-day window) | PASS: repo set and per-repo run/prompt totals and per-provider run splits equal an independent direct read-only count; rerun identical; dry runs created no DB; flag off skips without opening the store | [smoke.txt](smoke.txt), [scripts/smoke.py](scripts/smoke.py) |

## Threats to validity

- The live smoke is a **dry run**: per the operator's scope for this task, the flag was not enabled on this
  Mac and nothing was written to the operator's `rebalance.db`. The persisted flag-on refresh stays an
  open acceptance item on the issue.
- The direct count in the smoke shares the thread→workspace-root→`origin` mapping approach with the
  collector (independent SQL, same git resolution), so a shared mapping error would not be caught there;
  the fixture tests pin the mapping on a synthetic repo.
- Fixture DDL is a pinned subset of t3code's migrations; an upstream reshape is handled by the
  schema_version guard + column probes (witnessed), not by the fixture.
- The 14 root-suite failures were compared by test ID against base, not root-caused (out of scope).
