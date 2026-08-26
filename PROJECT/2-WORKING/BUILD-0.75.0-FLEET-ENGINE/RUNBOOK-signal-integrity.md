---
title: "Signal Integrity Marathon Runbook"
status: "Draft"
created: 2026-08-25
updated: 2026-08-25
owner: noel
goal: "How to actually launch MARATHON-signal-integrity.yaml, and the two things that stop it"
roadmap_exempt: true
pdda_hold: true
---

# Runbook — Signal Integrity marathon (build 0.75.0 Fleet Engine)

Dry-run result, against a fresh clone of `development` at `ed8aad2`:
**`4 phase(s) would run in order` — si1 → si2 → si3 → si4, exit 0.**

Two things must be true before a LIVE run, and neither is the default. Both were found by the
dry-run, not by reading the plan.

## 1. The marathon cannot be driven from inside rebalanceOS

`xyz-vendor.sh` reports, and GH-514's preflight enforces, that a run here **refuses before
dispatch**:

```
The rules in the way (file:line:pattern <TAB> path):
  .gitignore:136:phases/       phases/
  .gitignore:142:relay-system/ relay-system/
```

marathon-drive writes `marathon-system/` and `relay-system/` and then `git add`s both. An ignore
rule on either makes the add fail and **halts the chain mid-run — including after a phase has
already passed its gate**, which destroys the record of why it stopped.

Do **not** un-ignore them. Those rules are deliberate: this is a public repo and the transcripts
are builder/reviewer working logs. Publishing them is not undoable, and `git add -f` is the same
mistake in a different shape.

The supported answer is `--target-root`: drive from a harness clone, land only code changes here.

```
# from the harness clone (NOT from rebalanceOS)
relay-automation/marathon.sh \
  --plan PROJECT/2-WORKING/BUILD-0.75.0-FLEET-ENGINE/MARATHON-signal-integrity.yaml \
  --target-root /path/to/rebalanceOS \
  --pre-advance-cmd ".venv/bin/python -m pytest -q"
```

The relay thread, tick token, `marathon-system/` and `relay-system/` transcripts all stay in the
harness clone; only the artifact edits land in rebalanceOS.

## 2. The pre-advance gate needs a venv the README does not build

The default gate is `bash validate.sh`. **This repo has no `validate.sh`**, so the gate must be
supplied or marathon-drive halts before turn 1.

The supplied gate must use the venv interpreter, and the venv must be built with the `server`
extra plus pytest. Measured on a fresh clone:

| Command | Collected |
|---|---|
| `python3 -m pytest -q` (system interpreter) | **0** |
| `.venv/bin/python -m pytest -q`, README install `.[embeddings,calendar]` | 2320, **13 collection errors** |
| `.venv/bin/python -m pytest -q`, `.[embeddings,calendar,server]` + pytest | **2441, clean** |

Both wrong invocations FAIL LOUDLY rather than passing silently — pytest exits 5 on
"no tests collected" and non-zero on collection errors, so marathon-drive halts at phase 1 either
way. (An earlier draft of this runbook claimed a zero-test gate would report success and approve
every phase. That was asserted, not measured, and it is wrong: exit 5 is non-zero. The cost of
getting the gate wrong here is a halted run and a confusing error, not a silently rubber-stamped
one.)

The 13 errors are all `ModuleNotFoundError: No module named 'fastapi'`, which lives in the
`server` extra. `README.md:28` documents `.[embeddings,calendar]` and does not mention `server`
or pytest, so the documented Getting Started path produces a clone whose suite cannot collect.
That belongs to 0.70.0 Green Board's exit criterion, not to this marathon — filed separately
rather than fixed here.

Clone bring-up that does work:

```
python3 -m venv .venv
.venv/bin/pip install -e ".[embeddings,calendar,server]" pytest
.venv/bin/python -m pytest -q --collect-only   # expect 2441 collected, 0 errors
```

## Phase order and write sets

| Phase | Issue | Artifact |
|---|---|---|
| si1 | #54, #62 | `src/rebalance/ingest/_http.py`, `tests/test_http_client.py` |
| si2 | #62 | `src/rebalance/ingest/github_scan.py`, `tests/test_github_scan.py` |
| si3 | #75 | `scripts/health_issue_reporter.py`, `tests/test_health_issue_reporter.py` |
| si4 | #123 | `src/rebalance/ingest/next_actions.py`, `tests/test_next_actions.py` |

The write sets are disjoint, which is worth knowing but buys no parallelism — marathon phases run
strictly one at a time (GH-241). The `depends_on` chain is real: si2 leans on si1's budget and
ETag cache, si3 leans on si1's client, and si4 must respect si1's budget when it resolves users.
