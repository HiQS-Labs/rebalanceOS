# [SHAKEDOWN] rebalance — 2026-10-21 20:49

**Target:** rebalance (`.claude/skills/rebalance`)
**Target HEAD:** `543f6de` — Publish watched GitHub repos for Sleuth issue stream (#342)
**Env:** Darwin 24.6.0 arm64 · GNU bash 3.2.57
**Verdict:** [clean] — the 2026-08-17 `<skill_dir>` path bug is fixed (GH-45 locator); the documented locator resolves every standard install and fails loudly elsewhere, and the anchored collector survives all eight scenarios.

Re-run for #129 (0.70.0 Green Board gate #66) of [2026-08-17](../2026-08-17/rebalance-1158.md).

## Static audit

```text
## Shakedown static audit
Target: rebalance (.claude/skills/rebalance)
Target HEAD: 543f6de Publish watched GitHub repos for Sleuth issue stream (#342)
Env: Darwin 24.6.0 arm64

### Invocation paths (graded from SKILL.md)
[ok]  L70  $1/collect.sh  — anchored to a variable
[block]  L75  collect.sh  — bare name
[block]  L95  collect.sh  — bare name
[ok]  L107  $REBALANCE_SKILL/collect.sh  — anchored to a variable
[block]  L115  collect.sh  — bare name
[block]  L207  pdda.sh  — bare name
[block]  L210  test-pdda-annotation.sh  — bare name

### Bundled-script hygiene
shebang [ok]  exec-bit [warn]  self-loc [n/a]  — collect.sh
shebang [ok]  exec-bit [warn]  self-loc [block]  — test-pdda-annotation.sh
shebang [ok]  exec-bit [warn]  self-loc [block]  — test-skill-locator.sh
```

Adjudication: every `[block]` invocation is prose, not a command. L75/L95/L115 are inside the
locator function (`_rsd_ok` checks and the stderr message) or the explanation under it; L207 says
the collector *never* runs `pdda.sh`; L210 names the bundled smoke test. The only documented
command is L107, which is anchored. Both test scripts self-locate with
`HERE=$(cd "$(dirname "$0")" && pwd -P)` (the audit's regex looks for `BASH_SOURCE`, so it grades
them `[block]` — false positive). Missing exec bits are intended: every invocation goes through `bash`.

## Live harness

As-documented = the SKILL.md locator block verbatim + the documented invocation, with the staged
skill dir as the collector's only scan root (bounded, private — no device-wide scan).

```text
### Run A — as documented (locator + bash "$REBALANCE_SKILL/collect.sh" "{SKILL}")
  control(CWD=skill)   found/err  exit 1   rebalance: could not locate the rebalance skill …
  foreign CWD          found/err  exit 1   rebalance: could not locate the rebalance skill …
  nested CWD           found/err  exit 1   rebalance: could not locate the rebalance skill …
  spaces in path       found/err  exit 1   rebalance: could not locate the rebalance skill …
  project install      found      exit 0
  user install         found      exit 0
  symlinked install    found/err  exit 1   rebalance: could not locate the rebalance skill …
  stripped exec bit    found/err  exit 1   rebalance: could not locate the rebalance skill …
  -> Run A: no discovery bug under these scenarios

### Run B — proposed (anchored): bash "{SKILL}/collect.sh" "{SKILL}"
  all eight scenarios   found      exit 0
  -> Run B: survives every scenario
```

The six Run A `exit 1` rows are the locator's designed loud refusal, not a discovery bug: the
harness stages those scenarios in throwaway directories that are not a `.claude/skills/rebalance`
install, and the locator only accepts `REBALANCE_SKILL_DIR`, a project install found walking up
from CWD, or `$HOME/.claude/skills/rebalance`. Both real install layouts resolve and run.

The skill's own locator matrix (`test-skill-locator.sh`, GH-45) also ran at this HEAD:
`PASS — all GH-45 locator shakedown checks green` (includes symlinked installs, nested CWD,
spaces, bad override failing loudly, and a byte-identical scan root).

## Proposed patch

None required. Optional nit: the audit's self-location check would stop false-flagging the two
test scripts if they used `${BASH_SOURCE[0]}` instead of `$0` — behaviour is identical under `bash <file>`.

## What I could not verify

- Shakedown tests the documented shell command under varied CWD/install conditions; it does not
  instrument Claude Code's internal skill resolver.
- The collector scanned only the staged skill directory, not its default device-wide roots — this
  verifies discovery, not the collector's inventory.
- The Step 1 MCP call was not exercised (runtime behaviour, not script discovery).
