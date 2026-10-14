# Sanitized independent plan review

Model: claude-fable-5-1; effort: high.
Round 1: findings (driver 5). Round 2: reviewer PASS; native attestation publication failed (driver 4) because relay-system is ignored. This is not a mechanically attested implementation approval. Original private transcript SHA-256: 6cc56015629db0dd61b6932b9b1c3b8aaeeb7a52b9a7ba714fa2f6d94f39b8b2

### Reviewer · Round 1 (claude — Claude Fable 5.1)

Reviewed `PROJECT/2-WORKING/GH-282-PULSE-DELIVERY-PIPELINE.md` (131 lines) and `GH-282-RECON.md` (36 lines)
against source at worktree HEAD ec92641. Definition of Done in Setup is an unfilled placeholder, so I graded
against the packet's four questions. No pytest, validate.sh or fixtures were run; read-only `rg`/`sed` probes only.

swept file: yes
Sweep coverage: both plan docs in full; `experimental/git-pulse/collect.sh` 1-635 and
`src/rebalance/lib/git_ops.py` 1-501 in full; `sync_snapshot.py` 56-358; `pulse.py` 60-119 and 800-1031;
`index_ops.py` 2070-2168; `pulse_health.py` 130-202; `pulse_sync.sh` 30-85; `daily_synthesis.py` 425-500;
`hiqs_digest.py` 915-974. Not read: the rest of `pulse.py`, `doctor.py`, `health-check.py`, `view.sh` bodies.

**Findings — behaviour or contract gaps in the plan**

1. `[Should]` Q1 — commit-only has no success contract, so a healthy fleet-mode run reports failure.
   Step 1 says every Python publisher commits only, and recon says the policy lives "inside the shared
   producer boundary". The boundary returns `{"committed": committed, "pushed": False}` when not pushing
   (`src/rebalance/lib/git_ops.py:467-469`). `utils/daily_synthesis.py:465-466` computes
   `published = bool(result.get("pushed"))` then `if not (unchanged or published)` returns `ok: False`,
   reason `git publish failed: unknown Git publication failure` (`:467-472`), with `push=True` hardcoded at `:460`.
   `utils/hiqs_digest.py:972` accepts `pushed or not push`, but its caller default is `push=True` (`:995`), so an
   override inside the boundary fails it the same way.
   Fix: step 1 names one "queued for collector" result key returned by the boundary, lists the caller gates to
   update (daily_synthesis.py:465, hiqs_digest.py:972, the sync refresh result), and adds an acceptance line:
   fleet-mode run with a new commit and no push exits 0.
   Observed input: fleet-mode result `{"committed": True, "pushed": False}` reaching `daily_synthesis.py:465-466`.
   Affected scope: every publisher result where fleet mode is on and the caller passed `push=True`.
   Falsifier: a clone-run test of daily synthesis in fleet mode with a changed block; if it already returns
   `ok: True` and exit 0 with no code change, this finding is wrong.

2. `[Should]` Q1/Q2 — the plan does not say which identity names sync payloads, and the collector cannot derive it.
   Sync export uses `get_device_id()` (`index_ops.py:2098`), a `socket.gethostname()` slug
   (`sync_snapshot.py:67-72`; `doctor.py:118-124` documents its `-local` suffix). The collector uses the
   `scutil --get ComputerName` slug (`collect.sh:272`, `:282`, `:86-94`). The sync subdirectory is Python config
   (`config.py:1506`, default `sync`) that `config.sh` does not carry. Step 2 keeps "existing per-device layout";
   step 3 has the collector stage "sync payloads" — it has no way to compute `sync/calendar/<python-id>.json`.
   The collector also rewrites its own `device_id` at runtime (`collect.sh:284-306`, `set_config_value` at `:269`),
   so "explicitly validated … matching the existing collector identity" needs a named source of truth and a check time.
   Fix: state (a) Python reads the collector's configured `device_id` at each publish and refuses on mismatch,
   (b) which ID names sync payloads in fleet mode, (c) how the collector learns the sync subdir, or that the
   exact owned paths are handed to it explicitly.
   Observed input: a Mac whose hostname slug ends `-local` while its collector `device_id` does not.
   Affected scope: fleet-mode sync payload paths and the collector's owned-path set.
   Falsifier: on the Studio, `get_device_id()` equals `device_id` in `~/.config/git-pulse/config.sh` and
   `sync_subdir` is unset on all four Macs; then only the source-of-truth sentence is needed.

3. `[Should]` Q2 — collector deadlines have no stated mechanism, and delay/retries inside the lock starve publishers.
   Probe: `command -v timeout gtimeout; echo rc=$?` → no output, `rc=1` (no `timeout(1)` on this Mac).
   Collector network calls are bare: `collect.sh:195` (pull), `:510` (early push), `:612-614` (push). The lock is
   taken at `collect.sh:316-334`, before the repo scan, and held to exit. Step 3 adds a delay "capped at 240 seconds"
   plus three attempts with 2–20s jitter. Held inside the lock, Python publishers get `GitPublishLockBusy` →
   `deferred` (`pulse.py:830-837`) → exit 75 (`pulse_sync.sh:56-57`); in commit-only mode a deferred render is
   never committed, so that page misses the cycle's only push.
   Fix: state that the per-device delay runs before the lock exec at `collect.sh:316`, and name the deadline
   mechanism (python3 is already a collector dependency at `:317`; `git_ops.py:186-199` shows the process-group kill).
   Observed input: a pulse_sync run starting while the collector sleeps its stagger delay under the lock.
   Affected scope: fleet-mode Macs where a publisher schedule overlaps the collector run.
   Falsifier: a real-Git clone probe with the delay placed after the lock showing pulse_sync still commits.

4. `[Should]` Q3 — step 5 "stage only that UUID's snapshot" conflicts with how `snapshots/` is staged today.
   The collector accepts any dirty path under `snapshots/` (`collect.sh:501`) and stages the whole directory with
   `git add -A` (`:596`, `:601`; comment at `:593-595` says the snapshot hook "does NO git of its own"). If the CLIO
   owner export lands under `snapshots/`, anything reconcile/import writes there is published wholesale — that is
   the imported-origin echo. If the wildcard is narrowed to one UUID, the existing snapshot hook's files become
   foreign dirt and block the collector at `:502-503`.
   Fix: name the CLIO owner export path, say whether the `snapshots/` wildcard stays, and say where imported
   origins are written so they are provably outside every staged path.
   Observed input: an imported-origin file written under `snapshots/` by the helper's reconcile.
   Affected scope: every dirty or untracked path under `snapshots/` on a fleet-mode Mac.
   Falsifier: PR #5's helper writes imported origins only outside the checkout; then one sentence saying so closes this.
   Probe: `rg -n -i clio experimental/git-pulse -g '!*.md'` → no match, so no collector↔CLIO seam exists here yet.
   CLIO PR #5 itself: `[Unverified — external repo, not in this worktree]`.

5. `[Should]` Q4 — ALIVE_NOT_PUBLISHING has no opt-in predicate, so the pilot would flag the three other Macs.
   Health reads only `devices/*.yaml` (`pulse_health.py:188-196`) and no field marks a device as a fleet-mode
   publisher. Standalone collectors need no Rebalance install (`collect.sh:315`), and non-opted Macs keep the root
   page (`pulse.py:1002`), so each has a fresh heartbeat and no `devices/<id>/live-pulse.md`.
   Fix: the collector writes an explicit marker in its YAML when fleet mode is on; the new state applies only then.
   Step 4's "legacy metadata compatibility" points this way — make the predicate explicit.
   Observed input: any `devices/<id>.yaml` with fresh `last_scan_utc` for a Mac that never opted in.
   Affected scope: devices whose metadata lacks the fleet marker.
   Falsifier: a health test with a fresh legacy YAML and no device page; expected state stays `ALIVE`.

**Findings — proportionality and doc hygiene**

6. `[Nit]` Q2 — `read_latest_snapshot` has no production caller. Probe:
   `rg -n 'read_latest_snapshot' -g '!TESTS-RESULTS/**' -g '!PROJECT/**' -g '!relay-system/**' .` → only the
   definition at `sync_snapshot.py:342` and `tests/test_sync_snapshot.py:15,390,401`. Step 2's reader aggregation
   serves tests only: name the real consumer or shrink it to "stop writing the pointer". Also state the fate of the
   tracked, now-stale `latest.json` (still written at `sync_snapshot.py:148`, `:210`; owned at `index_ops.py:2117-2121`).
7. `[Nit]` Q1 — prior art omitted: `PULSE_PUSH=false` already gives commit-only for the live page
   (`scripts/pulse_sync.sh:37-41`). Say whether fleet mode reuses or supersedes it and which wins when both are set.
8. `[Nit]` The doc carries two plans. Lines 46-66 still read "Phase 1 … (Current Scope)" and list Phase 3
   `devices/<id>/status/<job>.yaml`, which the ordered steps at 85-114 dropped; frontmatter `phases: 3` vs a
   four-entry table of contents; effort row says "~50 lines across 3 files". Mark 46-66 superseded.
9. `[Nit]` Pre-existing, in files this plan touches: under `set -euo pipefail` (`collect.sh:5`) an offline
   `pull_safely` (`:508`) or early push (`:510`) exits before the heartbeat is written (`:530`), as a generic
   exit 1; the collector has no exit taxonomy to match pulse_sync's. The bare push at `:510` also fails on a branch
   with no upstream before the `-u origin HEAD` fallback at `:614` can run. Step 3 should cover both.
10. `[Nit]` Q4 rollback — the restored legacy collector treats any dirty `devices/<id>/…` page as foreign and
    blocks (`collect.sh:498-503`). Add one rollback line: confirm a clean tree and no unpushed fleet commits first.

**Passes**

- `[Pass]` Recon: shared publisher has exact-path commits, common lock and 120s default deadline —
  `git_ops.py:44-57`, `:453-464`, `:380-387`.
- `[Pass]` Recon: publishers that push today — `utils/daily_synthesis.py:460` (`push=True`),
  `utils/hiqs_digest.py:995`, `src/rebalance/cli/refresh.py:138`, `src/rebalance/mcp/tools/index.py:165`;
  sync always pushes because `sync_snapshot.py:291-296` passes no `push` argument.
- `[Pass]` Recon: collector proves HEAD is upstream before advancing the watermark — `collect.sh:625-632`.
- `[Pass]` Recon: `read_latest_snapshot` is pointer-only — `sync_snapshot.py:348-356`.
- `[Pass]` Namespace is reader-safe: device readers glob non-recursively, so a `devices/<id>/` directory does not
  break them — `pulse_health.py:188`, `health-check.py:162`, `view.sh:187`.
- `[Pass]` Q4 qualification limits are honest: "Synthetic probes do not satisfy these live gates" and the issue
  stays open until four-Mac rollout, three cycles with offline/rejoin, and seven-day failure rate (plan 121-124).
- `[Pass]` Proportionate: no new store, timer, ledger writer or central host — "no new timer, vector store, push
  loop or XYZ ledger writer" (plan 78-79), consistent with the packet's envelope.
- `[Unverified — needs clone run]` Baseline "2804 passed, 21 skipped, 11 xfailed, 143 subtests" (plan 81-82).
- `[Unverified — outside worktree]` "Installed runtime: 17e08c1, 14 commits behind" (recon 3).

VERDICT: FAIL
Basis: The ownership direction is right and proportionate, and the live gates are honest, but five contracts are
left open in ways the cited code shows will misreport or block: commit-only success, sync-payload identity,
collector deadline/lock placement, `snapshots/` staging versus CLIO echo, and the not-publishing predicate. Each
needs one or two sentences in the plan, not new machinery. Nits 6-10 are optional.

Handing off to Producer — go to the Producer window and say "take your turn": disposition findings 1-5
(Implemented / Modified / Declined), amend the plan doc, bump ROUND to 2.

