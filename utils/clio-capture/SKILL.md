---
name: clio-capture
description: Install, repair, upgrade, check or remove CLIO prompt capture on this device. Runs clio-runtime.sh from the Skills Army deployed copy, so the capture hooks link to the deployed bytes and upgrade with each Git Pulse Sync pull. Use for "install CLIO capture", "repair/upgrade CLIO on this Mac", "is CLIO capture healthy here", or the per-device CLIO checklist. Not for searching history (that is the clio skill) or SQLite activation and fleet setup (clio-store.py commands in INSTALL.md).
---

# CLIO capture runtime

Run the installer from this skill's own folder, which is the Skills Army deployed copy
(`${XYZ_SKILLS_ROOT:-~/git-pulse-sync/Deployed Skills}/clio-capture`). It refuses to run from a
repository checkout.

```bash
bash "<this skill's folder>/clio-runtime.sh" status            # read-only; exit 1 means install would change something
bash "<this skill's folder>/clio-runtime.sh" install           # preview: what would change, what would be backed up
bash "<this skill's folder>/clio-runtime.sh" install --apply   # converge (repair and upgrade are the same operation)
bash "<this skill's folder>/clio-runtime.sh" uninstall --apply # reverse only what the receipt says this tool did
```

## What it manages

- `~/.claude/hooks/{clio-store.py, prompt-log-to-md.sh, clio-codex-tail.sh, clio-agy-tail.sh}`: symlinks into
  this folder, so a Pulse pull upgrades them.
- `~/.claude/hooks/{clio-capture.sh, log-prompt.sh}`: generated from `INSTALL.md`'s heredocs. `status`
  reports them `stale` after a pull changes the writer; run `install --apply` to refresh.
- The Claude Code `UserPromptSubmit` registration, plus the ZCode registration when `~/.zcode` exists.
- On macOS, the Codex and Agy tailer launchd jobs, created only when absent.
- A receipt at `~/.claude/clio-runtime.json` (source, HQ commit, digest, owned paths, backups).

Existing hand-installed files it replaces are moved to `~/.claude/clio-runtime-backups/<UTC>/`
first, and `uninstall` restores them. A hook edited after install is left in place on uninstall
and reported as `drifted`.

## What it never touches

App skill links (Skills Army HQ's job), the SQLite store and `~/.claude/clio-storage.json`
(activation and fleet setup stay explicit `clio-store.py` commands), the exporter's launchd job
(`com.claude.prompt-log-to-md`, whose note path and interval are per device), and your prompt data.

Requires `jq` and `python3`; launchd jobs are macOS only. Full manual procedure and background:
[INSTALL.md](INSTALL.md).
