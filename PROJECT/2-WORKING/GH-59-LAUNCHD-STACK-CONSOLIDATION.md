---
title: "Background Stack Consolidation, Deterministic Boot, and Robust Health Monitoring"
status: "Draft"
created: 2026-08-17
updated: 2026-08-17
owner: noel
goal: "One control plane for the launchd fleet, doctor failures that actually fail, and a GitHub sync that fits inside its hourly budget."
gh_issue: 59
related: [58, 60, 61, 62, 54]
effort: 2
complexity: 2
risk: 2
phases: 4
ratings_provisional: false
roadmap_exempt: false
---

# Background Stack Consolidation, Deterministic Boot, and Robust Health Monitoring

## Status

| What was just completed | What's next |
|---|---|
| Authored proposals (#58–#62); drafted `scripts/stack.sh` (untracked); measured the live machine and both failing jobs against real logs. | Phase 0: commit `stack.sh`, repoint `pulse_target_path`, load the 3 unloaded agents. |

## Quad Concepts
- 12 installer scripts and no way to ask "is the stack up?" → one `scripts/stack.sh` control plane.
- Two jobs broken for a day with nothing reporting it → crashed jobs grade `FAIL`, and `FAIL` is never suppressed.
- An hourly GitHub crawl that costs more than an hour's rate-limit budget → hourly scans Band A, daily scans everything.
- A plan built on guesses → every claim below was checked against the live machine before it was written down.

## Table of contents
1. [Evidence](#evidence)
2. [Phase 0 — Stop the bleeding](#phase-0--stop-the-bleeding)
3. [Phase 1 — Deterministic stack CLI (`scripts/stack.sh`)](#phase-1--deterministic-stack-cli-scriptsstacksh)
4. [Phase 2 — Doctor failures that fail](#phase-2--doctor-failures-that-fail)
5. [Phase 3 — GitHub sync inside its budget](#phase-3--github-sync-inside-its-budget)
6. [Out of scope](#out-of-scope)

---

## Evidence

Measured on this machine, 2026-08-17 ~21:25 PDT. Everything in the phases below rests on this
table, and nothing else does.

| # | Finding | How it was checked |
|---|---|---|
| E1 | **11 rebalance LaunchAgents**, plus 3 preserved 3-Eyes plists = 14 files. | `ls ~/Library/LaunchAgents/` |
| E2 | **8 loaded, 3 installed-but-never-loaded**: `health-check`, `health-check-triage`, `pulse-warning-watch`. | `launchctl list` |
| E3 | **12** installer scripts, not 11. | `ls scripts/install_*.sh` |
| E4 | `github-sync` and `pulse-sync` both report last exit `1`. | `launchctl list` |
| E5 | **`pulse-sync` root cause:** `pulse_target_path` points at `/Users/noelsaw/Documents/rebalance-OS/git-pulse-sync`, which no longer exists. The real mirror is `~/git-pulse-sync`. | `temp/logs/pulse_sync_2026-08-17.log`, `ls` |
| E6 | **`github-sync` root cause:** the full crawl costs more than one hour of PAT budget. See the run ledger below. | `temp/logs/github_sync_2026-08-17.log` |
| E7 | Rate limit at time of writing: `core` 4986/5000 remaining. The quota is not permanently gone — it is burned and refilled. | `GET /rate_limit` |
| E8 | All 11 managed jobs have a `scripts/com.rebalance-os.*.plist.template`. `stack.sh up` can render the whole fleet today. | `ls scripts/*.plist.template` |
| E9 | The live plists point at **`~/rebalance-runtime`**, not this checkout. | `plutil -p ~/Library/LaunchAgents/…` |

### github-sync run ledger, 2026-08-17

| Fired | Elapsed | Outcome |
|---|---|---|
| 08:45 | 75 s | `Failed to fetch /user: HTTP 503` |
| 09:45 | **3121 s (52 min)** | `No module named 'mlx_embeddings'` |
| 10:45 | 93 s | Rate limited, `remaining=0` |
| 11:45 | **2486 s (41 min)** | `No module named 'mlx_embeddings'` |
| 12:45 | 101 s | Rate limited, `remaining=0` |
| 13:45 | **2324 s (39 min)** | `No module named 'mlx_embeddings'` |
| 14:45 | 127 s | Rate limited, `remaining=0` |
| 15:45 | **3000 s (50 min)** | `No module named 'mlx_embeddings'` |
| 16:45 | 100 s | Rate limited, `remaining=0` |
| 18:28 | 87 s | Rate limited, `remaining=0` |
| 18:45 | 71 s | Rate limited, `remaining=0` |
| 19:45 | **3167 s (53 min)** | **complete** |
| 20:45 | 77 s | Rate limited, `remaining=0` |

Read it as a two-hour oscillation: a long run consumes the entire 5,000-request window, the next
hourly run starts eight minutes later with nothing left and dies in ~80 seconds, the window resets
during that hour, and the cycle repeats. The 19:45 run proves the point — it **succeeded** and still
exhausted the budget. So this is not a bug in the retry path being bypassed; the job is simply
larger than its schedule. Throttling is the correct fix, not a workaround.

### Prior art — build on these, do not duplicate them

| Exists | Where | Consequence for this plan |
|---|---|---|
| `x-ratelimit-*` sampling; `403`-with-`remaining==0` detection; `Retry-After` + backoff | `src/rebalance/ingest/_http.py:96-113`, `:184-188`, `:196` | Phase 3 **reads** a value the client already collects. No new instrumentation. |
| Repo activity bands (A = 0–7 d, B = 8–14 d, C = 15–30 d) | `src/rebalance/ingest/github_scan.py:56-57` | Phase 3 reuses `active_bands`. No competing "Focus 5" tiering. |
| Plist render + `plutil -lint` + unload-then-load | `scripts/lib/install_common.sh` → `rb_install_launchd_job` | Phase 1 calls it. No new plist machinery. |
| `doctor` already exits 1 on `FAIL` | `src/rebalance/cli/__init__.py:213-215` | Phase 2 changes **grading only**. The exit-code plumbing is done. |
| Crash-loop detection keyed on PID identity change | `doctor.py:78-84` (GH-146 root cause B) | Deliberate. Phase 2 does not revert it. |

### 3-Eyes

3-Eyes was stood down on 2026-08-17 (`AGENTS.md`: *do not repair, do not operate*, and explicitly
*do not build a replacement supervisor*). **This plan builds no supervisor and no watchdog.** It
relies on launchd's own `KeepAlive`, a CLI you run on purpose, and a non-zero exit code. The three
3-Eyes plists stay on disk untouched; Phase 1's managed-job manifest is what guarantees that.

---

## Phase 0 — Stop the bleeding

Four small changes that fix the actual outage. No new code.

- [ ] Commit and push `scripts/stack.sh`. It is 267 untracked lines living in one working tree with
      no backup behind it, and every later phase builds on it.
- [ ] Repoint `pulse_target_path` to `/Users/noelsaw/git-pulse-sync` (E5). One config value.
- [ ] Load the 3 installed-but-unloaded agents (E2) — this restores `health-check` today, before any
      refactor.
- [ ] Record the outstanding unknown as its own issue: `mlx_embeddings` fails to import inside the
      launchd context and ends 4 of 13 runs after 40+ minutes. It is **not** the cause of the rate
      limiting (the 19:45 run succeeded and still exhausted the budget), so it does not block this
      plan — but it must not be lost.

### QA Gate 0
- `launchctl list | grep rebalance` shows 11 jobs, 0 unloaded.
- The next `pulse-sync` fire exits 0.
- `git ls-files scripts/stack.sh` returns the path.

---

## Phase 1 — Deterministic stack CLI (`scripts/stack.sh`)

### Scope (GH-60)

Make the draft script trustworthy. Four defects found by reading it against the machine:

1. **`doctor` is broken.** It runs `python -m rebalance.doctor`, but `doctor.py` has no
   `__main__` block. Call the CLI entry point instead.
2. **The manifest is incomplete.** `git-pulse-daily-synthesis` has a template and an installer but
   is absent from `JOBS`, so `status` will never mention it and `up` will never load it.
3. **`down` deletes plists, and `restart` is `down` then `up`.** A failed `up` therefore leaves the
   machine with *zero* agents — precisely the silent outage this plan exists to prevent. `down`
   should unload and leave the file; add a separate explicit `purge` if removal is ever wanted.
4. **`up` silently rebinds the fleet to whichever checkout it runs from.** `rb_install_launchd_job`
   derives `REBALANCE_DIR` from its own location, and the live plists currently point at
   `~/rebalance-runtime` (E9). Running `up` from a dev clone migrates all 11 jobs with no warning.
   `up` must print the target root and refuse to change it without `--force`.

Plus the agreed hardening:

- Drive `up`/`down`/`status` from the explicit `JOBS` manifest, never a `com.rebalance-os.*` glob,
  so the 3 preserved 3-Eyes plists are structurally untouchable.
- `status` lists unmanaged `com.rebalance-os.*` plists in a separate section rather than hiding them.
- Reconcile the usage block with the dispatcher: `up`, `down`, `restart`, `status`, `doctor`,
  `verify` (`test` is an accepted alias).
- `tests/test_stack_script.py` — manifest completeness (every template has a `JOBS` entry and vice
  versa), `plutil -lint` on every rendered plist, and a negative control proving `down` refuses a
  label outside the manifest.
- Point `SCHEDULER.md` at `stack.sh` as the runbook. It exists; this is an edit.

Keep the 12 installers in place for now. Delete them only once `stack.sh` has been proven on a
second machine — a bootstrap tool that has replaced its own predecessors and exists in one place is
a single point of failure.

### QA Gate 1
- `bash scripts/stack.sh up` loads all 11 managed jobs and prints the target root it bound them to.
- `bash scripts/stack.sh down` unloads only managed jobs; all 14 plist files still on disk; the 3
  3-Eyes plists never appear in its output.
- `bash scripts/stack.sh doctor` runs the health check and exits with the health check's own code.
- `pytest tests/test_stack_script.py` passes in CI.

---

## Phase 2 — Doctor failures that fail

### Scope (GH-61)

`doctor` already exits 1 when any check is `FAIL` (`cli/__init__.py:213-215`). The gap is that
nothing grades these `FAIL`. Promote three states from `WARN` to `FAIL`:

1. A scheduled job whose last launchctl exit is non-zero with no live PID (`_check_launchd`).
2. A required configuration path that does not exist on disk (`_check_pulse`) — this is exactly E5.
3. A LaunchAgent that **this machine installed** and is now absent or unloaded
   (`_check_scheduler_liveness`).

Requirement 3 is scoped deliberately. "Required agent is missing → `FAIL`" applied to the full
catalogue would hard-fail a fresh clone that has never run an installer. The repo already draws this
line — `_COLLECTOR_FRESHNESS` gives every source a `configured=` probe so an unconfigured source
stays quiet instead of failing. Same rule here: *installed and now gone* is a failure; *never
installed* is not.

Also in scope:

- Flip `scripts/health_issue_reporter.py` to file issues for `FAIL` by default. Grading a job `FAIL`
  achieves nothing if the reporter still only files on... the same set it always did. This is the
  second half of the fix, not a follow-up.
- State the suppression invariant explicitly: warnings may be suppressed after a recent successful
  sync; **failures never are**. Today's behaviour is inherited rather than decided
  (`cli/__init__.py:203-211`).

Explicitly **not** in scope:

- **No blanket long-uptime rule.** The original proposal flagged any job running over 30 minutes.
  The ledger disproves it: `github-sync` legitimately runs 39–53 minutes, and `pulse-server` is a
  `KeepAlive` daemon that runs forever by design. A 30-minute rule fails both healthy cases. If an
  overlap signal is wanted later, the self-calibrating one is *"still running when its next
  scheduled fire is due"* — no magic number, correct for every cadence, and silent for daemons.
- **No revert of live-PID crash-loop handling.** That is GH-146 root cause B and it is documented at
  `doctor.py:78-84`. Neither failing job has a live PID (both show `-`), so this was never what hid
  them. Reverting it re-opens the false-positive alerts GH-146 closed.

### QA Gate 2
- With `pulse-sync` at exit 1, `rebalance doctor` exits 1.
- With all managed jobs healthy, `rebalance doctor` exits 0.
- An unloaded-but-installed agent produces `FAIL`; an agent that was never installed produces no
  check at all.
- A `FAIL` survives a recent successful sync (not suppressed); a `WARN` still gets suppressed.
- `health_issue_reporter.py --dry-run` lists the newly promoted checks.

---

## Phase 3 — GitHub sync inside its budget

### Scope (GH-62, GH-54)

Two steps, smallest first. **Ship 3a and re-measure before writing any of 3b.**

**3a — Scope the hourly run (small).**
- Hourly `github-sync` covers Band A only (0–7 days active), reusing `active_bands` from
  `github_scan.py:56-57`. No new tiering concept.
- Before the run, read the rate-limit sample `_http.py` already collects. If `remaining < 500`,
  stop cleanly and report `OK (throttled)` — a *success* for pipeline and doctor purposes, not a
  failure. A throttled skip is the system working.
- The 06:30 `daily-sync` keeps the full crawl. It has the whole night's budget.
- Then measure again: requests consumed and wall-clock for one Band A run.

**3b — Conditional requests (only if 3a leaves us over budget).**
- `If-None-Match` / `If-Modified-Since` in `_http.py` and the GitHub item fetchers. GitHub does not
  charge rate limit for a `304`, which is the entire win.
- ETags must persist across runs. Name the storage explicitly — a column on the existing scan state
  is preferable to a new table — because that is the real schema change here.
- `304` must mean *keep the existing rows*, distinct from *empty response*. Getting this wrong turns
  a successful no-change sync into apparent data loss.

### QA Gate 3
- 3a: one hourly run completes in under 3 minutes and consumes a measured, recorded number of
  requests well under 5,000.
- 3a: with `remaining` forced below 500, the job exits 0 and doctor shows `OK (throttled)`.
- 3a: the daily 06:30 run still covers all bands.
- 3b (if built): a `304` on an unchanged repo is observed in the log, and the row count for that
  repo is unchanged afterwards.

---

## Out of scope

**The unified hourly pipeline runner is dropped from this plan.** The original Phase 4 proposed
collapsing 11 LaunchAgents into 2 behind a new `hourly_pipeline.py` sequencer.

It does not fix either observed root cause. `pulse-sync` broke on a dead config path and
`github-sync` broke on a budget overrun; neither was caused by the jobs being separate, and neither
would have been prevented by merging them. What the change would do is replace launchd's scheduling,
per-job isolation, and per-job exit status with a Python sequencer that has to re-implement all
three, including continue-on-error semantics and per-stage telemetry that launchd gives for free.
Today's independent jobs are also why `vault-sync` kept working through a full day of `github-sync`
failures — that isolation is an asset.

The genuine complaint underneath it — "there is no single place to see or control the stack" — is
answered by Phase 1. `stack.sh` is the one entry point; it does not require the jobs themselves to
be merged.

Filed to `PARKED/` as **P-004**. Revisit only if per-job isolation is ever shown to be the problem.
