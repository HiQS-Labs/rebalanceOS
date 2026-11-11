# RELAY · gh375-final-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-11-11.
-->

NEXT: Producer
STATUS: Approved
ROUND: 1 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns. Plain blank separators may be added or removed between sections; preserve every substantive line, indentation, and fenced/literal blank line. A historical FAIL→PASS edit or changed fenced example is forbidden.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh375-final-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `src/rebalance/ingest/t3_code.py` (new) and the rest of the committed branch diff against base commit 70ccfc0 (run: git diff 70ccfc0 -- src tests), i.e. `src/rebalance/ingest/db/migrations/0010_agent_session_activity.sql` (new), `tests/test_t3_code.py` (new), and edits to `src/rebalance/ingest/index_ops.py`, `src/rebalance/ingest/db/queries.py` (`fetch_agent_activity`), `src/rebalance/ingest/config.py` (`get_t3_code_config`), `src/rebalance/lib/time_ops.py` (`utc_date_days_ago`), `src/rebalance/mcp/tools/projects.py`, `src/rebalance/doctor.py` (`_check_t3_code`), `tests/test_collector_contracts.py`, `tests/test_collector_registry.py`, docs (`ARCHITECTURE.md`, `MCP.md`, `AGENTS.md`, `CHANGELOG.md`, `manifest.json`, version 0.107.0).
- Approved plan and acceptance map: `PROJECT/2-WORKING/GH-375-T3-CODE-SESSION-STORE.md` (section "Phase 0 — Recon deltas and implementation plan"); plan QA thread `relay-system/2026-11-11/gh375-plan-codex.md` (Approved r2).
- Verification evidence: `TESTS-RESULTS/2026-11-11+GH-375/` — `SUMMARY.md`, `red-first.txt`, `mutation-witnesses.txt` (+ `scripts/`), `root-tests.txt`, `hiqs-tests.txt`, `doctor.txt`, `smoke.txt` (live dry-run vs direct count), `provenance.jsonl`. Seeded read-only T3 schema evidence: `.relay-artifacts/gh375-evidence.txt`.
- Recorded operator decisions: new table + opt-in reads; `github_activity` and frozen `hiqs_work_activity` byte-identical; no XYZ-forge board_sync wiring; the live flag-on smoke on the operator's Mac is NOT part of this task (dry run instead); no device config/job changes; never select message text or auth/secret/token/pairing/webhook tables.
- Operational envelope: local single-operator MCP server, a few Macs, local SQLite. rebalanceOS requires new red-first tests (SOP §3.6) — the new test file is expected, not a finding. Grade against commensurate complexity: no enterprise/multi-tenant threat model.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-11-11
- Definition of Done: every issue #375 Acceptance item is satisfied by code + evidence, or is the recorded operator deferral (flag-on smoke); the code matches the approved plan (no second writer, no parallel subsystem); checks substantiate the claims; ratings unchanged at 55/35/50/45 with no new evidence to move them.

### Reviewer questions (final QA)
1. For each Acceptance item in the plan's acceptance map, is it met? Cite the test and the code line that makes it true.
2. Does `t3_code.py` match the aggregation contract exactly (three grouped streams, merge per (repo, day, provider), PK-lookup provider fallback, `user_prompts`, `agent_threads`, midnight rule, window filter)? Any count-multiplication or off-by-one in the window (`utc_date_days_ago`)?
3. Write path: is delete+insert+ok-health one transaction with rollback; does a write failure leave health untouched; is `error` health only for extraction failures; is every health write skipped on dry run?
4. Privacy: does any executed SQL read text, auth/secret tables, or payload paths beyond `$.createdBy`/`$.branch`/`$.pullRequests`? Is only each PR object's `url` retained?
5. Registry/read side: is `t3_code` registered correctly; is the `_activity_repos` union strictly behind `watch_repos_from_agent_sessions`; does `fetch_agent_activity` honour the counting units (`thread_days` / `thread_provider_days`) documented in MCP.md and the docstring?
6. Doctor: are the states (disabled ± retained, enabled-no-row, missing, drift, error, stale, ok) correct, device-scoped, and DB-only?
7. Evidence: do the mutation witnesses, suites, doctor and smoke receipts substantiate the claims, and are the 14 root-suite failures credibly pre-existing (identical on base)? Is the dry-run smoke reported truthfully as a deferral substitute?
8. Anything over-engineered, duplicated, or wrong in docs/changelog/version? Any pre-existing defect in the touched functions?

Every `[Blocker]`/`[Should]` asking for a behaviour change carries `Observed input:`, `Affected scope:`, `Falsifier:`. Do not edit code. Set `STATUS: Approved` only if it passes.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns. Plain blank separators may be added or removed between sections; preserve every substantive line, indentation, and fenced/literal blank line. A historical FAIL→PASS edit or changed fenced example is forbidden.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1 · codex

Ship within the recorded scope.

swept file: yes

VERDICT: PASS
Basis: Read the complete new collector, migration and test module, the seeded schema evidence, the acceptance map, and the surrounding touched registry/read/config/time/MCP/doctor functions rather than only changed lines. No blocking or should-fix defect found, including in the pre-existing touched functions. This is source review plus assessment of retained receipts, not a new execution of the suites. Ratings remain 55/35/50/45; no evidence warrants changing them.

- [Pass] Acceptance: resolved fixture refresh and exact aggregation are supported by `tests/test_t3_code.py:259`, `:292`, `:303` and collector `src/rebalance/ingest/t3_code.py:181`. Runs and messages group separately; the message join uses the seeded run primary key. Thread sets merge per repo/day/provider; human prompts require role=user and createdBy=user; provider fallback uses COALESCE. Seeded evidence explicitly reports “messages with NULL run_id: 751” and “messages whose run_id has no run row: 0”. Midnight attribution is requested_at for runs, created_at for messages. The inclusive cutoff is intentional: approved plan says “window `day >= today_utc - window_days`”; `src/rebalance/lib/time_ops.py:152` implements that rule, so it is not an accidental one-day discrepancy.
- [Pass] Acceptance: schema drift, empty/missing store and disabled operation map to `tests/test_t3_code.py:345`, `:355`, `:361`, `:367`; implementation `src/rebalance/ingest/t3_code.py:139`, `:354`. Seeded metadata says “thread-projections|2”, matching the version-2 guard; required-column probes precede extraction. Missing/drift skip activity writes; empty extraction reaches ok health; disabled returns before opening T3.
- [Pass] Acceptance: repeatability and one-row delta (`tests/test_t3_code.py:377`), insert rollback (`:394`) and fresh/0009/idempotent migration (`:418`) match `src/rebalance/ingest/t3_code.py:291` and migration `0010_agent_session_activity.sql` (“PRIMARY KEY (source, device_id, repo_full_name, day, provider)”). Delete, inserts and ok health share BEGIN IMMEDIATE/commit, with rollback on failure. Destination write sits outside the extraction exception handler, so failed writes do not replace health with error. Dry-run guards cover missing/drift/error and return before the successful write; `tests/test_t3_code.py:280` checks retained emptiness.
- [Pass] Acceptance: frozen GitHub values are checked with nonempty activity plus a counter-change red control in `tests/test_t3_code.py:448`; the new writer names only the two agent-session tables (`src/rebalance/ingest/t3_code.py:260`, `:291`). Existing MCP GitHub functions remain separate in `src/rebalance/mcp/tools/projects.py:28`. No board-sync, job or device configuration wiring is introduced by these paths.
- [Pass] Acceptance/privacy: `tests/test_t3_code.py:503` captures executed SQL and has a text-path red control. Collector SQL reads only metadata and the createdBy/branch/pullRequests paths; `src/rebalance/ingest/t3_code.py:171` retains each PR object's string url only. No message text or auth/secret table is selected. The whole PR array is read transiently, as the documented contract allows; its other fields are not persisted.
- [Pass] Acceptance/read integration: `src/rebalance/ingest/db/queries.py:1453` sums explicitly named thread_days/thread_provider_days, canonicalizes repo aliases and bounds the result. `src/rebalance/mcp/tools/projects.py:55` clamps 1–90 and calls that reader; `tests/test_t3_code.py:316` pins actual FastMCP output including provider switching and URLs. Registry `src/rebalance/ingest/index_ops.py:2424` includes the flag-gated raw source in all/default refresh, covered by the updated collector tests. Its watched-repo union at `:965` is behind the separate watch flag, covered at `tests/test_t3_code.py:565`.
- [Pass] Acceptance/doctor: `src/rebalance/doctor.py:1504` handles disabled with/without retained health, enabled-no-row, missing, drift, error, stale and ok. `src/rebalance/ingest/t3_code.py:338` filters source and current device; doctor reads the destination DB only. `tests/test_t3_code.py:549` covers the eight states while making a T3 open fail.
- [Pass] Retained evidence: `mutation-witnesses.txt` records nine targeted red mutations and “24 passed” unmutated control. `root-tests.txt` lists the same 14 failed test IDs on candidate and base; that supports pre-existence of those failures, not a claim that the root suite is green or that their causes were diagnosed. `hiqs-tests.txt` records “163 passed, 1 skipped, 1 xfailed”. `doctor.txt` records exit 1 on both candidate and base with the same orphan-vector error, alongside the new disabled-source OK check. These are producer receipts assessed here, not reviewer reruns.
- [Pass] Live acceptance is the explicit operator deferral: `SUMMARY.md` says “The live smoke is a **dry run**” and leaves persisted flag-on refresh open; `smoke.txt` says “scratch DB created by dry runs: False” and reports equal repo sets/run/prompt totals/provider run splits. It does not independently establish live distinct-thread or thread-day totals, nor persistent live refresh. Those limits are compatible with the recorded scope; fixture assertions provide the exact bucket contract.
- [Pass] Documentation/version: `manifest.json:5` and `src/rebalance/__init__.py:31` both say 0.107.0; `CHANGELOG.md:13` carries the dated minor release. MCP documentation describes metadata exposure and counting units. No extra subsystem or replacement scheduler is needed.
- [Nit] `src/rebalance/ingest/t3_code.py:360` says dry_run “reads and writes nothing”, although it deliberately reads T3 and computes aggregates. Optional wording correction: “reads the source and writes nothing.” The implementation and public campaign accurately describe dry-run behavior.
- [Nit] `SUMMARY.md` describes the doctor base as 70ccfc0 through its “identical on base” table wording, while `doctor.txt` explicitly labels its comparison f081931. Optional correction: identify f081931 in that row. Root-suite comparison is separately and consistently labeled 70ccfc0.

Review limitations: no git commands, executable fixtures, pytest, validate.sh or shell test suites were run. Checks requiring a fresh execution remain [Unverified — needs clone run] for this reviewer; the harness gate follows this turn. No new behavioral probe was needed, so there is no scratch probe output to retain.

Relay closed (Approved), no further turn needed.


### Attestation · relay-drive — 2026-11-11T21:09:58Z
task: RELAY-gh375-final-codex
reviewer: codex
status: Approved
reviewed-head: a0eb5229c56167831dc2d04a1fe60292b79629b5
added-range: 9497+6600
added-sha256: 0a472efdae0611bd9a535327777262524268a9115034095805dc618e7a16549e
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
