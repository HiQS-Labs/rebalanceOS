# GH-296 job_guard on a small-swap Mac — spike, three-way test, and old-vs-fixed

Date: 2026-09-27. Tracking: #296. Device: MacBook Pro 14" (Apple M4 Pro, 24 GB RAM, 2 GB
swap file, macOS 15.6). Plan: the #296 issue body, approved by an agy relay in two rounds
(`qa/gh296-plan-qa.md`). Operator workload during every run: VS Code, Slack, Antigravity and two
Claude Code sessions open.

## Question

Why does the job guard refuse healthy runs of small scheduled jobs on this Mac, and does the fix
let them run without removing the protections GH-172 needs?

## Runs

| Run | When (PT) | What | Data |
|---|---|---|---|
| 1. Spike | 11:38–11:52 | 5 jobs guarded (default), then with the compressor ceiling out of reach | `runs/1-spike/` |
| 2. Three-way | 15:21–15:28 | 5 jobs: old guard, proposed rule (emulated), no guard at all | `runs/2-three-way/` |
| 3. Old vs fixed | 17:34–17:40 | 3 jobs: old guard (4349ff5) vs this branch, both guard layers | `runs/3-old-vs-fixed/` |

The jobs were pulse-sync, pulse-web-sync, pulse-warning-watch, github-sync and
obsidian-vault-embeddings. Each ran through the real wrapper with its plist's `--name` and
`--max-runtime-seconds`. Scripts as run are in `scripts/`. Samplers recorded `memory_pressure` free %,
`vm.swapusage` and the compressor size (`vm_stat`); `samples.csv` holds those readings.
Logs are reduced to guard lines and start/finish markers (public repo).

## Findings

**1. The old guard refuses every job on a healthy machine.** 13 of 13 attempts across three runs
exited 75 with `memory compressor holds 8.0–10.7 GB, ceiling is 6.0 GB, confirmed by swap in use
1.1–1.2 GB`. The machine was 42–54% free throughout, with swap flat at 1168–1226 MB of 2048 MB. No
memorystatus kills appeared in `log show` for either window checked.

**2. Root cause: the absolute 1 GiB swap bar.** On a 2 GB swap file, ~1.2 GB of residual swap
never goes away, so the "confirmed by swap" branch is always true. Red control:
`red-control-at-9204aeb.txt` shows the new test failing on the pre-fix code with the production
message.

**3. There are two guard layers, and both applied the bad rule.** In run 2, with the wrapper
removed, obsidian-vault-embeddings still failed (exit 1). The in-process guard refused both scopes
(job log: `"error": "refusing to start: memory compressor holds 9.3 GB, ceiling is 6.0 GB, confirmed
by swap in use 1.2 GB"`, `"sync_outcome": "fatal"`). A deferrable refusal was reported as a hard
failure.

**4. The fixed guard runs them (run 3, same minute, same machine state):**

| Job | old | fixed | peak footprint |
|---|---|---|---|
| pulse-warning-watch | 75 | 0 (0 s) | 0.0 GB |
| github-sync | 75 | 0 (194 s) | 1.6 GB |
| obsidian-vault-embeddings | 75 | 0 (117 s, both layers) | 1.6 GB |

**5. Jobs are small.** Peaks were ≤ 0.26 GB for the pulse jobs and github-sync in runs 1–2, and
1.6 GB for embeddings and github-sync in run 3, against the unchanged 3.0 GB per-job ceiling. In
`temp/logs/job_rss.jsonl` (217 guarded runs since 2026-09-26) the maximum is 1.85 GB.

**6. Log noise.** In run 3 the "not in distress, proceeding" line repeated on every 5 s poll: 39
lines in one 194 s github-sync run. The branch now logs it once per run.

## Branch verification

- **Full suite** (`pytest tests/ HiQS/tests`) on `82e7417`: 2870 passed, 6 failed, 21 skipped, 11 xfailed.
  - All 6 failures are end-to-end embedding tests that fail identically on untouched `origin/development` (4349ff5) while this laptop is on battery (`pmset`: "Battery Power"). They don't pin `power_defer`, so battery deferral skips the embedding.
  - The failing tests: `test_dashboard_refresh_integration::test_real_chain_writes_note_reingests_and_embeds`, `test_embedder::test_embed_vault_chunks_end_to_end`, `test_figma_source_module::test_backfill_embed_query_end_to_end`, `test_github_knowledge::test_embed_and_query_local_github_corpus`, and `test_semantic_index` ×2.
  - Hosted CI (Linux, no battery) is the tie-breaker.
- **Static gates:** clean. That's ruff check/format, the sqlite/banned-import, script-inventory, machine-path, read-layer and near-duplicate ratchets, doc links, frontdoor, and mypy.
- **QA:**
  - Plan: agy relay, approved in round 2 (`qa/gh296-plan-qa.md`).
  - Implementation: Codex relay, 5 rounds (`qa/gh296-impl-qa.md`), closed **Escalated** on one accepted limitation. Off the main thread (the terminal dashboard's background GitHub refresh) a mid-run memory trip is raised after the batch rather than interrupting it; lock and preflight still apply. The operator chose to open the PR with this documented; the follow-up is in #297.
- **Red controls** were observed failing before their fix: the swap rule (`red-control-at-9204aeb.txt`) and the three worker-thread tests (on `aeb6c5e`, recorded in the relay).

## Threats to validity

- **Not the 48 h soak.** These are short manual runs, not a 48-hour soak, and don't satisfy #296 AC 5.3.
- **Not the heaviest case.** Run 3's embeddings pass did real work (117 s, 1.6 GB), but it wasn't a
  full from-scratch re-embed.
- **Available memory touched the floor.** During run 3's embeddings pass it reached **4.0 GB**,
  exactly at the 4.0 GB floor (a trip needs < floor). On a busier 24 GB Mac, that floor, unchanged by
  this fix, would end the run as exit 4. That is intended backstop behaviour, not the bug fixed
  here.
- **Run 2's "proposed" mode was emulated.** It raised the compressor ceiling out of reach instead of
  running the new code. Run 3 uses the real branch code.
- **One Mac.** The Mac Studio (64 GB) and Mac Mini (32 GB) weren't re-measured.
- **Real side effects.** Runs 1–2 pushed pulse output and wrote normal job logs.


## PR 298 takeover review — 2026-10-02

Five review findings were fixed in the existing resolver, report and outcome classifier:
disabled checks omitted thresholds; null thresholds claimed config provenance; non-object root
config was silent; sub-byte thresholds silently truncated to zero; strict scheduler policy ignored
returned collector errors. The last fix centralizes strict policy in `classify_sync_outcome` and
preserves nonfatal embedding deferrals and optional next-actions notes. No new subsystem or writer.

| Check | Result | Receipt |
|---|---|---|
| Settings regressions on incoming eec7071 | 11 failed before correction | [red](review-settings-red.txt) |
| Strict-policy regression before correction | strict returned-error case failed; nonfatal controls passed | [red](review-strict-red.txt) |
| Focused guard/doctor/refresh suites | 179 passed, 2 subtests passed | [green](review-focused-green.txt) |
| Full pre-integration suite | 2888 passed, 21 skipped, 11 xfailed | [receipt](review-premerge-suite.txt) |
| Full integrated suite at 71786aa | 2891 passed, 21 skipped, 11 xfailed, 148 subtests passed | [receipt](review-integrated-suite.txt) |
| Ruff, format, mypy, repository ratchets, docs and frontdoor | all passed | [receipt](review-static.txt) |
| Integrated doctor | guard OK; overall passed with environment warnings | [filtered excerpt](review-doctor-excerpt.txt) |

Reproduction: `PYTHONPATH=src:HiQS python -m pytest tests/ HiQS/tests -q` using Python 3.13
and the existing installed dependencies. Focused run used `tests/test_job_guard_footprint.py`,
`tests/test_doctor_launchd.py`, `tests/test_job_guard_wiring.py`, `tests/test_daily_sync_exit.py`,
`tests/test_collector_registry.py`, and `tests/test_github_knowledge.py`. The settings red run
selected `null_threshold or non_object_config or sub_byte_threshold or reports_job_guard_off`;
the strict red run selected `strict_mode_rejects or strict_mode_keeps`.
[Source hashes](review-source-manifest.json) identify the final integrated code and tests.

External review: CodeRabbit's two documentation changes were already implemented; its reserved
exit-code finding was withdrawn. Greptile supplied no technical findings because its trial expired.
The prior Codex relay's accepted worker-thread limitation remains. Two read-only review lanes
checked the guard and refresh/doctor seams; the refresh lane found the strict-policy gap and then
verified the correction. The graph generation predates the PR, so changed code and excluded shell
paths were checked directly against source. No new independent model-service review was claimed.

Integration: development 4652361 is merged into the PR branch. Both roadmap entries and upstream
fleet/CLIO behavior are preserved. Version 0.98.0 replaces the PR's conflicting 0.97.0 allocation.

### Review limitations and deviations

An initial full run crossed the version edit and failed only the version consistency assertion
(2875 passed). It is not a clean baseline: [mixed-revision receipt](review-initial-mixed-revision.txt).
The subsequent full runs used stable source and passed. Raw test receipts replace machine paths;
the doctor excerpt omits private project/device data and unrelated checks. The full suite retains
21 existing skips and 11 expected failures, including superseded MLX tests, absent local web output,
and existing quarantines. Hardware load, 48-hour soak and seven-day qualification were not repeated;
background-thread mid-run interruption remains outside this review. Nothing was merged or deployed.
