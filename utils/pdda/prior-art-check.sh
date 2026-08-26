#!/usr/bin/env bash
# Prior-art gate — runs the checks ROUTER.md describes, instead of asking nicely.
#
# Why this exists: GH-5 shipped two duplicates of things already in the tree or
# in flight. The first response was a prose block at the top of ROUTER.md. A
# review pointed out the obvious — that is another exhortation, and the repo
# already had a mandated PDDA Phase 0 prior-art step that did not fire either.
# Prose an agent must voluntarily obey is not a safeguard. This script is.
#
# Usage:
#   utils/pdda/prior-art-check.sh <concept> [<concept>...]
#
# Exit 0 = no prior art found, you are clear to build.
# Exit 3 = prior art found. READ IT before writing anything. Not a failure —
#          a finding. PDDA Phase 0 requires you to state why extending the
#          existing thing does not work before replacing it.

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
NEW_REPO="HiQS-Labs/rebalanceOS"
# The retiring repo. Work stranded in ITS pr queue is invisible to any in-tree
# search — that is exactly how an entire lib/*_ops campaign got restarted.
OLD_REPO="Hypercart-Dev-Tools/rebalance-OS"

if [ "$#" -eq 0 ]; then
  echo "usage: $0 <concept> [<concept>...]" >&2
  echo "  e.g. $0 chunking split_oversized" >&2
  exit 2
fi

found=0

echo "== prior-art check: $* =="
echo

# 1. Work in flight — invisible to grep, on BOTH repos.
for repo in "$NEW_REPO" "$OLD_REPO"; do
  echo "-- open PRs on $repo --"
  if ! out="$(gh pr list -R "$repo" --state open --limit 50 \
                --json number,title,headRefName 2>/dev/null)"; then
    # LOUD: a check that could not run must say so, never read as "nothing found".
    echo "  !! could not query $repo (gh unavailable/unauthed) — THIS CHECK DID NOT RUN"
    found=1
    continue
  fi
  for term in "$@"; do
    if hits="$(printf '%s' "$out" | grep -i -- "$term" 2>/dev/null)" && [ -n "$hits" ]; then
      echo "  PRIOR ART: '$term' appears in an open PR:"
      printf '%s\n' "$hits" | sed 's/^/    /'
      found=1
    fi
  done
done
echo

# 2. Campaigns already under way.
echo "-- ROADMAP.md In progress --"
if [ -f "$REPO_ROOT/ROADMAP.md" ]; then
  section="$(awk '/^### In progress/{f=1;next} /^###/{f=0} f' "$REPO_ROOT/ROADMAP.md")"
  for term in "$@"; do
    if hits="$(printf '%s' "$section" | grep -i -- "$term" 2>/dev/null)" && [ -n "$hits" ]; then
      echo "  PRIOR ART: '$term' is already an in-progress campaign:"
      printf '%s\n' "$hits" | cut -c1-160 | sed 's/^/    /'
      found=1
    fi
  done
fi
echo

# 3. Cross-package source search. The standalone packages are the ones people
#    forget to look in, so they are named explicitly rather than left to a
#    top-level glob.
echo "-- source across src/ utils/ HiQS/ scripts/ --"
for term in "$@"; do
  hits="$(cd "$REPO_ROOT" && grep -rIl --include='*.py' --include='*.sh' -- "$term" \
            src utils HiQS scripts 2>/dev/null | grep -v '/\.' | head -20)"
  if [ -n "$hits" ]; then
    echo "  PRIOR ART: '$term' already appears in:"
    printf '%s\n' "$hits" | sed 's/^/    /'
    found=1
  fi
done
echo

if [ "$found" -ne 0 ]; then
  cat <<'MSG'
== PRIOR ART FOUND ==
Read it before building. If it is inadequate, PDDA Phase 0 requires you to state
WHY EXTENDING IT DOES NOT WORK. "I did not know it was there" is the failure this
gate exists to stop, and it is not a reason.
MSG
  exit 3
fi

echo "== no prior art found — clear to build =="
exit 0
