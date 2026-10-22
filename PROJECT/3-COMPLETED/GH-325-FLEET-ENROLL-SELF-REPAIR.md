---
gh_issue: 325
source: https://github.com/HiQS-Labs/rebalanceOS/issues/325
title: "Fleet enrollment: device-agnostic pulse clone path, enroll helper, doctor checks, self-repair on upgrade"
status: Completed
created: 2026-10-13
updated: 2026-10-21
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
| [#325](https://github.com/HiQS-Labs/rebalanceOS/issues/325) | items 1–6 below | `rebalanceOS-gh325-fleet-enroll-self-repair-2026-10-13` / `fix/rebalanceOS-gh325-fleet-enroll-self-repair-2026-10-13` | PR ready; awaiting merge | [#326](https://github.com/HiQS-Labs/rebalanceOS/pull/326) |
| [#246](https://github.com/HiQS-Labs/rebalanceOS/issues/246) | item 3 (same command) | same | PR ready; awaiting merge | [#326](https://github.com/HiQS-Labs/rebalanceOS/pull/326) |

Base: `origin/development` @ `0589b44`.

## Rating (2026-10-13)

`rated 65/55/50/55` (pri/sev/appeal/effort). Severity 55: no data loss; the consequence is that three
of four Macs cannot be enrolled without hand-editing two config files, and wrong docs send a Mac's
clone to a folder its config does not use — a Mac silently stays out of the fleet or `pulse-sync`
fails until someone notices. Priority 65: it blocks #282's four-Mac qualification, and the same
class (per-device config nobody owns or checks) is the #281 umbrella — #281 counted 17 issues in the
14 days to 2026-09-26; #277 and #302 are recent device-health instances. Trend over the last 14 days
versus the 14 before was not recounted here (unknown). Appeal 50 (neutral, no user value given).
Effort 55: one doctor check, two CLI verbs (`fleet-enroll`, `set-pulse`), docs, no schema change.

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
   `github_login`/`pulse_target_path`. Doctor reaches `fleet_settings()` only indirectly:
   `_check_pulse_collectors` → `_local_device_id` (`doctor.py:115-124`) → `sync_snapshot.get_device_id`
   (`sync_snapshot.py:66-68`), and on error emits a generic `fleet configuration` FAIL with no
   remedy (`doctor.py:1899-1902`). Nothing reports an installed-but-unenrolled Mac, and no row names
   a repair command. (Corrected in plan QA r2: the original "never calls" overstated silence.)
4. **`pulse_filename` silently ignored.** `pulse.py:963` uses `devices/<id>/live-pulse.md` in fleet
   mode. `get_pulse_config()` defaults `pulse_filename` to `live-pulse.md`, so "explicitly set" must
   be read from the raw config.
5. **Literal-path rule undocumented.** `fleet_settings()` (`lib/git_ops.py:33-77`) parses
   `config.sh` without shell evaluation. It substitutes `$CONFIG_DIR`/`${CONFIG_DIR}`, defaults an
   absent/empty `sync_repo_dir` to `<config_dir>/repo`, then rejects any *remaining* `$` — so
   `$HOME/...` fails — and requires the result to equal `pulse_target_path`. SOP step 4 says none
   of this. (Corrected in plan QA r1: the original "rejects any `$`" was too broad.)

## Outcome sought / smallest bet / non-goals

- **Outcome:** on each Mac's next upgrade, the agent following UPGRADE.md runs `rebalance doctor`,
  sees every fleet/pulse gap named with its repair command, runs it, and ends green — whatever the
  clone folder is called.
- **Build:** (a) one doctor check extension, (b) one CLI verb `rebalance config fleet-enroll`
  (preview by default, `--apply` writes) plus `rebalance config set-pulse` for #246,
  (c) doc changes in UPGRADE.md, SOP.md, SLEUTH_SYNC.md, and a config-derived default in the setup script.
- **Not built:** no auto-enrollment without confirmation (SOP keeps the per-Mac qualification gate);
  no shell evaluation of config (`$HOME`/`${HOME}`/`~` are expanded as literal tokens, like
  `$CONFIG_DIR` already is; anything else with `$` stays rejected); no moving anyone's clone; no deletion of legacy files in this PR (it is a
  documented, operator-run step in the private pulse repo); no change to `repair.py` (runtime git
  repair, unrelated); no #287 per-Mac state dir.
- **Alternative rejected:** docs-only fix (rewrite UPGRADE.md to say "use your path"). Rejected — the
  issue requires the next upgrade to *detect and repair* drift; without a doctor signal and a named
  command the agent has nothing deterministic to act on, and #246 stays open.
- **Rollback:** reverting the PR removes the code but does not undo config a Mac already applied.
  For that, the existing SOP GH-282 step 7 rollback applies (disable Python fleet mode only once the
  private checkout is clean and no fleet commits are unpushed), using the `config.sh.bak-gh325`
  backup the helper writes before its first change. The Rebalance keys it sets are the same ones
  SOP step 4 already sets by hand.

## Design

Existing subsystems extended, no new modules:

- **Collector config reader + one clone resolver** — split the literal `config.sh` parse already
  inside `fleet_settings()` into `read_collector_config()` and `collector_clone(values, config_dir)`
  in `lib/git_ops.py`. `collector_clone` keeps today's effective semantics exactly (absent/empty
  `sync_repo_dir` → `<config_dir>/repo`; `$CONFIG_DIR`/`${CONFIG_DIR}` substituted, `git_ops.py:73-75`)
  and adds literal `$HOME`/`${HOME}`/leading `~` expansion — no shell evaluation; any other remaining
  `$` is rejected. `fleet_settings()`, doctor, `fleet-enroll` and `--print-clone` all use it. One
  parser, one resolver. (Accepting `$HOME` in the resolver means the publisher stops rejecting it; the
  helper still writes the literal path so both readers agree byte-for-byte.)
- **Collector config writer** — `install.sh`'s `set_config_value` is bash inside an installer that
  also loads launchd, so it is not callable as a library. Add `set_collector_values()` next to the
  reader in `lib/git_ops.py`: replaces **every** assignment of a key (so a later duplicate cannot
  override), appends if absent, quotes with `shlex.quote` because `collect.sh:17` sources the file,
  preserves all other lines, backs up once to `config.sh.bak-gh325`. Used only by `fleet-enroll`.
  (Disclosed second writer, accepted in plan QA r1; the keys it touches — `fleet_mode`,
  `fleet_sync_subdir`, `sync_repo_dir` — are ones `install.sh` never sets after creation,
  `install.sh:265,272,289`.)
- **Rebalance config writer** — reuse `set_pulse_config()`. Add one capability: a way to remove
  `pulse_filename` (pass `pulse_filename=""` → key deleted), since fleet mode ignores it.
- **Doctor** — extend `_check_pulse()` into `_check_pulse()` + `_check_pulse_fleet()` (new rows
  named `pulse fleet`), added beside it at `doctor.py:2558`. Rows, each with its repair command as
  the hint:

  | Condition | Status | Hint |
  |---|---|---|
  | collector config absent **and** `pulse_fleet_enabled` false | no row (no collector, nothing to enroll) | — |
  | collector config absent **and** `pulse_fleet_enabled` true | FAIL "fleet enabled but collector config missing" | prerequisite, not the helper: `bash experimental/git-pulse/install.sh` (the helper refuses this state) |
  | collector installed, either side not enrolled (`fleet_mode` ≠ true or `pulse_fleet_enabled` false) | WARN "this Mac is not enrolled in fleet mode" | `rebalance config fleet-enroll` (preview) |
  | `pulse_fleet_enabled` true and `fleet_settings()` raises | FAIL with its message (unresolved `$` expression, path mismatch, device ID, `fleet_mode` off, unsafe `sync_subdir`) | `rebalance config fleet-enroll --apply` |
  | `pulse_fleet_enabled` true and raw config has `pulse_filename` | WARN "pulse_filename ignored in fleet mode" | `rebalance config fleet-enroll --apply` |
  | enrolled and valid | OK `enrolled as <device_id> (<path>)` | — |

- **`rebalance config fleet-enroll [--apply]`** (`cli/config_cmds.py`):
  1. Read collector config; refuse if absent or `device_id` missing/unsafe (same regex as
     `fleet_settings`).
  2. Resolve the clone. Let `C` = `collector_clone()` (effective collector clone) and `P` =
     existing `pulse_target_path`. If both exist as git repos and differ → refuse, print both,
     write nothing. Otherwise the chosen clone is whichever is a git repo (`C` preferred); refuse
     if neither is.
  3. Planned changes: collector `sync_repo_dir=<chosen literal>` whenever the stored value is not
     already that literal string, `fleet_mode=true`, `fleet_sync_subdir=<Rebalance sync_subdir>`;
     Rebalance `pulse_target_path=<chosen literal>`, `pulse_device_id=<device_id>`,
     `pulse_fleet_enabled=true`, remove `pulse_filename`.
  4. **Validate before writing:** run `fleet_settings()` against the proposed collector values and
     proposed Rebalance config in memory (covers unsafe `sync_subdir`, device ID, path equality).
     Any failure → refuse, print the reason, write nothing.
  5. Print the plan. Without `--apply`, exit 0 having written nothing. With `--apply`, write the
     collector file then Rebalance config, then run `fleet_settings()` again and print OK. Re-running
     on an enrolled Mac is the repair path; with nothing to change it prints "already enrolled" and
     leaves both files byte-identical.
  6. `--print-clone`: print-only discovery, independent of enrollment eligibility (no device-ID
     requirement, writes nothing). Same resolver and conflict check as step 2. Exit codes:
     - **2 — invalid or ambiguous:** collector config unparseable, an unresolved `$` expression, or
       `C` and `P` both existing git repos that differ. Message names the values. Callers **stop**.
     - **0 — resolved:** prints `C` if it is a git repo, else `P` if it is; if neither exists yet,
       prints `P` when set, else `C` when the collector sets an explicit `sync_repo_dir` (a
       configured-but-not-yet-cloned path; callers may clone there).
     - **3 — nothing configured:** no collector config (or no explicit `sync_repo_dir`) and no `P`.
       Only this code allows the first-install fallback to a folder the operator chooses.
     Used by UPGRADE.md step 3 and `setup_sleuth_file_source.sh`, so nothing hardcodes a folder.
  7. No dirty-clone check: enrollment writes no files inside the clone; dirt is the collector's
     concern at publish time (#314).
- **`rebalance config set-pulse --github-login X --target-path P [--timezone Z]`** (#246): validates
  `P` is a git repo, writes via `set_pulse_config()`. `_check_pulse()`'s missing-keys hint points
  at it.

## Docs

- **UPGRADE.md step 3** — resolve the clone from this Mac's config instead of a fixed folder:
  `CLONE="$(.venv/bin/rebalance config fleet-enroll --print-clone)"`. Exit 0 → use it (clone there
  if it does not exist yet). Exit 3 (nothing configured) → ask the operator for a folder
  (`~/git-pulse-sync` is the example), clone, record it with `set-pulse --target-path`. Exit 2 →
  stop and report; do not clone or change Sleuth. `--base-url` uses `"$CLONE/sync/sleuth/…"`.
- **UPGRADE.md new section "Fleet self-repair (agent-run, every upgrade)"** — a bounded procedure,
  run once after the refresh steps:
  1. Run `rebalance doctor`. Act only on `pulse` / `pulse fleet` rows that are WARN or FAIL; OK rows
     have nothing to do.
  2. `pulse` missing keys → ask the operator for `github_login` / clone path; never guess them; run
     `set-pulse` with the answers.
  3. `pulse fleet` FAIL "collector config missing" → stop and report: run the collector installer
     first. The helper cannot fix it.
  4. Mac already enrolled (`pulse_fleet_enabled` true) with a WARN/FAIL → run
     `fleet-enroll --apply` **once**, without asking.
  5. Mac not enrolled (WARN "not enrolled") → run `fleet-enroll` (preview), show it, and apply only
     on the operator's yes (SOP per-Mac qualification gate).
  6. Re-run `rebalance doctor` once. If a `pulse`/`pulse fleet` row is still WARN/FAIL, or the
     helper refused (for example two different clones), stop and report the exact row and values.
     Do not retry, loop, pick a clone, or move/re-clone anything.
- **SOP.md GH-282 section** — step 4 points at `fleet-enroll`; add the literal-path rule (only
  `$CONFIG_DIR`, `$HOME`, `${…}` forms of those, and a leading `~` are expanded, as literal tokens;
  any other `$` is rejected; the result must equal `pulse_target_path`; the helper writes the
  resolved literal path); add "Four-Mac
  rollout" (order: Studio done → Mac Mini → MacBook Pro 14" → MBP 16"; one Mac per day; gate each on
  doctor green + one delivered collector interval + SOP step 6 checks) and "Retire legacy shared
  pages" (after all four show fleet delivery for seven days per #282: remove root `live-pulse.md`
  and `live-pulse-<device>.md` from the pulse repo in one commit; keep `pulse-<id>.md`,
  `devices/<id>.yaml`; drop `pulse_filename` everywhere — already done by `fleet-enroll`).
- **SLEUTH_SYNC.md** — `~/git-pulse-sync` becomes "your clone (example: `~/git-pulse-sync`)".
- **`scripts/setup_sleuth_file_source.sh`** — default `CLONE_DIR` to the output of
  `rebalance config fleet-enroll --print-clone` (same resolver as the publisher, so no literal
  variable text reaches `git clone`). Exit 3 only → fall back to `~/git-pulse-sync`; exit 2 → exit
  non-zero with the message before any clone, pull or Sleuth write. An explicit `--clone-dir`
  skips discovery and still overrides.
- CHANGELOG entry.

## Implementation order (verification inline)

1. `lib/git_ops.py`: extract `read_collector_config()` + `collector_clone()`, add
   `set_collector_values()`. Verify: existing `tests/test_pulse_health.py`,
   `tests/test_git_publication_contract.py` still pass; new cases for `collector_clone` covering
   absent/empty → `<config_dir>/repo`, `$CONFIG_DIR/repo`, `${CONFIG_DIR}/repo`, `$HOME/x`, `~/x`
   (resolve) and `$OTHER/x` (rejected); `set_collector_values` replaces duplicate assignments.
2. `ingest/config.py`: `set_pulse_config(pulse_filename="")` deletes the key. Verify: new case in
   an existing config test file.
3. `doctor.py`: `_check_pulse_fleet()` + `set-pulse` hint for missing keys. Verify: new cases in
   `tests/test_doctor_pulse_severity.py` — one per table row, asserting status **and** hint through
   the same public `run_doctor`/report path. **Red controls** against base `0589b44`'s doctor, same
   inputs, evidence in `TESTS-RESULTS/2026-10-13+GH-325/`: (a) installed-but-unenrolled collector →
   base report has no WARN/FAIL naming enrollment; (b) fleet enabled, collector config missing →
   base emits the generic `fleet configuration` FAIL (recorded as-is, not suppressed) but no
   installer remedy; candidate emits the actionable row. The existing generic FAIL is kept.
4. `cli/config_cmds.py`: `fleet-enroll`, `set-pulse`. Verify (temp `GIT_PULSE_CONFIG_DIR` + temp git
   repos): preview writes nothing (bytes unchanged); `--apply` on `$HOME/...` writes a literal path
   and `fleet_settings()` passes; empty `sync_repo_dir` with `pulse_target_path` elsewhere → writes an
   explicit literal so both readers agree; existing valid `$CONFIG_DIR/repo` → accepted; two
   different existing clones → refuse, bytes unchanged; unsafe `sync_subdir` → refuse before any
   write; missing `device_id` → refuse, no write; second `--apply` → "already enrolled", both files
   byte-identical; `--print-clone` → 0 with `P` when the collector is absent (no device ID needed),
   2 on conflicting clones and on `$OTHER/repo`, 3 when nothing is configured.
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
- Doctor rows on Macs without the collector and without fleet enabled: none emitted.
- `fleet_settings()` now accepts `$HOME`/`${HOME}` (literal-token expansion; `~` already passed via
  `Path.expanduser()`). Identity, subdirectory and path-equality checks are unchanged. Every caller
  (`pulse.py`, `index_ops.py:2152`, `sync_snapshot.py:66`) gains that acceptance; none loses one.

## Plan QA log

- r1 (Codex, 2026-10-13, `TESTS-RESULTS/2026-10-13+GH-325/QA/gh325-plan-codex.md`): 3 Should + 1
  Nit, all **accepted**. (1) doctor now WARNs on installed-but-unenrolled and FAILs on
  fleet-enabled-without-collector with an installer hint; (2) one effective clone resolver shared by
  publisher, doctor, helper and setup script, full validation before the first write, duplicate-key
  safe writer; (3) UPGRADE self-repair is a bounded once-then-recheck-then-stop procedure. Nit: two
  CLI verbs. Rollback now names SOP step 7 for applied config. Driver exit 3 (reviewer did not hand
  the token back); verdict was written and committed, so treated as a completed changes-requested round.
- r2 (Codex): 2 Should + 1 Nit, all **accepted**. (1) `--print-clone` is print-only with exit
  0/2/3 distinguishing resolved / invalid-or-ambiguous / nothing-configured; both callers stop on 2
  and fall back only on 3. (2) Recon corrected: doctor already reaches `fleet_settings` via
  `_local_device_id` and emits a generic FAIL; red control (b) now asserts the missing remedy, not
  total silence. Nit: `~` was already accepted. Driver exit 3 again (token not handed back).
- `set_collector_values()` writing a file `install.sh` also writes: backup first; only three keys.
