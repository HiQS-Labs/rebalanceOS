# CLIO

## Upstream — edit here first

This folder (`rebalanceOS/utils/clio-capture/`) is **CLIO's canonical source**. It is published
unchanged to [HiQS-Labs/XYZ-CLIO](https://github.com/HiQS-Labs/XYZ-CLIO).
The exceptions are this README and `LICENSE`; XYZ-CLIO keeps its own at the repository root.

- Make every CLIO change here first, through a reviewed rebalanceOS PR, then publish it to
  XYZ-CLIO. Never edit XYZ-CLIO's copy directly.
- Devices get CLIO only through Skills Army HQ deployment from this repository, never by
  hand-copying files or editing installed hooks.
- The direction flipped with GH-362, which synced this folder to XYZ-CLIO `bacd26f`.

A Claude Code skill that installs a `UserPromptSubmit` hook logging every prompt
you submit — across every repo, on one machine — to a single centralized file:
`~/.claude/prompt-log.jsonl`.

Each line records a timestamp, repo name, git branch, machine name, session ID,
and the prompt text (with auto-injected context like `<ide_selection>` blocks
stripped out, so it's a record of what you actually typed).

An optional second script converts that JSONL into human-readable Markdown —
newest entry first — at any location you choose, such as a note in an Obsidian
vault. It can run on demand or on a 5-minute `launchd` schedule (macOS).

**Install on a device:** from the Skills Army deployed copy, run `clio-runtime.sh status`, then
`clio-runtime.sh install --apply` (see [SKILL.md](SKILL.md)). It links the hooks into the deployed
copy and records a receipt, so nothing is hand-copied.

See [INSTALL.md](INSTALL.md) for the full install, verify, export, auto-sync, and
uninstall instructions.

## Why

If you use Claude Code across many repos and machines, there's no built-in way
to see everything you've asked it over time. This gives you one append-only
log you can grep, sync to notes, or just keep as an audit trail.

## Use cases

- **Cross-device recall.** You work on the same project from a laptop and a
  desktop (or any multiple-device setup) and want to answer "where/when did I
  ask Claude to do X on this project?" without digging through separate
  session histories per machine.
- **Branch-level recall.** Each entry records the git branch checked out at
  prompt time, so you can trace a specific ask back to the branch it happened
  on — even after that branch is merged or deleted.
- **Cross-project AI memory, layered into a "second brain."** Point the
  Markdown export at an Obsidian vault and, once that vault is vectorized/
  indexed for retrieval, an AI assistant can search across *what you asked
  Claude Code to do*, alongside your other notes — one more layer in a
  multi-layered personal knowledge system, not just a flat log file.

## Requirements

- macOS or Linux
- [`jq`](https://jqlang.org/) (`brew install jq` / `apt install jq`)

## License

Apache License 2.0 — see [LICENSE](LICENSE).

This project is provided **"AS IS," WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND**, either express or implied (Apache 2.0 §7). It runs on your machine
with a hook that shells out and edits your Claude Code `settings.json` —
read the scripts before running them, and use at your own risk.
