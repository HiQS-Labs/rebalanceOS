# Sleuth reminder sync

`rebalance sleuth-sync` pulls Slack reminders into the local `sleuth_reminders`
SQLite table (consumed by the morning brief, dashboard, and the
`sleuth_sync_reminders` MCP tool).

**Production is read from a published file — no inbound access to the Sleuth
server, no SSH tunnel, no open port.** The Sleuth box pushes its reminders to a
private git repo; rebalance-OS reads the locally-synced copy. (This replaced an
earlier SSH-tunnel approach — if you're looking for `127.0.0.1:12020` or
`install_sleuth_tunnel_scheduler.sh`, they're gone.)

## How it works

```
Sleuth box (systemd timer, every 5 min)
   └─ GET  http://127.0.0.1:2020/.../reminders?format=rebalance   (loopback, on the box)
   └─ PUT  Hypercart-Dev-Tools/rebalance-git-pulse : sync/sleuth/reminders-<ws>.json   (GitHub contents API)
                                                  │
                          git fetch + upstream blob  ▼
rebalance-OS  ──reads──►  upstream sync/sleuth/reminders-<ws>.json   (local file fallback)
```

- **Publisher** lives in the `sleuth-app` repo under `deploy/reminders-export/`
  (systemd `sleuth-reminders-export.timer`). It only commits when the reminder
  data actually changed.
- **Consumer** points `base_url` at the local file. A `base_url` that is a
  `file://` URL or a plain `/…`/`~/…` path is read directly; an `http(s)://`
  `base_url` still uses the live API (that's how **dev** works — the dev box is
  reachable directly).
- **Freshness:** `refresh_index` / the daily launchd sync does a best-effort
  `git fetch` and reads the upstream export blob without rebasing, stashing or changing
  the worktree/index. Fetch failure is reported with an explicit local-cache fallback;
  a successful fetch is not proof of successful ingest. Setup separately uses the existing
  shared writer lock to refresh an already-cloned checkout before configuring the file source.

## Setup on a device

**One command** — clones the export repo, configures rebalance, and verifies:

```bash
bash scripts/setup_sleuth_file_source.sh
# options: --workspace neochrome  --clone-dir <path>  --repo-url <url>
```

The clone folder differs per Mac (`~/git-pulse-sync` on one,
`~/Documents/GitHub/rebalance-git-pulse` on another). The script and the steps below
ask this Mac's own config with `rebalance config fleet-enroll --print-clone`
(exit 0 found, 3 nothing configured, 2 broken or two different clones — stop).
Only when nothing is configured does it fall back to `~/git-pulse-sync` (GH-325).

Manual equivalent, if you prefer:

1. **Find or create this Mac's clone** of the private export repo:
   ```bash
   rc=0; CLONE="$(rebalance config fleet-enroll --print-clone)" || rc=$?
   case "$rc" in
     0) ;;                                   # this Mac's configured clone
     3) CLONE="$HOME/git-pulse-sync" ;;      # nothing configured yet: choose a folder
     *) echo "stop: fix the pulse config first (see message above)"; exit 1 ;;
   esac
   [ -d "$CLONE/.git" ] || git clone https://github.com/Hypercart-Dev-Tools/rebalance-git-pulse.git "$CLONE"
   ```
2. **Point rebalance-OS at the local file** (token is unused for a file source —
   any non-empty placeholder):
   ```bash
   rebalance config set-sleuth \
       --base-url "$CLONE/sync/sleuth/reminders-neochrome.json" \
       --token file-source \
       --workspace neochrome
   ```
3. **Verify:**
   ```bash
   rebalance doctor                          # sleuth → configured · export Nh old
   rebalance sleuth-sync --active-only --json | head
   ```

Either way — no SSH key on the prod box, no tunnel, no firewall change. Dev is
unchanged: `--base-url http://<dev-host>:2020 --token <token> --workspace neochrome-dev`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Sleuth reminders file not found: …` | The clone or configured local fallback is missing | Use the setup command above to resolve/create the clone. To refresh an existing checkout manually: `rebalance config refresh-pulse-clone --path "$CLONE"` |
| `doctor`: `published export is stale — heartbeat … (Nh ago)` | The publisher timer is dead **or** the local sync/clone is stuck (the publisher stamps an hourly `exportGeneratedAt`; doctor warns past ~3h) | Check the publisher: `systemctl list-timers sleuth-reminders-export.timer` on the Sleuth box. Locally, normal sync fetches and reads the upstream blob — inspect `source_refresh` and any fallback error. For a manual checkout refresh use `rebalance config refresh-pulse-clone --path "$CLONE"` |
| `… refusing to reconcile (wrong file/endpoint?)` / `missing filters.activeOnly` / `source.type …` | Contract guard tripped — wrong workspace file, truncated/partial export, or publisher drift. **No DB rows were changed.** | Confirm `base_url` points at the right `reminders-<workspace>.json` and the publisher is healthy; the guard is intentional — it refuses to retire reminders from a bad payload |
| `Sleuth reminders file is invalid JSON` | Partial write / merge conflict in the clone | Inspect the reported upstream/local source and `git -C "$CLONE" status`; repair the invalid export at its source, then rerun sync. For a checkout refresh use `rebalance config refresh-pulse-clone --path "$CLONE"` |
| Want the live API instead (dev/debug) | — | `rebalance config set-sleuth --base-url http://<host>:2020 --token <token> --workspace <ws>` |

**Freshness model:** the publisher stamps an hourly-rounded `exportGeneratedAt`; the consumer persists it and `rebalance doctor` compares **that** (not the local `last_synced_at`, which re-reads keep bumping) to now — so a dead publisher is visible. Before each read the sync does a best-effort, **non-destructive** refresh of the export clone (`git fetch` + `git show` of the upstream export blob, without worktree/index writes, rebase or autostash); status is reported as `source_refresh`.

## Related

- `scripts/setup_sleuth_file_source.sh` — one-command device onboarding (clone + configure + verify)
- `sleuth-app` repo → `deploy/reminders-export/` — the publisher (script + systemd units + `install.sh`)
- `UPGRADE.md` — full credential migration for a device
