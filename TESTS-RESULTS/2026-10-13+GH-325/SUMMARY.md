# GH-325 — verification summary

Branch `fix/rebalanceOS-gh325-fleet-enroll-self-repair-2026-10-13`, base `origin/development` @ `0589b44`.
Code verified at `07b22ed`. Plan: `PROJECT/2-WORKING/GH-325-FLEET-ENROLL-SELF-REPAIR.md`.

## Plan QA

Codex, three rounds, `QA/gh325-plan-codex.md`. r1: 3 Should + Nit accepted. r2: 2 Should + Nit
accepted. r3: Approved (relay-drive attestation, reviewed `14c1f29`).

## Automated

| Check | Result |
|---|---|
| `tests/test_fleet_enroll.py` (new: resolver, writer, discovery, CLI, doctor rows) | 19 passed, 12 subtests |
| Mutation check of the new tests (each reverted after) | conflict check off → 3 fail; `$HOME` expansion off → 5 fail; first-duplicate-only write → 1 fail; validate-before-write removed → 1 fail |
| Full suite, CI flags (`.[calendar,server,dev]`, embedder tests ignored) | 2754 passed, 20 skipped, 10 xfailed (pre-existing GH-178 quarantine) |
| `ruff check .`, `ruff format --check .`, `mypy src/` | clean |
| CI ratchets: banned imports, script inventory, machine paths, read layer, near duplicates, doc links, frontdoor | clean |

## Red controls — public `run_doctor` report, same inputs, base vs candidate

Script: `doctor-red-control.py` (temp config only; collector-health read stubbed to `[]` so the
fleet branch is reached). Outputs: `doctor-red-control.base-0589b44.jsonl`, `…candidate.jsonl`.

| Scenario | Base `0589b44` | Candidate |
|---|---|---|
| (a) collector installed, Mac not enrolled | no enrollment row at all | `pulse fleet` WARN "this Mac is not enrolled in fleet mode", hint `rebalance config fleet-enroll` |
| (b) fleet on, collector config missing | generic `fleet configuration` error, **empty hint** | adds `pulse fleet` error naming `bash experimental/git-pulse/install.sh`; generic row kept |

## Manual checks (this Mac Studio)

- `fleet-enroll` preview against the live runtime config (read-only): one planned change,
  `remove pulse_filename` (the Studio still sets it). `--print-clone` returned the Studio's clone,
  exit 0. Both config files byte-identical before and after (shasum).
- `scripts/setup_sleuth_file_source.sh` with collector `sync_repo_dir="$OTHER/repo"` in a temp
  HOME/config: exit 1, message "cannot tell which pulse clone this Mac uses", temp HOME empty
  (nothing cloned), temp config unchanged.

Not done here (operator-run, per SOP): applying `fleet-enroll` on any Mac, the four-Mac rollout,
and legacy page retirement.
