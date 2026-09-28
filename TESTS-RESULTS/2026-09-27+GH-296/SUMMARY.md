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
