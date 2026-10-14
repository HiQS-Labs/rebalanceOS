---
gh_issue: 325
source: https://github.com/HiQS-Labs/rebalanceOS/issues/325
title: "Fleet enrollment: device-agnostic pulse clone path, enroll helper, doctor checks, self-repair on upgrade"
status: "Captured — plan drafted, awaiting Codex plan QA"
created: 2026-10-13
updated: 2026-10-13
owner: noel
doc_type: feature
goal: >
  Any Mac, whatever its pulse clone folder is called, can be enrolled into fleet mode with one
  command, and doctor names every fleet/pulse config gap with the command that repairs it, so the
  agent running UPGRADE.md repairs drift on the next upgrade instead of an operator hand-editing.
effort: 2
complexity: 2
risk: 2
phases: 1
ratings_provisional: false
roadmap_exempt: false
---

# GH-325 — Fleet enrollment and self-repair on upgrade

Also closes [#246](https://github.com/HiQS-Labs/rebalanceOS/issues/246) (no `rebalance config`
command sets pulse keys). Related: #282 (fleet delivery umbrella), #281 (per-device config owner).

## Task table

| Issue | Scope | Clone / branch | State | PR |
|---|---|---|---|---|
| [#325](https://github.com/HiQS-Labs/rebalanceOS/issues/325) | items 1–6 below | `rebalanceOS-gh325-fleet-enroll-self-repair-2026-10-13` / `fix/rebalanceOS-gh325-fleet-enroll-self-repair-2026-10-13` | plan QA | — |
| [#246](https://github.com/HiQS-Labs/rebalanceOS/issues/246) | item 3 (same command) | same | plan QA | — |

Base: `origin/development` @ `0589b44`.

## Rating (2026-10-13)

`rated 65/55/50/55` (pri/sev/appeal/effort). Severity 55: no data loss; the consequence is that three
of four Macs cannot be enrolled without hand-editing two config files, and wrong docs send a Mac's
clone to a folder its config does not use — a Mac silently stays out of the fleet or `pulse-sync`
fails until someone notices. Priority 65: it blocks #282's four-Mac qualification, and the same
class (per-device config nobody owns or checks) is the #281 umbrella — #281 counted 17 issues in the
14 days to 2026-09-26; #277 and #302 are recent device-health instances. Trend over the last 14 days
versus the 14 before was not recounted here (unknown). Appeal 50 (neutral, no user value given).
Effort 55: one doctor check, one CLI verb, docs, no schema change.

## Observed problem (recon)

1. **Hardcoded clone folder.** `UPGRADE.md:144-149` (step 3, "Sleuth") clones
   `rebalance-git-pulse` to `~/git-pulse-sync` and sets `--base-url ~/git-pulse-sync/…`. The same
   default is in `scripts/setup_sleuth_file_source.sh:28` and `SLEUTH_SYNC.md:21,41,46-54,71-74`.
   It sits under Sleuth because the Sleuth export is published into the same repo
   (`sync/sleuth/reminders-<ws>.json`). Mac Mini's clone is `~/Documents/GitHub/rebalance-git-pulse`;
   Mac Studio's is `~/git-pulse-sync`. The truth for each Mac is already in its own config:
   collector `sync_repo_dir` (`~/.config/git-pulse/config.sh`) and Rebalance `pulse_target_path`.
2. **No rollout/retirement plan.** SOP.md § "GH-282 — fleet delivery deployment and lessons"
   enables one Mac. Nothing orders the other three, or retires the Python-written shared root pages
   that fleet mode stops updating: `live-pulse.md` and `live-pulse-<device>.md` (from per-device
   `pulse_filename`). Collector files `pulse-<id>.md` and `devices/<id>.yaml` are **still written**
   in fleet mode (`collect.sh:537-540,735`) and read by `health-check.py`, `recap.py`, `view.sh` and
   `pulse_health` — they are not retired.
3. **No enroll helper; doctor silent.** Enrolling = collector `fleet_mode=true`,
   `fleet_sync_subdir=<sync_subdir>` plus Rebalance `pulse_fleet_enabled=true`,
   `pulse_device_id=<device_id>` (SOP step 4). `set_pulse_config()` (`ingest/config.py:1381`) has
   no callers and no CLI (#246). `_check_pulse()` (`doctor.py:2155`) only checks
   `github_login`/`pulse_target_path`; it never calls `fleet_settings()`, so a fleet misconfiguration
   surfaces only when `pulse-sync` runs and fails.
4. **`pulse_filename` silently ignored.** `pulse.py:963` uses `devices/<id>/live-pulse.md` in fleet
   mode. `get_pulse_config()` defaults `pulse_filename` to `live-pulse.md`, so "explicitly set" must
   be read from the raw config.
5. **Literal-path rule undocumented.** `fleet_settings()` (`lib/git_ops.py:33-77`) parses
   `config.sh` without shell evaluation, refuses any value containing `$`, and requires
   `sync_repo_dir` to resolve to the same directory as `pulse_target_path`. SOP step 4 says neither.

## Outcome sought / smallest bet / non-goals

- **Outcome:** on each Mac's next upgrade, the agent following UPGRADE.md runs `rebalance doctor`,
  sees every fleet/pulse gap named with its repair command, runs it, and ends green — whatever the
  clone folder is called.
- **Build:** (a) one doctor check extension, (b) one CLI verb `rebalance config fleet-enroll`
  (preview by default, `--apply` writes) plus `rebalance config set-pulse` for #246,
  (c) doc changes in UPGRADE.md, SOP.md, SLEUTH_SYNC.md, and a config-derived default in the setup script.
- **Not built:** no auto-enrollment without confirmation (SOP keeps the per-Mac qualification gate);
  no `$HOME` expansion in `fleet_settings()` (keeping the no-shell-eval rule; the helper writes the
  literal path instead); no moving anyone's clone; no deletion of legacy files in this PR (it is a
  documented, operator-run step in the private pulse repo); no change to `repair.py` (runtime git
  repair, unrelated); no #287 per-Mac state dir.
- **Alternative rejected:** docs-only fix (rewrite UPGRADE.md to say "use your path"). Rejected — the
  issue requires the next upgrade to *detect and repair* drift; without a doctor signal and a named
  command the agent has nothing deterministic to act on, and #246 stays open.
- **Rollback:** revert the PR. The command only writes when `--apply` is passed and backs up
  `config.sh` first (`config.sh.bak-gh325`); Rebalance config keys it sets are the same ones SOP
  step 4 already tells operators to set by hand.

## Design

Existing subsystems extended, no new modules:

- **Collector config reader** — refactor the literal `config.sh` parse already inside
  `fleet_settings()` into `read_collector_config()` in `lib/git_ops.py` (same regex, same no-eval
  rule, adds `sync_repo_dir` already in the key set). `fleet_settings()` calls it; doctor and the
  CLI reuse it. One parser.
- **Collector config writer** — `install.sh`'s `set_config_value` is bash inside an installer that
  also loads launchd, so it is not callable as a library. Add `set_collector_values()` next to the
  reader in `lib/git_ops.py`: same line-replace-or-append semantics, writes literal double-quoted
  values, backs up once. It is used only by `fleet-enroll`. (Disclosed second writer of a file the
  installer also writes; the keys it touches — `fleet_mode`, `fleet_sync_subdir`, `sync_repo_dir` —
  are ones `install.sh` never sets after creation.)
- **Rebalance config writer** — reuse `set_pulse_config()`. Add one capability: a way to remove
  `pulse_filename` (pass `pulse_filename=""` → key deleted), since fleet mode ignores it.
- **Doctor** — extend `_check_pulse()` into `_check_pulse()` + `_check_pulse_fleet()` (new rows
  named `pulse fleet`), added beside it at `doctor.py:2558`. Rows, each with its repair command as
  the hint:

  | Condition | Status | Hint |
  |---|---|---|
  | collector config absent | no row | — |
  | collector `fleet_mode=true`, Rebalance `pulse_fleet_enabled` false | WARN "collector in fleet mode, Rebalance not enrolled" | `rebalance config fleet-enroll` |
  | `pulse_fleet_enabled` true and `fleet_settings()` raises | FAIL with its message (covers `$` paths, path mismatch, device ID, `fleet_mode` off) | `rebalance config fleet-enroll --apply` |
  | `pulse_fleet_enabled` true and raw config has `pulse_filename` | WARN "pulse_filename ignored in fleet mode" | `rebalance config fleet-enroll --apply` |
  | neither side enrolled, collector installed | OK/notice "not enrolled in fleet mode" (muted; enrollment is opt-in) | `rebalance config fleet-enroll` |
  | enrolled and valid | OK `enrolled as <device_id> (<path>)` | — |

- **`rebalance config fleet-enroll [--apply]`** (`cli/config_cmds.py`):
  1. Read collector config; refuse if absent or `device_id` missing/unsafe (same regex as
     `fleet_settings`).
  2. Resolve the clone: collector `sync_repo_dir` with `~`/`$HOME` expanded to a literal absolute
     path; fall back to existing `pulse_target_path`; refuse if neither is a git repo or they
     resolve to different directories.
  3. Planned changes: collector `sync_repo_dir=<literal>` (only if it contained `$`/`~`),
     `fleet_mode=true`, `fleet_sync_subdir=<Rebalance sync_subdir>`; Rebalance
     `pulse_target_path=<literal>`, `pulse_device_id=<device_id>`, `pulse_fleet_enabled=true`,
     remove `pulse_filename`.
  4. Print the plan. Without `--apply`, exit 0 having written nothing. With `--apply`, write, then
     run `fleet_settings()` and print OK or the error. Re-running on an enrolled Mac is the repair
     path and is idempotent (no changes → "already enrolled").
  5. No dirty-clone check: enrollment writes no files inside the clone; dirt is the collector's
     concern at publish time (#314).
- **`rebalance config set-pulse --github-login X --target-path P [--timezone Z]`** (#246): validates
  `P` is a git repo, writes via `set_pulse_config()`. `_check_pulse()`'s missing-keys hint points
  at it.

## Docs

- **UPGRADE.md step 3** — resolve the clone from this Mac's config instead of a fixed folder.
  Text: "Use this Mac's existing clone of `rebalance-git-pulse` (`sync_repo_dir` in `~/.config/git-pulse/config.sh`).
  Only if there is none, clone it to a folder of your choice (`~/git-pulse-sync` is the example)."
  `--base-url` uses `<clone>/sync/sleuth/…`.
- **UPGRADE.md new section "Fleet self-repair (agent-run, every upgrade)"** — after the refresh
  steps: run `rebalance doctor`; for each `pulse`/`pulse fleet` row, run its hint. Rule: on a Mac
  already enrolled (`pulse_fleet_enabled` true) run `fleet-enroll --apply` without asking; on a Mac
  not yet enrolled run the preview and ask the operator, because SOP's per-Mac qualification gate
  applies. Never move or re-clone an existing clone.
- **SOP.md GH-282 section** — step 4 points at `fleet-enroll`; add the literal-path rule (no `$`,
  `~` is expanded by the helper, `sync_repo_dir` must equal `pulse_target_path`); add "Four-Mac
  rollout" (order: Studio done → Mac Mini → MacBook Pro 14" → MBP 16"; one Mac per day; gate each on
  doctor green + one delivered collector interval + SOP step 6 checks) and "Retire legacy shared
  pages" (after all four show fleet delivery for seven days per #282: remove root `live-pulse.md`
  and `live-pulse-<device>.md` from the pulse repo in one commit; keep `pulse-<id>.md`,
  `devices/<id>.yaml`; drop `pulse_filename` everywhere — already done by `fleet-enroll`).
- **SLEUTH_SYNC.md** — `~/git-pulse-sync` becomes "your clone (example: `~/git-pulse-sync`)".
- **`scripts/setup_sleuth_file_source.sh`** — default `CLONE_DIR` to the collector's `sync_repo_dir`
  when `~/.config/git-pulse/config.sh` sets one (literal read, no `source`), else `~/git-pulse-sync`.
- CHANGELOG entry.

## Implementation order (verification inline)

1. `lib/git_ops.py`: extract `read_collector_config()`, add `set_collector_values()`. Verify:
   existing `tests/test_pulse_health.py`, `tests/test_git_publication_contract.py` still pass.
2. `ingest/config.py`: `set_pulse_config(pulse_filename="")` deletes the key. Verify: new case in
   an existing config test file.
3. `doctor.py`: `_check_pulse_fleet()` + hint for missing keys. Verify: new cases in
   `tests/test_doctor_pulse_severity.py` — one per table row. **Red control:** the `$HOME` row and
   the not-enrolled row fail against the unmodified `_check_pulse()` (no fleet row emitted).
4. `cli/config_cmds.py`: `fleet-enroll`, `set-pulse`. Verify: tests with temp
   `GIT_PULSE_CONFIG_DIR` + temp git repo: preview writes nothing (file bytes unchanged); `--apply`
   on a `$HOME/...` `sync_repo_dir` yields a literal path and `fleet_settings()` passes; second
   `--apply` reports no changes; refusal on missing `device_id` writes nothing; refusal when path
   is not a git repo.
5. Docs (UPGRADE, SOP, SLEUTH_SYNC), setup script default, CHANGELOG, ROADMAP line.
6. Manual check on this Mac (Studio): `rebalance config fleet-enroll` preview against the live
   config shows only "remove `pulse_filename`" (Studio still sets it). Recorded under
   `TESTS-RESULTS/2026-10-13+GH-325/`. Not applied by this PR.
7. Gate: `ruff`, focused pytest files above, then the repo's full pre-push route once on the final
   commit.

## Risks

- A Mac whose `sync_repo_dir` and `pulse_target_path` point at *different* clones: the helper
  refuses and names both; the operator picks. No silent rebinding (AGENTS.md warns about rebinding a
  fleet to another clone).
- Doctor rows on Macs without the collector: none emitted.
- `set_collector_values()` writing a file `install.sh` also writes: backup first; only three keys.
