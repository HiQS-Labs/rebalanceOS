#!/bin/bash
# GH-44 front-door health board. See FRONTDOOR.md for what each check means.
#
# Contract: print NOTHING when healthy. Any output is a regression, and names which
# finding regressed. Exit 0 clean, 1 if any check fired.
#
# This is a documentation/metadata board, not a test suite — it greps tracked files
# and never mutates anything.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd -P)
cd "$ROOT" || exit 1

fired=0
report() { echo "FRONTDOOR[$1] $2"; fired=1; }

# --- 1. stale clone directory -------------------------------------------------
# The clone is `rebalanceOS`; `cd rebalance-OS` / `to/rebalance-OS` are the retired form.
# The sqlite filename ask_self/index/rebalance-OS.sqlite is a real artifact name, not a
# clone dir, so it is deliberately not matched.
#
# CHANGELOG.md, ROADMAP.md and PROJECT/** are excluded on purpose: they are append-only
# historical ledgers. An entry that said `cd rebalance-OS` in 2025 was CORRECT then, and
# rewriting it would falsify the record to satisfy a linter. Only live instructions —
# things a reader today would copy and run — are in scope.
#
# FRONTDOOR.md is excluded because it documents this very pattern in order to explain
# the check; a linter does not lint its own ruleset.
while IFS= read -r hit; do
  [ -n "$hit" ] && report 1 "stale clone dir: $hit"
done < <(git grep -nE 'cd rebalance-OS|to/rebalance-OS' -- '*.md' \
           ':(exclude)CHANGELOG.md' ':(exclude)ROADMAP.md' ':(exclude)PROJECT/**' \
           ':(exclude)FRONTDOOR.md' 2>/dev/null)

# --- 2. Code Intelligence over-promise ---------------------------------------
# The ask_self index is gitignored and the harness embeds via Gemini, so a fresh clone
# cannot query with "no setup" or "no API keys".
while IFS= read -r hit; do
  [ -n "$hit" ] && report 2 "ask_self over-promise: $hit"
done < <(git grep -nE 'index is committed|no ingest and no API keys|no setup required' -- README.md 2>/dev/null)

if git ls-files --error-unmatch ask_self/index/rebalance-OS.sqlite >/dev/null 2>&1; then
  report 2 "ask_self/index/rebalance-OS.sqlite is tracked — README wording assumes it is not"
fi

# --- 3. manifest.json drift ---------------------------------------------------
if [ -f manifest.json ]; then
  # NOTE: stderr is deliberately NOT suppressed and the exit status is checked.
  # An earlier version swallowed both, so a crashed extractor produced empty output
  # and read as a PASS — a check whose whole job is catching drift silently
  # certifying that there is none. Extraction problems are now reported failures.
  drift=$(python3 - <<'PY'
import ast, json, pathlib, re, sys

fail = []

try:
    man = json.load(open("manifest.json"))
except Exception as exc:
    print(f"manifest.json does not parse: {exc}")
    sys.exit(0)

try:
    pyproject = pathlib.Path("pyproject.toml").read_text()
except OSError as exc:
    print(f"cannot read pyproject.toml: {exc}")
    sys.exit(0)

m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
if not m:
    print("cannot find version in pyproject.toml — check cannot verify manifest version")
elif man.get("version") != m.group(1):
    print(f"version {man.get('version')} != pyproject {m.group(1)}")

url = (man.get("repository") or {}).get("url", "")
if "HiQS-Labs/rebalanceOS" not in url:
    print(f"repository url is not HiQS-Labs/rebalanceOS: {url}")


def is_mcp_tool(dec):
    """Match `@mcp.tool()` / `@mcp.tool` via the AST, not source formatting.

    The receiver is checked too: matching any `.tool` attribute would count an
    unrelated object's decorator as an MCP registration and invent tool-surface
    drift. If the server ever renames the receiver, extraction drops to zero and
    the empty-extraction guard below reports it — it cannot silently pass.
    """
    node = dec.func if isinstance(dec, ast.Call) else dec
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "tool"
        and isinstance(node.value, ast.Name)
        and node.value.id == "mcp"
    )


tools_dir = pathlib.Path("src/rebalance/mcp/tools")
if not tools_dir.is_dir():
    print(f"tool source dir missing: {tools_dir} — cannot verify the tool surface")
    sys.exit(0)

code, scanned = set(), 0
for f in sorted(tools_dir.glob("*.py")):
    try:
        tree = ast.parse(f.read_text())
    except SyntaxError as exc:
        print(f"cannot parse {f}: {exc} — tool surface not verifiable")
        continue
    scanned += 1
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(is_mcp_tool(d) for d in node.decorator_list):
                code.add(node.name)

# An empty extraction is a BROKEN CHECK, never a pass.
if scanned == 0:
    print(f"no python files scanned under {tools_dir} — tool surface not verifiable")
elif not code:
    print(f"extracted 0 @mcp.tool() registrations from {scanned} file(s) — "
          "extractor is broken or the registration idiom changed")
else:
    listed = {t.get("name") for t in man.get("tools", [])}
    for name in sorted(listed - code):
        print(f"manifest lists unregistered tool: {name}")
    for name in sorted(code - listed):
        print(f"registered tool missing from manifest: {name}")
PY
)
  rc=$?
  if [ "$rc" -ne 0 ]; then
    report 3 "manifest tool-surface check failed to run (python3 exit $rc) — not a pass"
  fi
  while IFS= read -r line; do
    [ -n "$line" ] && report 3 "$line"
  done <<< "$drift"
fi

# --- 4. ARCHITECTURE.md bad references ---------------------------------------
while IFS= read -r hit; do
  [ -n "$hit" ] && report 4 "link to nonexistent root PROJECT.md: $hit"
done < <(git grep -nE '\]\(\./PROJECT\.md\)' -- ARCHITECTURE.md 2>/dev/null)

while IFS= read -r hit; do
  [ -n "$hit" ] && report 4 "wrong license (repo is AGPL-3.0-only): $hit"
done < <(git grep -nE 'Apache License|APACHE-LICENSE' -- ARCHITECTURE.md 2>/dev/null)

# --- 5. credential-free checkpoint -------------------------------------------
# Scoped to the Step 1 SECTION, not the whole file. A file-wide grep passes on the
# top-of-page quick-start alone, so deleting the Step 1 checkpoint would go unnoticed —
# the check must assert the thing it claims to protect, in the place it belongs.
step1=$(awk '/^### Step 1 — Clone and install/{f=1;next} f&&/^### /{exit} f' README.md)
if [ -z "$step1" ]; then
  report 5 "cannot locate the 'Step 1 — Clone and install' section — check not verifiable"
elif ! printf '%s' "$step1" | grep -q 'rebalance version'; then
  report 5 "Step 1 has no credential-free 'rebalance version' checkpoint"
fi

# It must also land before the first credential step (Step 3 — Connect GitHub).
s1=$(grep -n '^### Step 1 — Clone and install' README.md | head -1 | cut -d: -f1)
gh=$(grep -n '^### Step 3 — Connect GitHub' README.md | head -1 | cut -d: -f1)
if [ -n "$s1" ] && [ -n "$gh" ] && [ "$s1" -gt "$gh" ]; then
  report 5 "Step 1 (line $s1) comes after the first credential step (line $gh)"
fi

# --- 6. Getting Started reachable from the top -------------------------------
head -40 README.md | grep -q '#getting-started' \
  || report 6 "no Getting Started pointer in the first 40 lines of README"

# --- 7. first-run egress list completeness -----------------------------------
# Bounded to the egress list itself. A file-wide grep would be satisfied by the clone
# URL for github.com, masking a removed list entry.
egress=$(awk '/^\*\*First-run network egress\*\*/{f=1;next} f&&/^### /{exit} f' README.md)
if [ -z "$egress" ]; then
  report 7 "cannot locate the 'First-run network egress' section — check not verifiable"
else
  for host in 'github.com' 'pypi.org' 'files.pythonhosted.org'; do
    printf '%s' "$egress" | grep -q "$host" \
      || report 7 "first-run egress list omits $host"
  done
fi

# --- kept-green regression guards --------------------------------------------
# FRONTDOOR.md promises these stay true, so each one is asserted here. A promise in
# the doc with no check behind it is the same silent-pass problem as an unguarded
# drift check — the board would read green while the contract quietly broke.

# README is the canonical root entry point and points at the tracked /welcome skill.
if [ ! -f README.md ]; then
  report 0 "README.md missing — the canonical root entry point is gone"
else
  grep -q '/welcome' README.md \
    || report 0 "README.md no longer points at the /welcome skill"
  git ls-files --error-unmatch .claude/skills/welcome/SKILL.md >/dev/null 2>&1 \
    || report 0 "README points at /welcome but .claude/skills/welcome/SKILL.md is not tracked"
fi

# Both licenses present AND still the licenses they claim to be. Presence alone would
# let either file be replaced with unrelated content and still produce an empty board.
if [ ! -f LICENSE ]; then
  report 0 "missing LICENSE"
elif ! grep -q 'GNU AFFERO GENERAL PUBLIC LICENSE' LICENSE; then
  report 0 "LICENSE is no longer the AGPL — README and ARCHITECTURE both declare AGPL-3.0-only"
fi

if [ ! -f LICENSE-COMMERCIAL.md ]; then
  report 0 "missing LICENSE-COMMERCIAL.md"
elif ! grep -q 'AGPL-3.0-only' LICENSE-COMMERCIAL.md; then
  report 0 "LICENSE-COMMERCIAL.md no longer references the AGPL-3.0-only default — dual-license story is inconsistent"
fi

# Human gates are named in the step that needs them. FRONTDOOR.md claims the board
# asserts this, so it must actually do so. Each check is bounded to one step section:
# a gate mentioned only in a distant section would still ambush the reader here.
check_gate() {  # check_gate <step heading regex> <token regex> <label>
  body=$(awk -v h="$1" '$0 ~ h {f=1;next} f&&/^### /{exit} f' README.md)
  if [ -z "$body" ]; then
    report 0 "cannot locate section '$3' — human-gate ordering not verifiable"
  elif ! printf '%s' "$body" | grep -qEi "$2"; then
    report 0 "$3 does not name its prerequisite before the commands that need it"
  fi
}
check_gate '^### Step 2 — Ingest your vault'              'vault'            'Step 2 (vault path)'
check_gate '^### Step 3 — Connect GitHub'                 'PAT|token'        'Step 3 (GitHub PAT)'
check_gate '^### Step 4 — Connect Google Calendar'        'OAuth|credential' 'Step 4 (Google OAuth)'
check_gate '^### Step 5 — Connect Gmail'                  'OAuth|credential' 'Step 5 (Gmail OAuth)'

# The Apple-Silicon hardware gate must be stated before the install that depends on it.
plat=$(grep -n '^### Supported platform & first-run network' README.md | head -1 | cut -d: -f1)
s1=$(grep -n '^### Step 1 — Clone and install' README.md | head -1 | cut -d: -f1)
if [ -z "$plat" ] || [ -z "$s1" ]; then
  report 0 "cannot locate platform section or Step 1 — hardware-gate ordering not verifiable"
elif [ "$plat" -gt "$s1" ]; then
  report 0 "the Apple-Silicon platform gate (line $plat) is stated after Step 1 (line $s1)"
fi

pyver=$(grep -m1 -E '^version = ' pyproject.toml | sed 's/.*"\(.*\)".*/\1/')
pkgver=$(grep -m1 -E '^__version__' src/rebalance/__init__.py | sed 's/.*"\(.*\)".*/\1/')
if [ -z "$pyver" ] || [ -z "$pkgver" ]; then
  report 0 "could not read pyproject version ('$pyver') or package __version__ ('$pkgver') — check not verifiable"
elif [ "$pyver" != "$pkgver" ]; then
  report 0 "pyproject version ($pyver) != package __version__ ($pkgver)"
fi

# --- 8. retired org/owner names in live files ---------------------------------
# GH-123-class bug: a hardcoded old org name in a REST API call doesn't get GitHub's
# free redirect (that only covers git fetch/push and browser links) — it silently
# rots until something actually calls the API and hard-crashes. Caught HiQS-Suite
# surviving in health_issue_reporter.py for days, invisibly, because the thing that
# would have reported the crash WAS the crashing script.
#
# RETIRED_OWNERS is a list so the NEXT rename is one line here, not a fresh grep
# invented from scratch. Scoped to files a live process actually reads/executes —
# the same historical-ledger exclusions as check 1 (CHANGELOG.md/ROADMAP.md/PROJECT/**
# and relay/marathon transcripts legitimately cite old org names in old, dated
# entries; rewriting them would falsify history, not fix a bug).
RETIRED_OWNERS=(HiQS-Suite)
for owner in "${RETIRED_OWNERS[@]}"; do
  while IFS= read -r hit; do
    [ -n "$hit" ] && report 8 "retired org '$owner' still referenced: $hit"
  done < <(git grep -nF "$owner" -- '*.py' '*.sh' '*.js' '*.json' '*.yml' '*.yaml' \
             ':(exclude)CHANGELOG.md' ':(exclude)ROADMAP.md' ':(exclude)PROJECT/**' \
             ':(exclude)relay-system/**' ':(exclude)marathon-system/**' \
             ':(exclude)test/**' ':(exclude)tests/**' \
             ':(exclude)utils/frontdoor-check.sh' 2>/dev/null)
done

exit "$fired"
