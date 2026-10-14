---
Goal: Plan QA for GH-325 (fleet enrollment, doctor checks, self-repair on upgrade)
Date: 2026-10-13
NEXT: claude-a
STATUS: Open
---

# Context

Review the plan in `PROJECT/1-INBOX/GH-325-FLEET-ENROLL-SELF-REPAIR.md` before any code is written.
Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/325 (also closes #246).

**Operational envelope:** a single operator's four personal Macs, each running a local Python CLI
(`rebalance`) and a bash collector (`experimental/git-pulse/collect.sh`). Config files are local and
owned by that operator. Grade against the stated requirements and commensurate complexity — do not
demand multi-tenant, distributed-locking or enterprise recovery machinery.

**Operator requirements (verbatim intent):**
1. The upgrade path must be agnostic to each Mac's pulse clone folder name. `UPGRADE.md:144-149`
   hardcodes `~/git-pulse-sync`; Mac Mini's clone is `~/Documents/GitHub/rebalance-git-pulse`.
2. A rollout plan for fleet mode across all four Macs and a retirement plan for old files.
3. An enroll helper, and doctor must warn when a Mac is not enrolled.
4. `pulse_filename` must not be silently ignored once fleet mode is on.
5. Document that `$HOME` paths are rejected in the pulse clone path.
6. Fixes must be durable and self-repair via AI orchestration on the next upgrade install
   (the agent running UPGRADE.md). Operator decision: drift is auto-repaired; enrolling a Mac that is
   not yet enrolled previews and asks first.

Read the plan in full, then these sources it cites:
- `UPGRADE.md` (lines 100-170), `SLEUTH_SYNC.md`, `SOP.md` § "GH-282 — fleet delivery deployment and lessons" (~line 317)
- `scripts/setup_sleuth_file_source.sh`
- `src/rebalance/lib/git_ops.py` (`fleet_settings`, `fleet_output_path`, lines 25-90, and ~505-520)
- `src/rebalance/ingest/config.py` (`get_pulse_config`, `set_pulse_config`, ~1323-1400)
- `src/rebalance/ingest/pulse.py` (~955-970, 1045-1100)
- `src/rebalance/doctor.py` (`_check_pulse` ~2155, `_check_pulse_collectors` ~1885, call sites ~2558-2567)
- `src/rebalance/cli/config_cmds.py` (`set-sleuth` ~482 as the CLI pattern)
- `experimental/git-pulse/install.sh` (`set_config_value` ~56) and `collect.sh` (fleet_mode ~20, 537-540, 735)
- `tests/test_doctor_pulse_severity.py`, `tests/test_pulse_health.py`

Questions:

1. Are the plan's factual claims about current behaviour correct? Check each cited file:line.
   In particular: does `fleet_settings()` reject `$` in `sync_repo_dir`, and does doctor today
   ever call it?
2. Is any of the six requirements missing or only partly covered? Is the UPGRADE.md self-repair
   step concrete enough for an agent to execute deterministically?
3. Does the plan extend existing code rather than build a parallel system? Judge specifically the
   new `set_collector_values()` writer next to `install.sh`'s `set_config_value` — is the disclosed
   second writer justified, or is there a simpler existing path?
4. Is the retirement scope right? The plan retires only root `live-pulse.md` and
   `live-pulse-<device>.md`, and keeps `pulse-<id>.md` / `devices/<id>.yaml` because the collector
   still writes them in fleet mode. Is that correct per `collect.sh`?
5. Are the doctor rows' severities sensible (WARN vs FAIL vs muted notice), and is the red control
   (new rows absent on the unmodified `_check_pulse`) a real falsifier?
6. Is `fleet-enroll --apply` safe when `sync_repo_dir` and `pulse_target_path` disagree, and
   idempotent on a re-run?
7. Is the rating `65/55/50/55` grounded in the evidence given? Appeal must stay 50 (no user value).
8. Flag anything over-engineered or that could be cut.

You may run narrow read-only probes (output under `.relay-scratch/` or `$TMPDIR`); do not run
pytest or test suites. Every [Blocker]/[Should] asking for a behaviour change must carry
`Observed input:`, `Affected scope:` and `Falsifier:` lines. Cite file:line.

Write your verdict below. Set STATUS to Approved if the plan can proceed as written (minor Nits
allowed); otherwise leave it Open with your findings and hand back.

<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->
▶ TAKE YOUR TURN (codex)
<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->


## Codex review — round 1 (2026-10-13)

**Verdict: Block pending the three bounded plan corrections below. STATUS remains Open.**
This is source-based plan QA, not implementation or live fleet qualification. All plan line
references below mean `PROJECT/1-INBOX/GH-325-FLEET-ENROLL-SELF-REPAIR.md`.

### [Should] 1. Make doctor expose missing enrollment and missing collector configuration

Plan lines 117–121 suppress the row whenever collector config is absent and grade a configured
but wholly unenrolled Mac OK/notice. The latter does not satisfy requirement 3 (“doctor must warn
when a Mac is not enrolled”). The former also hides a broken *enrolled* producer:
`src/rebalance/lib/git_ops.py:42–53` reads the collector file when fleet is enabled, and
`src/rebalance/ingest/pulse.py:1051–1054` returns failure if that file cannot be read. Ordinary
`_check_pulse` can still return OK for the same valid target (`src/rebalance/doctor.py:2155–2196`).

Observed input: (a) installed collector, both fleet flags false; (b) valid publisher target and
`pulse_fleet_enabled=true`, but collector config missing.
Affected scope: enrollment visibility and the every-upgrade detection/repair loop on these Macs.
Falsifier: doctor emits WARN plus preview hint for (a), and FAIL plus an actionable missing-config
remediation for (b), while an unconfigured installation without the collector remains quiet.

Cheapest correction: qualify the absent-config suppression with fleet disabled; use WARN for an
installed but unenrolled device. Keep enrollment confirmation separate from diagnostic severity.
A missing config cannot be repaired by the proposed helper, which explicitly refuses it; its hint
must name the prerequisite instead of repeatedly suggesting `fleet-enroll --apply`.

### [Should] 2. Define one effective clone resolution before any config write

The “rejects any `$`” factual claim (plan lines 71–73) is too broad:
`src/rebalance/lib/git_ops.py:73–75` first substitutes `$CONFIG_DIR` and `${CONFIG_DIR}`, and
uses `<config-directory>/repo` when `sync_repo_dir` is absent/empty. Only a remaining `$` is
rejected. The helper specifies only `~`/`$HOME` expansion (lines 127–129). It also falls back to
`pulse_target_path` but writes collector `sync_repo_dir` **only** if it contained `$`/`~`
(lines 130–133). Thus an absent/empty value can remain absent/empty while the Python target is
set to a different repo; the final validation then fails after enrollment keys were written.
The setup-script default (lines 162–163) needs the same effective-path semantics rather than
passing literal variable text to its clone command.

Observed input: safe device ID, empty `sync_repo_dir`, valid `pulse_target_path=/chosen/clone`
with `/chosen/clone` different from `<config-directory>/repo`; also an already valid
`sync_repo_dir="$CONFIG_DIR/repo"` configuration.
Affected scope: enrollment fallback, rerun compatibility, and device-agnostic Sleuth setup.
Falsifier: preview resolves the existing supported CONFIG_DIR forms correctly; absent/empty
values either produce a validated explicit collector assignment or refuse without writes when
an existing effective collector clone conflicts. Apply converges both readers on the same repo,
and a second apply leaves bytes unchanged. Different existing clones always refuse unchanged.

Cheapest correction: preserve the existing effective default and CONFIG_DIR substitutions,
explicitly handle `$HOME`/`${HOME}` without shell evaluation, reject unresolved expressions,
and write the resolved literal whenever the stored collector value would not resolve to the
chosen target. Validate the whole proposed configuration, including `sync_subdir`, before the
first write (currently validation is only after writes, lines 134–135). No new resolver framework
or transaction service is needed.

### [Should] 3. Close the upgrade repair loop with a bounded failure branch

Plan lines 149–153 say to run each hint, but do not specify rechecking or what happens when an
auto-repair refuses. The plan itself anticipates conflicting clones (lines 189–191), and
`fleet_settings` also rejects unsafe subdirectories (`src/rebalance/lib/git_ops.py:65–72`),
which copying the same Rebalance value into the collector cannot repair. “For each row, run its
hint” also includes OK rows with no hint, while `set-pulse` requires values not derivable from a
bare command name (plan lines 139–141).

Observed input: enrolled Mac with conflicting existing clone paths, or unsafe `sync_subdir`;
doctor suggests enrollment repair and that repair cannot converge.
Affected scope: requirement 6, deterministic AI orchestration on every upgrade.
Falsifier: the documented procedure attempts automatic repair once for an enrolled Mac, reruns
doctor after success, and stops with the exact unresolved values/prerequisite on refusal or a
remaining failure. It never invents a clone choice or loops. New enrollment still previews and
asks first; missing required set-pulse values are obtained explicitly rather than guessed.

Cheapest correction: add those branches and a final doctor recheck to the existing upgrade
paragraph. No scheduler, daemon, or general repair engine is warranted.

### Answers to the remaining review questions

- **Current behavior:** the hardcoded paths are present in UPGRADE step 3, SLEUTH_SYNC and the
  setup script. `_check_pulse` validates the two required keys and target existence/git marker;
  it does not call `fleet_settings`. The bounded source search found no direct call in doctor.
  Publisher validation is not exclusive to pulse-sync: `ingest/index_ops.py:2152–2156` and
  `ingest/sync_snapshot.py:66–68` also use it. `set_pulse_config` has no executable caller under
  `src/rebalance` in this seed. Fleet publication ignores `pulse_filename` as claimed
  (`ingest/pulse.py:962–963`); raw config is the right way to detect explicit presence.
- **Reuse / second writer:** justified for this scope. `install.sh:56–85` is embedded in a
  side-effecting installer; its calls at 265, 272 and 289 update identity/name/discovery, not
  the helper's three keys. Invoking the installer solely to edit config would be worse. Keep
  the new writer narrowly scoped, preserve unrelated lines, and correctly quote literal shell
  values because `collect.sh:17` sources the file. Do not blindly inherit first-match-only
  replacement semantics if duplicate assignments would leave a later overriding value.
- **Retirement:** correct narrow scope. `collect.sh:537–540` selects the root pulse and device
  YAML paths regardless of fleet mode, and lines 735–745 still stage them before adding the
  fleet namespace. The rollout order, per-Mac delivery gate and seven-day retention cover
  requirement 2. Existing SOP rollback conditions still apply; “revert the PR” alone does not
  undo applied local config (plan lines 91–93).
- **Severity / red control:** FAIL for enabled-but-invalid publication and WARN for an ignored
  explicit filename are sensible. Fix finding 1's exceptions. The red control is meaningful if
  it invokes the same public doctor/report path on base and candidate and asserts the diagnostic
  status and remedy for the same input. An import failure for the new helper or a row-name-only
  assertion is not behavioral proof. Existing severity tests cover collector health, not these
  enrollment contracts. **[Unverified — needs clone run]** all proposed tests, red controls,
  apply/idempotency behavior and live delivery; none was executed during this relay turn.
- **Mismatch safety / idempotence:** explicit refusal when both configured clones differ is
  sound. Add that refusal to the existing CLI verification cases (plan lines 175–179); finding 2
  identifies the missing fallback contract. Idempotence is an acceptance condition, not yet a
  measured property.
- **Rating:** 65/55/50/55 is reasonable as a planning judgment given the stated four-Mac rollout
  dependency and lack of data loss. Appeal stays 50. The historical issue count and actual
  three-Mac state were not independently verified here; the acknowledged unknown trend must  [Unverified — no citation]
  stay unknown. Nit: effort prose says “one CLI verb” although two are planned.
- **Complexity:** no need for a new module, distributed lock, enrollment FSM, background repair
  or extra test suite. Extend existing checks and keep the disclosed local writer bounded.

### Evidence and review limits

Read the full plan, cited source sections, SOP and architecture documentation; used the SWE
review rubric. Graph discovery was attempted first: `list_projects` had no entry for this relay
checkout. The related `rebalanceOS` index is a different checkout, generation
`2026-09-02T03:54:57Z`; coverage reported metadata changes on eight of nine queried source paths.
Its results were provisional only, and the cited claims above use the seeded source directly.
No index was created or refreshed.

Read-only source check command:
`rg -n 'fleet_settings|set_pulse_config' src/rebalance/doctor.py src/rebalance`
Exit status: 0. Decisive output included `lib/git_ops.py:33:def fleet_settings`,
`ingest/config.py:1381:def set_pulse_config`, publication/snapshot/index_ops callers, and no
`doctor.py` match. Direct reading of `_check_pulse` and its call site at doctor.py:2558 supplied
positive corroboration. This is static source evidence, not a live execution claim.

No test suite, executable fixture, live config mutation, or git command was run. Only this relay
file was edited; scratch setup was confined to `.relay-scratch/tmp`.

## Producer response — round 1 dispositions (2026-10-13)

All findings accepted; plan revised in `PROJECT/1-INBOX/GH-325-FLEET-ENROLL-SELF-REPAIR.md`
(see its "Plan QA log").

- **[Should] 1 — Accepted.** Doctor table now: no collector + fleet off → no row; collector config
  missing + fleet on → FAIL with installer prerequisite hint (not the helper); installed but either
  side unenrolled → WARN with preview hint.
- **[Should] 2 — Accepted.** One resolver `collector_clone()` keeps today's effective semantics
  (empty → `<config_dir>/repo`, `$CONFIG_DIR`/`${CONFIG_DIR}`) and adds literal `$HOME`/`${HOME}`/`~`;
  other `$` rejected. Shared by `fleet_settings`, doctor, `fleet-enroll` and `--print-clone` (used by
  UPGRADE and the setup script). Helper writes the literal whenever the stored value differs,
  validates the whole proposed config in memory before the first write, refuses on two different
  existing clones. Writer replaces duplicate assignments and quotes with `shlex.quote`.
- **[Should] 3 — Accepted.** UPGRADE self-repair is a six-step bounded procedure: act only on
  WARN/FAIL rows; ask for unknowable `set-pulse` values; stop on missing collector; enrolled Mac →
  `--apply` once; unenrolled → preview + ask; one doctor recheck, then stop and report. No loop.
- **Nit — Accepted.** "two CLI verbs". Rollback now cites SOP step 7 + the config backup.

Round 2 questions: are the three corrections sufficient and correctly specified? Does accepting
`$HOME`/`~` in `fleet_settings()` (literal-token expansion) introduce any regression for its callers
(`pulse.py`, `index_ops.py:2152`, `sync_snapshot.py:66`)? Anything new over-engineered?
Set STATUS to Approved if the plan can proceed.

<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->
▶ TAKE YOUR TURN (codex)
<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->


## Codex review — round 2 (2026-10-13)

**Verdict: Block pending two bounded specification corrections. STATUS remains Open.**
The three prior findings are addressed in the main enrollment path: plan lines 127–151
specify visibility, effective clone selection, validation before writes and byte-stable reruns;
lines 167–181 specify a bounded repair/recheck procedure. Two seams still need correction.
All plan references below refer to `PROJECT/1-INBOX/GH-325-FLEET-ENROLL-SELF-REPAIR.md`.

### [Should] 1. Distinguish missing configuration from resolution failure in clone discovery

Plan lines 152–154 specify `--print-clone` as “C, else P”, without explicitly carrying over
lines 137–140's conflicting-clone refusal or bypassing enrollment's device-ID prerequisite.
Lines 164–166 equate refusal with “no clone configured anywhere”; lines 192–195 fall back to
`~/git-pulse-sync` on any refusal. A parse error, unresolved expression, or conflicting pair
is not proof that no clone is configured. The existing setup script then clones or pulls at
the selected path and writes the Sleuth source (`scripts/setup_sleuth_file_source.sh:48–73`).
That fallback can recreate the wrong-folder behavior this task is intended to eliminate.

Observed input: collector `sync_repo_dir="$OTHER/repo"` and an existing configured publisher
clone; alternatively two distinct existing C/P clones, or no collector file with valid P.
Affected scope: UPGRADE step 3 and the Sleuth setup script's automatic clone selection.
Falsifier: print-only discovery returns P when the collector is absent without requiring an
identity; conflicting clones or malformed configuration stop both callers without cloning,
pulling or changing the source; only a distinct no-configured-clone result permits the
explicit first-install fallback. An explicit `--clone-dir` remains usable.

Cheapest correction: define print-only resolution independently of enrollment eligibility,
reuse the same conflict check, and distinguish absence from invalid/ambiguous configuration
with a documented exit status. Both callers must branch on that distinction. No new framework.

### [Should] 2. Correct the doctor baseline and red-control expectation

I correct my round-1 inference: no direct `fleet_settings` reference in doctor does **not**
mean doctor never reaches it. `doctor.py:115–124` calls `sync_snapshot.get_device_id`, which
calls `fleet_settings` at `sync_snapshot.py:66–68`. `_check_pulse_collectors` invokes that
identity helper and already emits `Check("fleet configuration", FAIL, str(exc))` on
ValueError/OSError (`doctor.py:1899–1902`), provided the health read reaches that branch.
The public report invokes this check at `doctor.py:2567`.

Thus plan lines 64–68 overstate silence, and lines 209–212 cannot require the base public
report to have no WARN/FAIL for fleet-enabled/missing-config input. The proposed change still
adds value: actionable remediation, reliable detection, and unenrolled-device visibility.

Observed input: `pulse_fleet_enabled=true`, valid publisher target, missing collector config,
with the existing collector-health read returning normally (an empty list suffices).
Affected scope: baseline factual claim and the missing-config red control through run_doctor.
Falsifier: on base, record the existing generic fleet-configuration FAIL when this branch is
reached; demonstrate the candidate's missing-config installer remedy is absent on base.
Keep the separate installed-but-unenrolled control for the missing enrollment warning.

Cheapest correction: qualify the recon claim and assert the new actionable diagnostic contract,
not total absence of a failure. Do not suppress the existing failure to manufacture red evidence.

Static source inspection command (exit 0):
`rg -n -A 14 '^def _local_device_id' src/rebalance/doctor.py`
Decisive output: line 122 imports `get_device_id` from `rebalance.ingest.sync_snapshot`;
line 124 returns `get_device_id().removesuffix("-local")`. Direct source reads above establish
the downstream validation and its exception handler. This is a static call-path finding,
not a claim that the full report was executed.

### Remaining round-2 answers and limits

- The shared small resolver is justified by its concrete callers. Literal `$HOME` expansion
  can extend acceptance without changing the fleet return shape, identity checks, subdirectory
  checks or path equality. Those invariants must remain. `~` already passes through
  `Path.expanduser()` in current `git_ops.py:75`; describing it as newly accepted is a Nit.
  Publication, snapshot identity and sync export consume the same validated device/subdirectory
  result (`pulse.py:1051–1054`, `sync_snapshot.py:66–68`, `index_ops.py:2152–2156`). No caller
  regression is demonstrated by the plan alone; preserve literal-token boundaries and do not
  introduce shell evaluation. Config normalization on apply remains useful.
- The narrowly scoped second writer, pre-write validation, duplicate replacement and backup
  are proportionate for four personal Macs. No transaction service or extra subsystem is needed.
- Retirement scope, ignored-filename visibility, rollout gates and rating remain acceptable.
  Appeal remains 50; historical counts and fleet rollout state remain unverified here.
- **[Unverified — needs clone run]** implementation behavior, resolver compatibility, full doctor
  red controls, idempotence and live delivery. No test suite or executable fixture was run.
- Used the SWE review rubric and direct seeded-source review. Graph project enumeration was
  fully paginated (84 entries); this checkout has no index. Related `rebalanceOS` generation
  `2026-09-02T03:54:57Z` is a different checkout. Coverage for the seven relevant paths reported
  changed metadata on six and excluded `scripts/` on one; direct source was used instead.
  No graph refresh, git command, live configuration change or source edit was performed.
  Only this relay file was edited; scratch setup was confined to `.relay-scratch/tmp`.
