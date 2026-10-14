---
Goal: Final QA for GH-325 implementation (fleet enrollment, doctor rows, self-repair on upgrade)
Date: 2026-10-13
NEXT: done
STATUS: Approved
---

# Context

Review the committed implementation on this branch against its approved plan before a PR is opened.
Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/325 (also closes #246).

**Operational envelope:** one operator's four personal Macs; a local Python CLI plus a bash
collector; local config files. Grade against the approved plan and stated requirements with
commensurate complexity. Do not ask for multi-tenant, locking or recovery machinery. This repo
permits new tests.

Read in full:
- Plan (approved after 3 Codex rounds): `PROJECT/2-WORKING/GH-325-FLEET-ENROLL-SELF-REPAIR.md`
- Plan QA thread: `TESTS-RESULTS/2026-10-13+GH-325/QA/gh325-plan-codex.md`
- Evidence: `TESTS-RESULTS/2026-10-13+GH-325/SUMMARY.md` and the red-control `.py`/`.jsonl` files

The diff is `git diff 0589b44..HEAD`. Code: `src/rebalance/lib/git_ops.py`,
`src/rebalance/ingest/config.py`, `src/rebalance/doctor.py`, `src/rebalance/cli/config_cmds.py`,
`tests/test_fleet_enroll.py`. Docs/script: `UPGRADE.md`, `SOP.md`, `SLEUTH_SYNC.md`,
`scripts/setup_sleuth_file_source.sh`, `CHANGELOG.md`; version 0.99.0.

Requirement → acceptance map:
1. Clone folder agnostic per Mac → `--print-clone` (0/2/3) used by UPGRADE step 3, SLEUTH_SYNC and the setup script.
2. Rollout + retirement → SOP "Four-Mac rollout" and "Retire legacy shared pages".
3. Enroll helper + doctor warns when not enrolled → `fleet-enroll`, `set-pulse`, `_check_pulse_fleet`.
4. `pulse_filename` not silently ignored → `pulse fleet filename` WARN; `fleet-enroll` removes it.
5. `$HOME` rule documented → resolver accepts `$HOME`/`~`, SOP "Clone path rule".
6. Durable self-repair on upgrade → UPGRADE "Fleet self-repair" bounded procedure.

Questions:

1. Is each of the six requirements satisfied by the actual code and docs? Cite file:line.
2. Do the code paths match the approved plan (doctor table rows and hints, `--print-clone` exit
   semantics, validate-before-write, refusal on two clones, idempotent rerun, duplicate-safe
   writer)? Any deviation?
3. Did a duplicate subsystem or second writer slip in beyond the disclosed `set_collector_values`?
   (A third, pre-existing parser in `pulse_health.resolve_sync_repo_dir` was deliberately left
   alone and parked — judge whether that is acceptable.)
4. Do the tests and red controls substantiate the claims in SUMMARY.md? Is the red control a real
   falsifier through the public `run_doctor` path?
5. Behaviour change check: `fleet_settings()` now accepts `$HOME`/`${HOME}`. Any caller regression
   (`pulse.py`, `index_ops.py`, `sync_snapshot.py`, doctor `_local_device_id`)?
6. Is the UPGRADE self-repair procedure executable by an agent without guessing, and bounded?
7. Is the rating `65/55/50/55` still consistent with the delivered scope? Appeal stays 50.
8. Anything over-engineered to cut, or a bug a user would hit?

You may run narrow read-only probes (output under `.relay-scratch/` or `$TMPDIR`); do not run
pytest or test suites. Every [Blocker]/[Should] asking for a behaviour change must carry
`Observed input:`, `Affected scope:` and `Falsifier:` lines. Cite file:line.

Write your verdict below. Set STATUS to Approved if the implementation can ship as a PR (Nits
allowed); otherwise leave it Open with findings and hand back.

<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->
▶ TAKE YOUR TURN (codex)
<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->


## Codex final review — round 1 (2026-10-13)

**Verdict: Ship as a PR, with the nits and verification limits below. STATUS: Approved.**
No blocking implementation defect found in the reviewed scope. This is approval for PR
preparation, not fleet deployment qualification or an attestation that the pending harness passed.

### Requirement and plan coverage

1. **Clone-folder independence:** `src/rebalance/lib/git_ops.py:118` centralizes discovery;
   `src/rebalance/cli/config_cmds.py:527` implements print-only 0/2/3 results before identity or
   enrollment checks. Existing collector clone wins, then existing publisher clone; two different
   existing clones refuse (`git_ops.py:135`). Configured future paths and no-config results are
   distinct (`git_ops.py:149`). UPGRADE step 3 (`UPGRADE.md:144`), Sleuth instructions
   (`SLEUTH_SYNC.md:44`) and script discovery (`scripts/setup_sleuth_file_source.sh:41`) use it.
   The script stops on every nonzero result except 3 before clone/pull/config writes; an explicit
   clone argument bypasses discovery.
2. **Rollout and retirement:** `SOP.md:361` specifies order, one Mac per day, operator approval,
   doctor/delivery checks and the existing qualification gate. `SOP.md:375` delays retirement
   until seven delivered days on all four Macs and retains collector pages, device YAML,
   device directories and snapshots. This implements a procedure, not a claim of completed rollout.
3. **Enrollment and diagnostics:** CLI entry points are at `config_cmds.py:482` and `:503`;
   `_check_pulse_fleet` is wired into the public report at `doctor.py:2623`. Missing collector
   with fleet off is silent; with fleet on it names the installer; unenrolled installations WARN;
   invalid enabled settings FAIL with a repair hint; valid enrollment is OK (`doctor.py:2212`).
   Enabled Python with collector fleet mode off yields the invalid-enrollment FAIL, appropriately
   selecting repair rather than first-enrollment approval. The plan's overlapping table rows are
   resolved sensibly here.
4. **Ignored filename:** raw presence is retained at `ingest/config.py:1355`, independently of the
   default filename. Doctor emits the filename WARN (`doctor.py:2252`), and enrollment removes the
   key through the existing writer (`git_ops.py:179`, `ingest/config.py:1406`).
5. **Path rule:** `SOP.md:343` accurately describes the approved change from rejecting HOME to
   literal HOME/CONFIG_DIR expansion. `git_ops.py:68` preserves the effective default, recognizes
   variable boundaries, expands tilde and rejects remaining dollar expressions without evaluation.
6. **Durable upgrade repair:** `UPGRADE.md:189` is an actionable, bounded agent procedure: ask for
   unknown values, stop on a missing collector, repair an enrolled Mac once, preview and obtain
   approval for new enrollment, recheck once and report unresolved rows without choosing a clone.

The proposed state is validated in memory at `git_ops.py:181` before either writer is invoked
(`config_cmds.py:561`). Missing identity, missing clone, conflicting clones and unsafe subdirectory
refuse before writes. Empty change dictionaries exit before writes (`config_cmds.py:551`), and
`set_collector_values` replaces every matching assignment, preserves unrelated lines, quotes values
and backs up once (`git_ops.py:84`). These match the approved local-file design; a cross-file
transaction subsystem is unnecessary for the stated envelope.

### Reuse, callers and complexity

The reviewed paths use the shared resolver and existing Rebalance config writer. The disclosed
collector writer remains justified: the installer setter is embedded in a side-effecting installer,
and its calls update identity/name/discovery (`experimental/git-pulse/install.sh:265`, `:272`,
`:289`). No additional persistence system or scheduler is introduced in the reviewed implementation.
The existing `pulse_health.resolve_sync_repo_dir` parser remains separate (`pulse_health.py:102`);
leaving it for the disclosed follow-up is acceptable because enrolled Macs obtain the normalized
publisher path through its first-choice branch at `:110`. It is not evidence that all repository
parsing has been consolidated; its fallback semantics still differ.

HOME acceptance preserves the fleet result shape and identity/subdirectory/path-equality checks
(`git_ops.py:198`). The relevant callers consume the same device/subdirectory values or fleet
truthiness: `pulse.py:860`, `:962`, `:1052`; `index_ops.py:2156`;
`sync_snapshot.py:68`, `:243`, `:294`; `doctor.py:124`; publication guard `git_ops.py:658`.
No caller regression is apparent from these source paths. Runtime compatibility remains subject
to the clone gate. No extra abstraction or machinery needs cutting.

The rating **65/55/50/55** remains proportionate to the stated four-Mac dependency, recoverable
configuration failures and bounded implementation. Appeal stays 50. Historical issue counts and
actual fleet state were not independently established by this review.

### Evidence assessment and nonblocking nits

- The retained red-control script calls **public `run_doctor`**, uses identical scenarios and
  stubs only collector-health retrieval to reach the intended branch
  (`doctor-red-control.py:18`, `:35`). Both JSONL files substantiate the two diagnostic comparisons:
  candidate adds enrollment WARN/preview and missing-config FAIL/installer; base's generic fleet
  and scheduler failures remain present. This is a meaningful behavioral falsifier, not an import
  failure or suppression of the old error. It does not measure real collector delivery.
- Tests assert config bytes, conflict refusal, pre-write validation, literal normalization,
  duplicate replacement and rerun stability (`tests/test_fleet_enroll.py:82`, `:130`, `:139`,
  `:178`). **Nit:** the five doctor cases call the private helper (`:212`), rather than all rows
  going through the public report as planned. The retained public red controls cover two states,
  and the report wiring is visible in source, so this does not block PR preparation.
- **Nit:** UPGRADE's rc branches are comments (`UPGRADE.md:148`), and the manual Sleuth snippet
  proceeds directly from discovery to clone (`SLEUTH_SYNC.md:54`). Their surrounding prose tells
  the agent to stop, satisfying the agent-run procedure, but they are not guarded paste-and-run
  scripts. Prefer an explicit shell branch or direct reference to the already guarded setup
  script when next editing these instructions.
- **Evidence limit:** SUMMARY's full-suite totals, mutation counts, lint/type/ratchet results and
  manual byte comparisons are producer-reported; the supplied campaign contains no corresponding
  raw console records to independently audit those claims. The JSONL supports the doctor comparison,
  not all those other claims. Retain the subsequent harness output with its revision/command and
  distinguish it from the earlier reported runs. **[Unverified — needs clone run]** those checks,
  actual CLI execution/idempotence and full caller regression coverage were not rerun here.
  Live application, four-Mac rollout and retirement remain operator-run, as SUMMARY states.

### Review boundary

Used the SWE review rubric; read the approved plan, all plan-QA rounds, campaign summary and
red-control source/results, the implementation, tests and relevant caller/documentation sections.
No graph tools were exposed in this session's tool inventory, so direct targeted source reads
provided Verify-style evidence; no graph generation or coverage completeness is claimed. The
requested base-to-head git diff was not executed because this turn expressly prohibits git.
This review covers the seeded implementation, not independent verification of commit provenance
or an exhaustive diff outside the named scope.

No test runner, executable fixture, behavioral probe, git command, live configuration mutation or
source edit was run. Only this relay file was changed; scratch setup used `.relay-scratch/tmp`.
The post-turn harness remains responsible for executable gates.
