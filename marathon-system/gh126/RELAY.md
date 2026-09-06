# Marathon Phase gh126
STATUS: Open
NEXT: codex (Builder)

<!-- marathon-drive: task=MARATHON-GH126-TURN builder=codex reviewer=agy round-cap=5 -->

## Phase Brief

---
gh_issue: 126
source: https://github.com/HiQS-Labs/rebalanceOS/issues/126
title: "GH-126 — turn the datetime/subprocess banned-import warnings into an exact-baseline ratchet"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). Phases 2–3 of the issue; the exact-baseline design already exists for sqlite (#136) and is reused, not duplicated."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: hygiene
rating: "pri/sev/appeal/effort 60/55/65/45 · calc 225"
effort: 3
complexity: 2
risk: 2
phases: 1
ratings_provisional: false
goal: >
  The 33 datetime/subprocess findings under src/rebalance/ingest/ that pdda reports as WARN become an
  exact, line-independent JSON baseline in the existing checker; additions and stale shrinks both
  fail in CI and in pdda.sh; a reasoned pragma exempts a reviewed import.
non_goals:
  - Phase 1 (PR template + ROUTER.md Reuse Proof wording) — docs/governance, separate lane.
  - Adding `json` to the ban (explicitly excluded by the issue).
  - A second validator. Extend utils/pdda/check_banned_imports.py; do not add a file beside it.
---

# GH-126 — banned-imports exact-baseline ratchet

## Status

| What was just completed | What's next |
|---|---|
| Capture for the 2026-09-05 marathon, scoped to Phases 2–3. `check_banned_imports.py` already implements the exact-baseline pattern for `sqlite3.connect` (`sqlite_connect_baseline.json`); this lane applies the same mechanism to the datetime/subprocess family. | Builder lane. |

## Acceptance

Verbatim from #126. This lane delivers criteria 2–5 and must not break 6–7; criterion 1 is
Phase 1 (docs/governance) and is left for a separate lane — see `non_goals`.

- [ ] `ROUTER.md` is the only source of prior-art check wording; the PR template links to it and captures a Reuse Proof.
- [ ] No new validator duplicates `check_banned_imports.py` or `tests/test_collector_contracts.py`.
- [ ] The current debt is represented by an exact, line-independent baseline.
- [ ] New debt and stale/reduced baselines both fail locally and in CI.
- [ ] Fixture, current-tree, and mutation tests constrain the ratchet.
- [ ] `pytest tests/` and `pytest HiQS/tests` pass; `rebalance doctor` passes.
- [ ] Existing 3-Eyes CI exclusions remain untouched.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_sqlite_gateway_ratchet.py tests/test_banned_imports_ratchet.py -q && .venv/bin/python utils/pdda/check_banned_imports.py --check",
  "fix_probes": [
    { "type": "path_absent", "path": "utils/pdda/banned_imports_baseline.json" },
    { "type": "path_absent", "path": "tests/test_banned_imports_ratchet.py" }
  ],
  "artifacts": [
    "utils/pdda/check_banned_imports.py",
    "utils/pdda/banned_imports_baseline.json",
    "tests/test_banned_imports_ratchet.py",
    "utils/pdda/pdda.sh"
  ],
  "artifacts_new": [
    "utils/pdda/banned_imports_baseline.json",
    "tests/test_banned_imports_ratchet.py"
  ],
  "remediation": {
    "source": "issue#126",
    "criteria": "datetime/subprocess findings pinned to an exact line-independent baseline in the existing checker; additions and shrinks fail in CI and pdda.sh; reasoned pragma exempts; parse failures fail closed."
  },
  "lanes": { "agy_safe": ["utils/pdda/check_banned_imports.py", "utils/pdda/banned_imports_baseline.json", "tests/test_banned_imports_ratchet.py", "utils/pdda/pdda.sh"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified. CI wiring (`.github/workflows/ci.yml`) is deliberately NOT in this lane's artifacts to avoid colliding with GH-127; the existing `--check` call at ci.yml:41 already runs the checker, so a new family in the checker is picked up without a workflow edit.*

## Phase 2–3

- [ ] Finding identity = relative path + import family + occurrence count; line numbers diagnostic only.
- [ ] `utils/pdda/banned_imports_baseline.json` committed, exact, matching the current tree.
- [ ] `--check` fails on additions AND on decreases/renames; `--update-baseline` is local and explicit.
- [ ] `# CANONICAL-PATH-OK: <reason>` same-line pragma exempts; blank reason fails.
- [ ] AST parse/read failure fails closed.
- [ ] `pdda.sh banned-imports` uses the same code path.

### QA checklist
- [ ] Mutation control: add one forbidden import to a fixture → `--check` red; remove one → red until baseline updated; move a line → stable; empty pragma → red.
- [ ] Current tree matches the committed baseline exactly.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): utils/pdda/check_banned_imports.py,utils/pdda/banned_imports_baseline.json,tests/test_banned_imports_ratchet.py,utils/pdda/pdda.sh
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick claim MARATHON-GH126-TURN --agent codex --paths "marathon-system/gh126/RELAY.md,utils/pdda/check_banned_imports.py,utils/pdda/banned_imports_baseline.json,tests/test_banned_imports_ratchet.py,utils/pdda/pdda.sh"
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick ping MARATHON-GH126-TURN --agent codex
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH126-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/gh126/RELAY.md and utils/pdda/check_banned_imports.py,utils/pdda/banned_imports_baseline.json,tests/test_banned_imports_ratchet.py,utils/pdda/pdda.sh. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: utils/pdda/check_banned_imports.py,utils/pdda/banned_imports_baseline.json,tests/test_banned_imports_ratchet.py,utils/pdda/pdda.sh. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH126-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick done MARATHON-GH126-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   Edit ONLY marathon-system/gh126/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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
