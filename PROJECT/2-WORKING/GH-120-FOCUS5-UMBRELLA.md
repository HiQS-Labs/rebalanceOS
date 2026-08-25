---
title: "Focus 5 features + adjacent fixes"
status: "In progress"
created: 2026-08-24
updated: 2026-08-24
owner: noel
gh_issue: 120
goal: "Add a horizontal layout mode to Focus 5, and stop the CLIO prompt-log writer failing silently."
release: "0.70.0 Green Board"
---

# GH-120 — Focus 5 umbrella

Ongoing umbrella. Items are checked off in [#120](https://github.com/HiQS-Labs/rebalanceOS/issues/120);
each substantial one may take its own PR against the shared branch
`feat/gh120-focus5-umbrella`.

## Status

| Item | State |
|---|---|
| 1. Focus 5 horizontal layout mode | in progress |
| 2. CLIO prompt-log writer fails silently | diagnosed, not fixed |

## 1. Focus 5 — horizontal layout mode

`.f5-card` is `display: flex; flex-direction: column` (`src/rebalance/web.py:302-303`), so each
repo's three sections — health, newest PR, activity — stack top to bottom, and `.f5-grid` places
five such cards side by side.

Keep that as the default; add a switch that lays each repo's data out **left to right inside its
own card**. The change is within the card, not to roster ordering.

Constraints worth carrying into the build:

- The card body is `{_f5_health}{_f5_pr}{_f5_activity}` — those three become the horizontal columns.
- A horizontal card wants full page width, so the mode likely also collapses `.f5-grid` to one
  column and stacks the five repos vertically. Confirm against a real screen before committing.
- `.f5-views` (the Focus 5 / Dirty Five segmented control) is the pattern to copy for the toggle.
- Persist the preference in `localStorage`, as the health banner caret does.
- Focus 5 and Dirty Five share `_focus5_body`, so the switch must serve both.
- `Open ↗` and the `✕` hide control must stay reachable in both modes.

## 2. CLIO prompt-log writer fails silently

Diagnosed 2026-08-24. The launchd job `com.claude.prompt-log-to-md` reports
`LastExitStatus = 0` while its own stdout log shows `state: never-delivered=7`, unchanged across
at least six consecutive runs. Seven prompts have never been written and no run recovers them.

stderr says why:

```
grep: /Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md: Interrupted system call
cat:  /Users/noelsaw/Documents/Noel Saw/0. Claude Prompts.md: Interrupted system call
```

Desktop & Documents iCloud sync is on, so the 1.3 MB target sits on a cloud-managed volume. While
the file provider pages a dataless file back in, `grep`/`cat` are interrupted; the script reads a
failed read as an empty one, concludes those prompts are absent, writes nothing, and exits 0.

Two defects, the second of which hid the first:

1. No EINTR retry. Reads of a cloud-managed file must be retried, or the file materialised
   (`brctl download`) before reading.
2. A failed read exits 0. A run that could not read its own target is not a successful run.

Also: the scheduled script is `~/.claude/hooks/prompt-log-to-md.sh`, **not** the repo copy at
`utils/CLIO/prompt-log-to-md.sh`. Reconcile the two, or a fix lands in a file nothing runs.

## Links

- Issue: [#120](https://github.com/HiQS-Labs/rebalanceOS/issues/120)
- Release manifest item: `mfi-01M0V940ASQHCQHZF33GVS34V8` → 0.70.0 Green Board
