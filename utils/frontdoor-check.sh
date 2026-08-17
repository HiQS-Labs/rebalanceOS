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
if "HiQS-Suite/rebalanceOS" not in url:
    print(f"repository url is not HiQS-Suite/rebalanceOS: {url}")


def is_mcp_tool(dec):
    """Match a @mcp.tool() / @mcp.tool decorator via the AST, not source formatting."""
    node = dec.func if isinstance(dec, ast.Call) else dec
    return isinstance(node, ast.Attribute) and node.attr == "tool"


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
grep -q 'rebalance version' README.md \
  || report 5 "README has no credential-free 'rebalance version' checkpoint"

# The checkpoint must come BEFORE the first credential step (Step 3 — Connect GitHub).
ck=$(grep -n 'rebalance version' README.md | head -1 | cut -d: -f1)
gh=$(grep -n '^### Step 3 — Connect GitHub' README.md | head -1 | cut -d: -f1)
if [ -n "$ck" ] && [ -n "$gh" ] && [ "$ck" -gt "$gh" ]; then
  report 5 "checkpoint (line $ck) comes after the first credential step (line $gh)"
fi

# --- 6. Getting Started reachable from the top -------------------------------
head -40 README.md | grep -q '#getting-started' \
  || report 6 "no Getting Started pointer in the first 40 lines of README"

# --- 7. first-run egress list completeness -----------------------------------
for host in 'github.com' 'pypi.org' 'files.pythonhosted.org'; do
  grep -q "$host" README.md || report 7 "egress list omits $host"
done

# --- kept-green regression guards --------------------------------------------
for f in LICENSE LICENSE-COMMERCIAL.md; do
  [ -f "$f" ] || report 0 "missing $f"
done

pyver=$(grep -m1 -E '^version = ' pyproject.toml | sed 's/.*"\(.*\)".*/\1/')
pkgver=$(grep -m1 -E '^__version__' src/rebalance/__init__.py | sed 's/.*"\(.*\)".*/\1/')
[ "$pyver" = "$pkgver" ] \
  || report 0 "pyproject version ($pyver) != package __version__ ($pkgver)"

exit "$fired"
