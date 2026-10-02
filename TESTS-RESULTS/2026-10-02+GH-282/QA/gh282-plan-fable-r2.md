# Sanitized independent plan review

Model: claude-fable-5-1; effort: high.
Round 1: findings (driver 5). Round 2: reviewer PASS; native attestation publication failed (driver 4) because relay-system is ignored. This is not a mechanically attested implementation approval. Original private transcript SHA-256: 7f2c63df0e28784b79a804c5e6922c717499c149b824e5f85f5b9ac01dedf306

### Reviewer · Round 1 (claude — Claude Fable 5.1)

Reviewed `PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md` (120 lines) and `GH-282-RECON.md` (52 lines) at
worktree HEAD ec38f81 (plan amended in db9f8ad), against current source and against my five `[Should]` findings in
`relay-system/2026-10-02/gh282-plan-fable-r1.md`. Definition of Done in Setup is still an unfilled placeholder, so I
graded against the packet's four questions. No pytest, validate.sh or fixtures were run; read-only `rg` / `git grep` /
`sed` probes only.

swept file: yes
Sweep coverage: both plan docs in full; `experimental/git-pulse/collect.sh` 1-635 in full;
`src/rebalance/lib/git_ops.py` 170-501; `src/rebalance/ingest/sync_snapshot.py` 56-358; `pulse_health.py` 1-202 in
full; `pulse.py` 56-120 and 796-1031; `index_ops.py` 2066-2168; `scripts/pulse_sync.sh` 1-85 in full;
`utils/daily_synthesis.py` 440-475; `utils/hiqs_digest.py` 955-975; `doctor.py` 1850-1944;
`experimental/git-pulse/health-check.py` 128-187. Not read: the rest of `pulse.py`, `doctor.py`, `view.sh`, `install.sh`
bodies. Pre-existing defects in the swept files: none found beyond those already raised in r1 (nits 9-10), which the
plan now covers at line 120.

**Round-1 findings — disposition check**

- `[Pass]` r1-1 (commit-only success contract) closed. Plan 115: "fleet results carry `queued=True`, not
  `pushed=True`; daily synthesis, digest and sync outcome gates explicitly accept queued success. Fleet mode always
  wins over caller push=True and PULSE_PUSH". That names the gates I cited (`utils/daily_synthesis.py:465-466`,
  `utils/hiqs_digest.py:972`). The commit-only path is already safe inside the publisher: `pulse.py:868-877` returns
  "no content change" without a remote check when `push` is false, and `pulse.py:896` skips the pending-delivery
  branch.
- `[Pass]` r1-2 (identity source of truth) closed. Plan 116: "the collector config remains the device identity source
  of truth … missing, unsafe or mismatched values refuse before write … Collector fleet_sync_subdir must match Python
  sync_subdir; no hostname inference." Every mismatch I could construct from `collect.sh:280-306` fails closed
  (refuse), never writes to a wrong namespace.
- `[Pass]` r1-3 (deadline mechanism, lock placement) closed. Plan 117: "deterministic stagger runs before lock
  acquisition. Existing python3 supplies collector Git deadlines through subprocess process-group termination, no
  timeout(1) dependency." The lock exec is `collect.sh:316-334`; the reusable kill pattern is `git_ops.py:186-199`.
- `[Pass]` r1-4 (CLIO path versus `snapshots/` wildcard) closed on paper. Plan 118: "canonical CLIO owner export is
  exactly devices/<configured-CLIO-UUID>/clio.jsonl. Imported history remains solely in the private SQLite DB outside
  the Git checkout … No broad devices/ staging." No collision with existing readers: they glob `devices/*.yaml`
  non-recursively (`pulse_health.py:188`, `health-check.py:162`). The helper itself (CLIO PR #5) is
  `[Unverified — external repo, not in this worktree]`; plan step 5 keeps it a separately reviewed prerequisite.
- `[Pass]` r1-5 (not-publishing predicate) closed. Plan 119: "collector YAML carries fleet_mode=true only for opted-in
  devices. Legacy/unmarked collector devices keep existing ALIVE classification." A new state cannot read as healthy
  by accident: `doctor.py:1873` maps any unrecognised state to a warning, and the legacy collector rewrites the whole
  YAML (`collect.sh:530-549`), so rollback drops the marker on its own.
- `[Pass]` r1 nits 6-10 dispositioned at plan 120, including the rollback precondition "Rollback requires a clean
  private checkout and no unpushed fleet commits".

**Packet questions**

- `[Pass]` Q1 — policy covers every entry. Probe (rc=0):
  `rg -n 'publish_git_paths\(|_commit_and_push_if_changed\(|commit_and_push_sync\(|git_pull_rebase_safe\(' src utils scripts experimental -g '!*.md'`
  → callers are only `pulse.py:999`, `utils/daily_synthesis.py:456`, `utils/hiqs_digest.py:960`,
  `index_ops.py:2127,2138`, all through `git_ops.py:435`. `git grep -nE 'git .*(pull|push|fetch|commit|add|stash|reset)\b' -- experimental/git-pulse ':!*.md' ':!collect.sh'`
  → no match, so the collector is the only shell writer. `reconcile_pulse_mirror` (`pulse.py:74`) has no caller:
  `git grep -n reconcile_pulse_mirror -- src utils scripts experimental` → definition only. Policy at the shared
  boundary is therefore sufficient.
- `[Pass]` Q2 — snapshot and staging contracts are safe and proportionate. Sync export and commit already run inside
  the lock (`index_ops.py:2116-2144`) and the live page is written inside it (`pulse.py:821`, `:906`), so a busy-lock
  deferral leaves no dirty file for the collector to trip on. The collector refuses foreign dirt today
  (`collect.sh:501-503`) and proves upstream before the watermark (`collect.sh:625-632`); step 3 extends, not replaces.
- `[Pass]` Q3 — distinct UUID, no hostname inference: plan step 5 "Do not infer canonical capture identity from a
  hostname or echo imported origins"; recon 31-32 "CLIO owner UUID is a third, intentionally distinct identity".
  Same-note / 300-second exporter behaviour lives in the external helper: `[Unverified — external repo]`.
- `[Pass]` Q4 — limits and rollback are honest. Plan 101-103: issue stays open until "the real four-Mac rollout, at
  least three actual Pulse cycles including an offline/rejoin interval … seven-day failure-rate qualification …
  Synthetic probes do not satisfy these live gates." Plan 81: "A failed network delivery cannot instantly report its
  failure remotely".
- `[Unverified — needs clone run]` Baseline "2804 passed, 21 skipped, 11 xfailed, 143 subtests" (plan 61-62).
- `[Unverified — outside worktree]` "Installed runtime: 17e08c1, 14 commits behind" (recon 13).

**Nits — non-blocking, carry into implementation QA (step 6)**

1. `[Nit]` Plan 115-120 label the contracts "Implemented", but nothing is in code yet. Probe:
   `git grep -n 'pulse_device_id\|fleet_mode\|fleet_sync_subdir' -- src utils scripts experimental` → 2 hits, both the
   unrelated local variable at `collect.sh:149,157`. Reword to "Plan amended" so a later reader does not take it for
   shipped behaviour; implementers should treat 115-120 as binding parts of steps 1-5, since the ordered steps were
   not all updated to carry them (stagger-before-lock and the status record appear only there).
2. `[Nit]` The device-ID comparison should apply the collector's own normalisation, or require the literal to be
   canonical already. The collector lowercases and sanitises (`collect.sh:280-281`) and falls back to the hostname
   slug when `device_id` is empty without writing it back (`collect.sh:302-306`; `set_config_value` runs only in the
   migration at `:269`). A raw literal compare refuses a working Mac. Fails closed, so not a blocker; add an opt-in
   precondition "no pending device-ID migration, `device_id` present and canonical in config.sh".
3. `[Nit]` The "owned status" record in plan 119 has no path or write point. Name it (under `devices/<id>/`), commit it
   in the same locked transaction as the page, and note that exit 75 and exit 1 runs cannot record themselves
   (`pulse_sync.sh:55-56`, `:51-52`) — age of the last delivered status is the only signal for those.
4. `[Nit]` Reading "committed upstream status" needs local git, which changes the health reader's stated contract
   "Reading is pure: flat-YAML line parse, no subprocess, no git" (`pulse_health.py:14`). Say so, keep it to bounded
   local commands, and fall back to the legacy classification on git error.
5. `[Nit]` Two classifiers exist: `pulse_health.py:138` and `experimental/git-pulse/health-check.py:135`
   ("thresholds and states mirror that script exactly", `pulse_health.py:20`). State whether ALIVE_NOT_PUBLISHING
   lands in both or only the doctor path.
6. `[Nit]` State the worst-case time the collector holds the lock with three attempts at 120-second deadlines plus the
   early pull/push, so the "busy is not failure" window for Python publishers is a known number.

VERDICT: PASS
Basis: All five round-1 contract gaps are answered in the plan with text that matches the cited code, every writer
into the shared checkout goes through the one boundary the policy governs, and the live-pilot gates stay open and are
not closed by simulated evidence. The six nits are wording and small implementation notes, none backed by an observed
failing input; they belong to implementation QA, not another plan round. Two items remain unverifiable from this
worktree (the external CLIO helper and the baseline test counts) and are labelled as such.

Relay closed (Approved), no further turn needed. Producer: proceed to implementation per steps 1-7, carrying nits 1-6.


### Attestation · relay-drive — 2026-10-02T18:36:41Z
task: REBALANCE-GH282-PLAN-FABLE-R2
reviewer: claude
status: Approved
reviewed-head: ec38f81449635e591294ebd8dfc364cf8a4f84d6
added-range: 6712+8859
added-sha256: b8070e750ddb2cddaa574cc1027f258aa72132aef88d741f7f108f0a77a16dac
