# Marathon Phase gh160
STATUS: Open
NEXT: codex (Builder)

<!-- marathon-drive: task=MARATHON-GH160-TURN builder=codex reviewer=agy round-cap=5 -->

## Phase Brief

---
gh_issue: 160
source: https://github.com/HiQS-Labs/rebalanceOS/issues/160
title: "GH-160 slice 1 — harden local_tz() and registry loading with property tests"
status: "Proposed (2-WORKING — marathon lane 2026-09-05). Tier-1 targets 3 and 4 from the issue; the config guard (#161) and md_parser (#165) are already done."
created: 2026-09-05
updated: 2026-09-05
owner: noel
doc_type: testing
rating: "pri/sev/appeal/effort 50/55/60/55 · calc 220"
effort: 2
complexity: 2
risk: 1
phases: 1
ratings_provisional: false
goal: >
  Two of the issue's enumerated Tier-1 parse-and-crash targets get Hypothesis-backed hardening:
  `local_tz()` must not raise on a malformed REBALANCE_TZ (verified: "/UTC" and "../.." currently
  crash), and registry loading must convert uncaught yaml.YAMLError / pydantic ValidationError into
  a diagnosable failure rather than a traceback.
non_goals:
  - Tier 2 (silent wrong answers) and the remaining Tier-1 targets (next_actions grammar) — later slices.
  - Porting the XYZ-forge ATE — the issue itself rejects that.
---

# GH-160 slice 1 — local_tz() and registry loading

## Status

| What was just completed | What's next |
|---|---|
| Capture for the 2026-09-05 marathon; Hypothesis is already in the dev extra (#165). | Builder lane. |

## Acceptance

From #160 §3, targets 3 and 4, verbatim:

3. **`src/rebalance/ingest/registry.py:73-79,94`** — uncaught `yaml.YAMLError` and uncaught pydantic `ValidationError` on the project registry.
4. **`src/rebalance/lib/time_ops.py:146-171` `local_tz()`** catches only `ZoneInfoNotFoundError`. **Verified by execution:** `REBALANCE_TZ="/UTC"` and `REBALANCE_TZ="../.."` crash.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/python -m pytest tests/test_time_ops_consolidation.py tests/test_collector_registry.py tests/test_time_ops_property.py tests/test_registry_property.py -q",
  "fix_probes": [
    { "type": "path_absent", "path": "tests/test_time_ops_property.py" },
    { "type": "path_absent", "path": "tests/test_registry_property.py" }
  ],
  "artifacts": [
    "src/rebalance/lib/time_ops.py",
    "src/rebalance/ingest/registry.py",
    "tests/test_time_ops_property.py",
    "tests/test_registry_property.py"
  ],
  "artifacts_new": [
    "tests/test_time_ops_property.py",
    "tests/test_registry_property.py"
  ],
  "remediation": {
    "source": "issue#160",
    "criteria": "local_tz() never raises on malformed REBALANCE_TZ (falls back with a warning); registry loading turns YAML/pydantic errors into a named, tested failure; both pinned by Hypothesis tests."
  },
  "lanes": { "agy_safe": ["src/rebalance/lib/time_ops.py", "src/rebalance/ingest/registry.py", "tests/test_time_ops_property.py", "tests/test_registry_property.py"], "orchestrator_only": [] }
}
```

*Contract auto-drafted by the 2026-09-05 marathon prep from the issue text — artifacts/lanes not yet operator-verified.*

## Phase 1

- [ ] Red controls first: `REBALANCE_TZ="/UTC"` and `"../.."` reproduce the crash on the current tree; a malformed registry YAML and a schema-violating project reproduce the tracebacks.
- [ ] `local_tz()`: catch the full failure surface (`ValueError`, `OSError`, `IsADirectoryError`, plus `ZoneInfoNotFoundError`), warn once, fall back to the existing default.
- [ ] Registry: wrap `yaml.safe_load` and the pydantic construction; raise one repo-defined error naming the file and the reason.
- [ ] Hypothesis: `st.text()` over `REBALANCE_TZ`; arbitrary YAML-ish text over the registry loader — neither may raise anything but the named error.

### QA checklist
- [ ] Every red control witnessed red before its fix.
- [ ] Existing time_ops and registry tests unchanged and green.
- [ ] No behaviour change for a VALID tz or registry.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
1. Implement the brief by creating/editing the artifact file(s): src/rebalance/lib/time_ops.py,src/rebalance/ingest/registry.py,tests/test_time_ops_property.py,tests/test_registry_property.py
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick claim MARATHON-GH160-TURN --agent codex --paths "marathon-system/gh160/RELAY.md,src/rebalance/lib/time_ops.py,src/rebalance/ingest/registry.py,tests/test_time_ops_property.py,tests/test_registry_property.py"
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick ping MARATHON-GH160-TURN --agent codex
   - /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH160-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/gh160/RELAY.md and src/rebalance/lib/time_ops.py,src/rebalance/ingest/registry.py,tests/test_time_ops_property.py,tests/test_registry_property.py. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: src/rebalance/lib/time_ops.py,src/rebalance/ingest/registry.py,tests/test_time_ops_property.py,tests/test_registry_property.py. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick release MARATHON-GH160-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick done MARATHON-GH160-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/Documents/GH Repos/rebalanceOS/.xyz/bin/tick
   Edit ONLY marathon-system/gh160/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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
