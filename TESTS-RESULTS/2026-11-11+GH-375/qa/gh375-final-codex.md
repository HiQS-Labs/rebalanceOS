# RELAY · gh375-final-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-11-11.
-->

NEXT: Reviewer
STATUS: Open
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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
