# Marathon Phase gh174
STATUS: Open
NEXT: agy (Reviewer)

<!-- marathon-drive: task=MARATHON-GH174-TURN builder=codex reviewer=agy round-cap=5 -->

## Phase Brief

---
gh_issue: 174
source: https://github.com/HiQS-Labs/rebalanceOS/issues/174
title: "GH-174 — directory-independence: implement option 1, the seconds-long rootdir assertion"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). Option 1 of the three costed in the issue."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: hygiene
rating: "pri/sev/appeal/effort 55/45/65/90 · calc 255"
effort: 1
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
goal: >
  One test that runs `pytest --collect-only -q` from a foreign directory (outside the repo, and
  from a directory containing a stray conftest.py) and asserts the header reports the repo as
  rootdir and pyproject.toml as configfile. Seconds, not a doubled CI job.
non_goals:
  - Options 2 and 3 (subset differential; nightly full differential). If option 1 proves enough, the issue closes on that measurement.
---

# GH-174 — the cheap rootdir assertion

## Status

| What was just completed | What's next |
|---|---|
| Capture for the 2026-09-05 marathon; option 1 chosen per the issue's own cost ordering. | Builder lane: the test, plus the measured wall-clock cost stated in the PR. |

## Acceptance

Verbatim from #174:

Whatever lands should state, in the PR, which of the three options above it implements and what it costs in CI wall-clock — measured, not estimated. If the answer is "option 1 is enough", closing this issue with that measurement recorded is a valid outcome.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_pytest_rootdir_pinned.py -q",
  "fix_probes": [
    { "type": "path_absent", "path": "tests/test_pytest_rootdir_pinned.py" }
  ],
  "artifacts": [
    "tests/test_pytest_rootdir_pinned.py"
  ],
  "artifacts_new": [
    "tests/test_pytest_rootdir_pinned.py"
  ],
  "remediation": {
    "source": "issue#174",
    "criteria": "A single fast test asserts rootdir/configfile resolve to the repo from a foreign cwd and from a dir with a stray conftest.py; its wall-clock cost is measured and stated."
  },
  "lanes": { "agy_safe": ["tests/test_pytest_rootdir_pinned.py"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified.*

## Phase 1

- [ ] `tests/test_pytest_rootdir_pinned.py`: subprocess `pytest --collect-only -q <repo>/tests` with `cwd=` (a) a temp dir outside the repo, (b) a temp dir containing a stray `conftest.py` that would break collection if honoured; parse `rootdir:` and `configfile:` from the header.
- [ ] Measure the test's own wall-clock and state it in the PR body.

### QA checklist — Phase 1
- [ ] Witnessed red: temporarily point the subprocess at a copy of the repo with `[tool.pytest.ini_options]` removed and confirm the assertion fails.
- [ ] Test is hermetic — no dependency on the operator's machine paths.

### Round 1 · Builder · codex

Created `tests/test_pytest_rootdir_pinned.py`. Its two parameterized subprocess probes collect the
absolute repository test directory from an outside working directory, including one that contains a
failing stray `conftest.py`; both require the collection header to report this repository as `rootdir`
and `pyproject.toml` as `configfile`. The test derives the repository path from its own location and
uses the current Python interpreter, so it has no operator-specific path or launcher dependency.
`-v` accompanies the required `-q` because quiet mode alone suppresses the session header that this
assertion must inspect. Verification: `python3 -m pytest tests/test_pytest_rootdir_pinned.py -q` —
2 passed in 5.45s (5.72s measured wall-clock, including pytest startup).


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): tests/test_pytest_rootdir_pinned.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick claim MARATHON-GH174-TURN --agent codex --paths "marathon-system/gh174/RELAY.md,tests/test_pytest_rootdir_pinned.py"
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick ping MARATHON-GH174-TURN --agent codex
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH174-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/gh174/RELAY.md and tests/test_pytest_rootdir_pinned.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: tests/test_pytest_rootdir_pinned.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH174-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick done MARATHON-GH174-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   Edit ONLY marathon-system/gh174/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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
