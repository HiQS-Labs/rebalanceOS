# [SHAKEDOWN] rebalance — 2026-08-17 11:58

**Target:** rebalance (`.claude/skills/rebalance`)
**Target HEAD:** `465aa90` — feat: 0.73.0 Subsystem Unification — one implementation of each shared primitive (#40)
**Env:** Darwin 24.6.0 arm64 · GNU bash 3.2.57
**Verdict:** [path bug reproduced] — the documented command leaves `<skill_dir>` unresolved; an invocation anchored to the staged skill directory survived all eight scenarios.

## Static audit

```text
## Shakedown static audit
Target: rebalance (/Users/noelsaw/Documents/GH Repos/rebalanceOS/.claude/skills/rebalance)
Target HEAD: 465aa90 feat: 0.73.0 Subsystem Unification — one implementation of each shared primitive (#40)
Env: Darwin 24.6.0 arm64

### Invocation paths (graded from SKILL.md)
[warn]  L64  /collect.sh  — absolute path — survives any CWD, but hardcoded to one machine/layout
[block]  L154  pdda.sh  — bare name — relies on PATH; almost never on PATH in another session
[block]  L157  test-pdda-annotation.sh  — bare name — relies on PATH; almost never on PATH in another session

Note: this greps every `.sh` token, including illustrative examples in prose — a meta-skill
that documents bad paths on purpose will show blocks for those examples; read in context.

### Bundled-script hygiene
shebang [ok]  exec-bit [warn]  self-loc [n/a]  — collect.sh
shebang [ok]  exec-bit [warn]  self-loc [block]  — test-pdda-annotation.sh

Verdict: [path bug reproduced] — at least one blocker
```

Adjudication: the `pdda.sh` token is explicitly named as something the collector never runs, and
`test-pdda-annotation.sh` is a prose reference rather than a documented invocation. The test does
self-locate with `HERE=$(cd "$(dirname "$0")" && pwd -P)`. Both scripts are intentionally invoked
through `bash`, so their absent execute bits do not block discovery. The load-bearing finding is
line 64: `<skill_dir>` is explanatory prose inside the command itself, not a resolved path.

## Live harness

The collector was given the staged skill directory as its sole scan root. This exercises discovery
without performing its default device-wide scan.

```text
## Shakedown live harness — rebalance

### Run A — as documented: bash "<skill_dir>/collect.sh" "{SKILL}"
  control(CWD=skill)   NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  foreign CWD          NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  nested CWD           NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  spaces in path       NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  project install      NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  user install         NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  symlinked install    NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  stripped exec bit    NOT-FOUND  exit 127 bash: <skill_dir>/collect.sh: No such file or directory
  -> Run A: DISCOVERY BUG reproduced (script not found under some condition)

### Run B — proposed (anchored): bash "{SKILL}/collect.sh" "{SKILL}"
  control(CWD=skill)   found      exit 0
  foreign CWD          found      exit 0
  nested CWD           found      exit 0
  spaces in path       found      exit 0
  project install      found      exit 0
  user install         found      exit 0
  symlinked install    found      exit 0
  stripped exec bit    found      exit 0
  -> Run B: survives every scenario

Verdict: [path bug reproduced] — the as-documented command is not CWD-robust
```

## Proposed patch

Replace the placeholder command with a one-time locator that covers user and project installs,
including symlinks and nested project CWDs, then invoke the collector through `bash`:

```diff
diff --git a/.claude/skills/rebalance/SKILL.md b/.claude/skills/rebalance/SKILL.md
--- a/.claude/skills/rebalance/SKILL.md
+++ b/.claude/skills/rebalance/SKILL.md
@@
-```bash
-bash "<skill_dir>/collect.sh"
-```
-
-Where `<skill_dir>` is this SKILL.md's directory. Optional knobs (defaults are the standard):
+```bash
+REBALANCE_SKILL=""
+for root in "$HOME/.claude/skills" \
+            "$(git rev-parse --show-toplevel 2>/dev/null)/.claude/skills"; do
+  [ -d "$root" ] || continue
+  hit=$(find -L "$root" -path '*/rebalance/SKILL.md' 2>/dev/null | head -n1)
+  [ -n "$hit" ] && { REBALANCE_SKILL=$(dirname "$hit"); break; }
+done
+[ -n "$REBALANCE_SKILL" ] || {
+  echo "rebalance skill directory not found" >&2
+  exit 1
+}
+bash "$REBALANCE_SKILL/collect.sh"
+```
+
+Optional knobs (defaults are the standard):
```

## What I could not verify

- The harness tests the documented shell command under varied CWD/install conditions; it does not
  instrument Claude Code's internal skill resolver or prove what path metadata the runtime supplies.
- To keep this audit bounded and private, the collector scanned only the staged skill directory,
  not its default device-wide roots. This verifies script discovery, not the collector's inventory.
- Run B proves an already-resolved absolute skill directory survives the matrix. The locator shown
  in the proposed patch should receive its own focused matrix before application.
- The skill's Step 1 MCP call was not exercised; it is runtime behavior rather than script discovery.
