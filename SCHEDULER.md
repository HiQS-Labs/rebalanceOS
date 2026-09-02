# Scheduler Policy

This table is the single source of truth for the launchd fleet. Every plist
template in `scripts/`, every wrapper script, and every installer must agree
with it — a divergence is a bug. `tests/test_scheduler_policy.py` enforces the
machine-checkable columns (label, cadence, wrapper, entry call/scope) against
the actual templates and scripts, and checks that this file documents every
job.

## Job table

| Job (label suffix) | Cadence | Wrapper | Work | Prerequisites | Outputs |
|---|---|---|---|---|---|
| `daily-sync` | daily 06:30 + RunAtLoad (boot/login catch-up) | `scripts/daily_sync.sh` | `refresh_index(db_path)` — default recipe: all raw sources + code/semantic/sync | vault path, GitHub token, calendar/sleuth auth as configured | SQLite knowledge base fully refreshed; dashboard note write-back |
| `obsidian-vault-embeddings` | hourly at :15, 06:15–23:15 | `scripts/obsidian_vault_embeddings.sh` | `refresh_index(db_path, scope=["vault", "semantic"])` | `vault_path` in temp/rbos.config | vault raw tables + semantic index fresh within the hour |
| `github-sync` | hourly at :45, 06:45–23:45 | `scripts/github_sync.sh` | `refresh_index(db_path, scope=["github", "focus5"])` | GitHub token (keyring/config) for github; Focus 5 needs none | github raw tables fresh (semantic backfill deferred to daily-sync); Focus 5 roster recomputed hourly |
| `pulse-sync` | hourly at :00, 06:00–23:00 | `scripts/pulse_sync.sh` | `publish_pulse(db_path, dry_run=False, push=True)` | pulse_* keys in temp/rbos.config; local clone at pulse_target_path | markdown status page pushed to private repo (only when changed) |
| `pulse-web-sync` | every 30 min at :08/:38, 06:00–23:38 | `scripts/pulse_web_sync.sh` | `scripts/pulse_web.py` | `vault_path` in temp/rbos.config (locates "0. Goals.md") | `web/pulse.html` regenerated atomically (local only, no network) |
| `pulse-server` | daemon: RunAtLoad + KeepAlive, ThrottleInterval 30s | `scripts/pulse_server.sh` | `scripts/pulse_server.py --port 8767` | port 8767 free | FastAPI server on 127.0.0.1:8767 (loopback only) |
| `pulse-warning-watch` | every 15 min at :07/:22/:37/:52, around the clock + RunAtLoad | — (python direct) | `scripts/pulse_warning_watch.py --url http://127.0.0.1:8767/` | pulse-server running on 8767 | `temp/pulse-warning-watch.jsonl` (one record per check) |
| `health-check` | hourly at :10, around the clock | — (python direct) | `scripts/health_issue_reporter.py --close` (FAIL-only, no LLM) | GitHub token for issue filing | GitHub issues opened/closed on failing doctor checks |
| `health-check-triage` | 3×/day at 08:25, 14:25, 20:25 | — (python direct) | `scripts/health_issue_reporter.py --warn --close --llm-triage --llm-daily-limit 8 --llm-max-per-run 5` | ANTHROPIC_API_KEY in rendered plist or keyring | LLM-triaged GitHub issues; quota circuit breakers CB-1/2/3 |
| `obsidian-rollover` | daily 00:40 (or next wake); RunAtLoad must stay **false** | `utils/obsidian_rollover.sh` | `utils/obsidian_daily_rollover.py` | Full Disk Access via bash wrapper (TCC) | daily note rolled over; log in `~/Library/Logs/rebalance-os/` |
| `hiqs-digest` | 2×/day at 13:05, 17:05 (or next wake); RunAtLoad **false**; a catch-up before 17:05 takes the 13:05 slot, and a post-midnight catch-up skips itself | `scripts/hiqs_digest.sh` | `utils/hiqs_digest.py` — three deterministic collectors (today's github tables, `rebalance doctor --json`, date-bounded semantic query filtered to github sources), then one Gemini synthesis | rebalance venv + Gemini API key; Full Disk Access via bash wrapper (TCC, for the doctor vault reads); pulse_target_path clone | one markdown digest per slot pushed to `<pulse_target_path>/digests/hiqs-DATE-SLOT.md` (git-committed+pushed); AEGIS Sleuth's snapshot-relay posts it to Slack |
| `daily-synthesis` | daily 18:20 (or next wake); RunAtLoad **false**; a post-midnight catch-up skips itself | `utils/daily_synthesis.sh` | `utils/daily_synthesis.py` — Gemini daily-activity summary from the structured pulse snapshot, then Gemini synthesis of `view.sh --today` multi-device git activity (GH-114), in that order, one process (GH-74) | rebalance venv + Gemini API key; Full Disk Access via bash wrapper (TCC) | idempotent AI summary block, then idempotent Git Pulse summary block, appended to `0. Today's Notes.md` (if vault configured) AND/OR the Git Pulse block upserted into `<pulse_target_path>/CLIO/git-pulse-daily-log.md` (if `git_pulse_clio_enabled`, git-committed+pushed); log in `~/Library/Logs/rebalance-os/` |

> **Do not put a literal `|` inside a cell of the table above, even escaped as
> `\|`.** Two consumers split these rows on the pipe character —
> `doctor._scheduler_policy_jobs` and `scripts/stack.sh`'s `load_policy` — and
> neither implements Markdown escaping. A pipe inside a cell shifts every column
> after it, which silently drops a job from the managed set rather than raising
> an error. Write pipelines as prose, or name the wrapper script instead.

All labels are prefixed `com.rebalance-os.`. Experimental/utility agents
(`com.user.git-pulse`, `com.user.stickies2obsidian`) live in `experimental/`
and `utils/stickies-to-obsidian/` with their own installers and are out of
scope for this table.

## Freshness model (intentional, not accidental)

The hourly stagger is deliberate — readers trail writers inside each hour, and
since GH-175 **no two jobs share a minute**:

```
:00 pulse-sync (reads)
:07 pulse-warning-watch      :22      :37      :52
:08 pulse-web-sync (reads)   :38
:10 health-check
:15 obsidian-vault-embeddings (writes vault + semantic)
:25 health-check-triage (08/14/20 only)
:45 github-sync (writes github raw only)
06:30 daily-sync (writes everything, incl. github → semantic backfill)
00:40 obsidian-rollover      18:20 daily-synthesis
13:05 hiqs-digest           17:05 hiqs-digest
```

- **`daily-synthesis` used to be two jobs** (`obsidian-daily-sync` at 18:20,
  `git-pulse-daily-synthesis` at 18:30) with an ORDERING DEPENDENCY between
  them: when both destinations were configured, the Git Pulse block had to
  land *after* the GH-112 AI Daily Summary block, enforced only by the second
  job firing 10 minutes after the first (GH-175) — a sleep/wake catch-up could
  invert that. GH-74 merged them into one process: the pulse summary is
  upserted first, then the git-pulse summary, in one read-modify-write, so the
  order is guaranteed by the code, not by two independent launchd fire times.

- **pulse-web-sync moved off :00 for correctness, not tidiness** (GH-175). It is
  a derived read-only stage over what `pulse-sync` writes at :00; sharing that
  minute risked rendering from half-written state. :08 puts it clearly after.
- **pulse-warning-watch moved off the quarter hours** — on :00/:15/:30/:45 it
  collided with `pulse-sync`, `obsidian-vault-embeddings`, `pulse-web-sync` and `github-sync` in
  turn. Same 15-minute cadence, no shared minute.
- This is *same-minute* de-confliction only. It does **not** address run-window
  overlap: `daily-sync` runs ~25–30 min from 06:30 and still spans `github-sync`
  at :45. That overlap is handled by GH-131's bounded SQLite retry.

- **obsidian-vault-embeddings includes the `semantic` scope intentionally** — vault ingest
  alone only updates raw tables; the semantic backfill+embed is what makes a
  note edited at 10:05 searchable by 10:16.
- **github-sync intentionally excludes `semantic`** — hourly embedding of
  github docs is not worth the cost; the 06:30 daily-sync closes the gap. The
  lag is observable as the `github_documents_missing_from_semantic` drift
  metric (`index_status` MCP tool / `refresh_index` summary).
- **github-sync also carries `focus5`** — the Focus 5 collector is opt-in
  (`included_in_all=False`) and would otherwise never run unattended, leaving
  the roster frozen until a manual ↻ Refresh. It piggybacks the hourly github
  cadence rather than running its own launchd job: a device-local git scan
  (~30s, no network, no GitHub token) that recomputes `focus5_roster`. The web
  page stays non-blocking (PR #72) — this job is the background writer it reads.
- **pulse-sync and pulse-web-sync are read-only derived stages** — they render
  whatever the ingest jobs last wrote and never refresh sources themselves.
- **pulse-warning-watch depends on pulse-server** being up on 127.0.0.1:8767;
  a down server is itself a finding the watcher records.

## Shared mechanics

- Wrapper scripts source `scripts/lib/scheduler_common.sh`: env bootstrap
  (repo root, venv python, `PYTHONPATH=src`), per-day logs in `temp/logs/`
  (`<job_name>_YYYY-MM-DD.log`, dashes→underscores), job-lifecycle events
  (`job_started`/`job_completed`/`job_failed`) appended to
  `temp/logs/auth_activity.jsonl`, and retention trimming (30 days for
  daily-sync, 14 for the rest).
- Installers source `scripts/lib/install_common.sh`: chmod the wrapper,
  always-unload, render the template (`{{REBALANCE_DIR}}`, `{{PYTHON}}`,
  `{{HOME}}`), `plutil -lint`, load, poll-verify registration. Rendered plists
  live in `~/Library/LaunchAgents/` (gitignored).
- Python-direct jobs (no wrapper) log via launchd `StandardOutPath`/
  `StandardErrorPath` into `temp/logs/` instead of the dated wrapper logs;
  obsidian-rollover logs to `~/Library/Logs/rebalance-os/` because
  `~/Documents` is TCC-protected.

## Runbook

**`scripts/stack.sh` is the front door.** It reads the job table above as its
manifest — it keeps no list of its own, so this document stays the only place
the fleet is defined. Anything not in that table is *unmanaged*: `stack.sh`
shows it under a separate heading and never loads, unloads or deletes it. That
is what keeps the deferred 3-Eyes plists safe (GH-59).

| Task | Command |
|---|---|
| Check fleet status | `bash scripts/stack.sh status` |
| Bring the whole stack up | `bash scripts/stack.sh up` |
| Unload everything (plists kept) | `bash scripts/stack.sh down` |
| Reload everything | `bash scripts/stack.sh restart` |
| Health check | `bash scripts/stack.sh doctor` |
| Preflight without changing anything | `bash scripts/stack.sh verify` |
| Unload **and delete** managed plists | `bash scripts/stack.sh purge` |
| Install / reinstall ONE job | `bash scripts/install_<job>_scheduler.sh` (daily-sync: `install_scheduler.sh`) |
| Run a job now | `bash scripts/<job>.sh` |
| Tail a job log | `cat temp/logs/<job_name>_$(date +%Y-%m-%d).log` |
| Job lifecycle history | `temp/logs/auth_activity.jsonl` (also `rebalance serve` → /auth-log, the System Log page) |
| Health-check state changes | same log, `source=health` — written on TRANSITION only by `rebalance.ingest.health_log`, never once per run |
| Verify templates match installed plists | render with the installer substitutions and `diff` against `~/Library/LaunchAgents/` |

Plists pin absolute paths, so a job belongs to **one checkout**. `stack.sh up`
prints the root it is about to bind to and refuses to move a fleet that is
bound somewhere else unless you pass `--force`; `status` shows the current
binding in its `BOUND TO` column. Running `up` from the wrong clone is
otherwise a silent fleet-wide migration (GH-36, GH-59).

The 12 per-job installers remain supported and are what `stack.sh` calls
underneath. They stay until `stack.sh` has been proven on a second machine.

Secrets: never put API keys in templates (tracked in git). The
health-check-triage job reads `ANTHROPIC_API_KEY` from the rendered plist or
keyring; reinstalling overwrites a hand-added key (the installer warns).
