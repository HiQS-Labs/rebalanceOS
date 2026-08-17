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
while IFS= read -r hit; do
  [ -n "$hit" ] && report 1 "stale clone dir: $hit"
done < <(git grep -nE 'cd rebalance-OS|to/rebalance-OS' -- '*.md' \
           ':(exclude)CHANGELOG.md' ':(exclude)ROADMAP.md' ':(exclude)PROJECT/**' 2>/dev/null)

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
  drift=$(python3 - <<'PY' 2>/dev/null
import json, re, pathlib, sys

try:
    man = json.load(open("manifest.json"))
except Exception as exc:
    print(f"manifest.json does not parse: {exc}")
    sys.exit(0)

pyproject = pathlib.Path("pyproject.toml").read_text()
m = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
want = m.group(1) if m else None
if want and man.get("version") != want:
    print(f"version {man.get('version')} != pyproject {want}")

url = (man.get("repository") or {}).get("url", "")
if "HiQS-Suite/rebalanceOS" not in url:
    print(f"repository url is not HiQS-Suite/rebalanceOS: {url}")

pat = re.compile(r'@mcp\.tool\(\)\s*\n\s*(?:async\s+)?def\s+(\w+)\s*\(.*?\)\s*->.*?:', re.S)
code = set()
for f in pathlib.Path("src/rebalance/mcp/tools").glob("*.py"):
    code |= set(pat.findall(f.read_text()))
listed = {t.get("name") for t in man.get("tools", [])}
if code:
    for name in sorted(listed - code):
        print(f"manifest lists unregistered tool: {name}")
    for name in sorted(code - listed):
        print(f"registered tool missing from manifest: {name}")
PY
)
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
