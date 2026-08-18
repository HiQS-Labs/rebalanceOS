---
name: git-pulse-daily-synthesis
aliases:
  - daily-recap
description: >
  Generates the daily vault synthesis (pulse activity summary, then a Git Pulse multi-device
  activity summary) using Gemini and appends both to today's Obsidian note.
  Use this to manually trigger the daily synthesis. Pass flags like --dry-run or --force as needed.
---

# `git-pulse-daily-synthesis` Skill

This skill invokes the `utils/daily_synthesis.py` script (GH-74 — merged with the former
`obsidian_daily_sync.py`; see its module docstring). A run does both syntheses in one process: the
pulse-activity summary block lands first, then the Git Pulse summary block below it.

**Important Note:** This skill complements (but does not replace) `git-pulse-exec-recap` and `git-pulse-team-recap`. Those skills generate narrative prose into standalone recap files, whereas this skill generates the small daily blocks appended to your Obsidian Daily Note.

**Optional second destination (not primary, Git Pulse block only):** if `git_pulse_clio_enabled` is set in pulse config (`rebalance.ingest.config.set_pulse_config(git_pulse_clio_enabled=True)`), the Git Pulse block is ALSO upserted into a growing, git-committed log at `<pulse_target_path>/CLIO/git-pulse-daily-log.md` — one dated block per day, oldest content never overwritten. This works even without an Obsidian vault configured, since it's decoupled from the vault-readiness check. The primary path (writing to the Obsidian vault) is unaffected either way.

## Execution

When the user calls `/git-pulse-daily-synthesis [flags]`, execute the following bash script to invoke the python script.

```bash
# Resolve repo root relative to the skill execution context
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo ".")"

# Pass arguments directly to the python script
cd "$REPO_ROOT" && .venv/bin/python utils/daily_synthesis.py $ARGUMENTS
```

If the `--dry-run` flag is passed, ensure you print the output of the script back to the user, as the blocks will not be written to the vault.
