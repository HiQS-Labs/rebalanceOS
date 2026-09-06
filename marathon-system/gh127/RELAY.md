# Marathon Phase gh127
STATUS: Open
NEXT: agy (Reviewer)

<!-- marathon-drive: task=MARATHON-GH127-TURN builder=codex reviewer=agy round-cap=5 -->

## Phase Brief

---
gh_issue: 127
source: https://github.com/HiQS-Labs/rebalanceOS/issues/127
title: "GH-127 — the documented README install must produce a clone whose test suite collects"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). The earlier quick win fixed the test-suite NOTE; the Getting Started path itself still installs .[embeddings,calendar] and cannot collect."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: bugfix
rating: "pri/sev/appeal/effort 75/70/75/85 · calc 305"
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
goal: >
  Make README Getting Started, followed verbatim on a fresh clone, yield `pytest --collect-only`
  with 0 errors; state the expected collected count; add a CI job that exercises the documented
  path on a clean checkout so it cannot regress.
non_goals:
  - Redesigning extras. The `dev` extra exists (#165); `server` exists. This lane only makes the documented path use them.
---

# GH-127 — README install must collect

## Status

| What was just completed | What's next |
|---|---|
| The "To run the test suite" note was fixed earlier (`.[dev,server]`). Getting Started at README.md:28 still says `.[embeddings,calendar]`, which cannot collect (13 `fastapi` import errors). | Builder lane: fix the Getting Started line, state the expected count, add the clean-checkout CI job. |

## Acceptance

Verbatim from #127:

- [ ] Following README Getting Started verbatim on a fresh clone yields `--collect-only` with 0 errors.
- [ ] The expected collected-test count is stated somewhere a caller can check against.
- [ ] A CI job exercises the documented path on a clean checkout, so this cannot regress unnoticed.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest --collect-only -q tests/ | tail -1 | grep -q ' collected' && ! .venv/bin/python -m pytest --collect-only -q tests/ 2>&1 | grep -q 'errors during collection'",
  "fix_probes": [
    { "type": "grep_present", "path": "README.md", "pattern": "pip install -e \\\".\\[embeddings,calendar\\]\\\"" }
  ],
  "artifacts": [
    "README.md",
    ".github/workflows/ci.yml"
  ],
  "remediation": {
    "source": "issue#127",
    "criteria": "README Getting Started installs extras that collect; expected count stated; a clean-checkout CI job runs the documented path."
  },
  "lanes": { "agy_safe": ["README.md", ".github/workflows/ci.yml"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified.*

## Phase 1

- [ ] README.md:28 → an extras set that collects (`.[embeddings,calendar,server,dev]` or the `dev` extra pulling `server` — pick one and say why in the PR).
- [ ] State the expected collected count where the test note lives, with the command that prints it.
- [ ] New CI job: fresh checkout, follow the README lines verbatim, `--collect-only` must report 0 errors.

### QA checklist — Phase 1
- [ ] Witnessed red: the new CI job fails on the current README (before the fix) — prove it in the PR.
- [ ] No other CI job's behaviour changes.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): README.md,.github/workflows/ci.yml
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick claim MARATHON-GH127-TURN --agent codex --paths "marathon-system/gh127/RELAY.md,README.md,.github/workflows/ci.yml"
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick ping MARATHON-GH127-TURN --agent codex
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH127-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/gh127/RELAY.md and README.md,.github/workflows/ci.yml. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: README.md,.github/workflows/ci.yml. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH127-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick done MARATHON-GH127-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   Edit ONLY marathon-system/gh127/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
4b. TO VERIFY A FINDING, WRITE PROBE FILES OUTSIDE THE REPO — under $TMPDIR, never inside the
   working tree. Creating even one scratch file in the repo is an off-lane write: containment
   reverts it and FAILS YOUR WHOLE TURN, discarding the review you just did (GH-441). Observed
   2026-08-08: a reviewer found a real latent crash, wrote two probe files in-tree to demonstrate
   it, and lost the turn for doing so — the finding survived only because RELAY.md happens to be
   on your allowlist. `cp` what you need to "$TMPDIR/probe.$$/" and work there instead. Verifying
   is wanted; verifying in-tree is what costs you the turn.
5. HAND OFF EXPLICITLY (GH-268): end your turn by naming who acts next — "handing off to codex —
   codex, take your turn" when requesting changes, or "relay closed, no further turn needed" when
   approving. The beta report singled this out: the Reviewer turn did not tell the user to go back to the
   Producer, so the relay looked stalled when it was simply waiting. Do this EVERY round.

### Round 1 · Builder · codex

- Updated both README Getting Started install commands to use `embeddings`, `calendar`, `server`, and
  `dev`; the platform fallback now drops only `embeddings`. `dev` supplies pytest and `server` supplies
  FastAPI, which collection imports.
- Replaced the stale test-install addendum with the collection command and current Python 3.12 baseline:
  `2146 tests collected` with 0 errors (from the published GH-144 campaign).
- Added the isolated `readme-install` macOS 14 CI job, which runs the README commands verbatim on a
  fresh checkout before collecting `tests/`. It does not alter the existing split test lanes.
- Verification: the sandbox blocks PyPI DNS, so a fresh local install could not complete; reviewer should
  validate the clean-check job in CI. Local YAML/content checks follow before handoff.
