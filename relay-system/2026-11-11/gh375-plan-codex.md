# RELAY · gh375-plan-codex
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
6. **Commit only the relay file** (`relay(gh375-plan-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/1-INBOX/GH-375-T3-CODE-SESSION-STORE.md` — **plan only; no production code written yet.** The issue body (sections Observed … Preflight Contract) is transcribed into the doc; the start-task section **"Phase 0 — Recon deltas and implementation plan"** at the end is the executable plan and acceptance map.
- Evidence (read-only, seeded): `.relay-artifacts/gh375-evidence.txt` — T3 schema excerpts from the separate `t3code-fork` repo (not in this worktree) and count-only probes of the live T3 store. No message text was read.
- Source paths for grounding (this repo): `src/rebalance/ingest/index_ops.py` (Collector/register_collector :35-125, `_activity_repos` :932-966, `get_watched_repos` :1030-1085, `refresh_index` :1697-1845, `_dry_run_adapter` :1997, `_refresh_clio` :2081-2113, registrations :2350-2430), `src/rebalance/ingest/db/migrate.py` :63-98, `src/rebalance/ingest/db/migrations/0009_watched_repos_snapshot.sql` + `README.md`, `src/rebalance/ingest/db/connection.py` (`db_connection_readonly` :90-104), `src/rebalance/ingest/config.py` (`get_claude_cloud_config` :1370-1383), `src/rebalance/ingest/db/queries.py`, `src/rebalance/mcp/tools/projects.py`, `src/rebalance/doctor.py` (`_check_apple_reminders` :1475-1502, wiring :2638-2660), `src/rebalance/ingest/apple_reminders.py` (`apple_reminders_health` :780-812), `src/rebalance/lib/git_ops.py` (`parse_github_remote_url` :310, `run_git` :387), `src/rebalance/ingest/sync_snapshot.py` (`get_device_id` :74), `src/rebalance/ingest/github_scan.py` :741-766, `tests/test_collector_contracts.py`, `tests/test_collector_registry.py`, `utils/pdda/check_read_layer.py`, `ARCHITECTURE.md` :138-200 and :355-360, `AGENTS.md`, `SOP.md` §3.6, reference reader `utils/clio-capture/clio-store.py` :1079-1096 (PR #371, not to be modified).
- Recorded operator decisions (2026-11-11): "new table + opt-in reads"; `github_activity` and the frozen `hiqs_work_activity` output stay byte-identical; XYZ-forge `board_sync` wiring is a separate follow-on, not this PR; the live flag-on smoke on the operator's Mac is **not** part of this task (fixture tests + a `dry_run=True` read of the live T3 file instead); no device config or installed-job changes; privacy: never select message text or any auth/secret/token/pairing/webhook table.
- Operational envelope: a local single-operator MCP server on a few Macs; T3 store is a local SQLite file; rows are per device. Grade against commensurate complexity — rebalanceOS requires new red-first tests (AGENTS.md, SOP.md §3.6), but no extra frameworks, daemons, schedulers, plists or scripts (GH-241), no enterprise/multi-tenant threat model.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-11-11
- Definition of Done: the plan is approvable when it (a) satisfies every issue Acceptance item or records an explicit operator-sanctioned deferral, (b) extends the existing collector registry / migration runner / read layer / doctor rather than building a parallel subsystem or second writer, (c) is grounded in the cited paths, (d) has falsifiable acceptance checks with red controls, and (e) has sound rollback and blast-radius notes.

### Reviewer instructions for this relay (GH-1414 paraphrase-first)
**Step 1 — before opening any source file or the evidence pack**, read only the artifact doc and write, at the top of your block, 2–5 sentences under **What this proposes**, 2–5 under **How the existing system works, per this document**, and a short **What it's not** (ground exclusions in the doc's own sections; label inference; distinguish excluded vs deferred vs unresolved). State the input boundary you used for the paraphrase.
**Step 2 — source-backed assessment**: then read the evidence pack and source paths above and answer, with `file:line` citations:
1. Are the "Recon deltas" D1–D8 correct against the evidence/source, and does the plan handle each correctly?
2. Does the aggregation contract (three independent streams merged per (repo, day, provider); message provider via primary-key lookup `COALESCE(run.provider, thread.default_provider)`) avoid count multiplication, and is the D5 `thread_days` naming an honest resolution?
3. Does the write path (build in memory → one `BEGIN IMMEDIATE`: device+window delete, insert, health upsert; rollback on failure; `error` health on extraction exception) meet the rollback acceptance item? Any ordering hole?
4. Is the schema guard (metadata version == 2 + `LIMIT 0` column probes, drift health, zero activity rows) sufficient and correctly placed relative to the read snapshot?
5. Registration as `raw_source`, `included_in_all=True` (D4) — does it correctly reuse the registry, and is changing the two pinned set tests the right minimal consequence? Any other consumer that iterates `COLLECTORS`/raw sources that would now be affected (e.g. `next_actions.py:707`, `semantic_index.py:684`, index_status signal health)?
6. Is the opt-in `_activity_repos` union safe by default and correctly scoped (also reaches `diagnose.py:149`)?
7. Does the test plan cover every Acceptance item with a real red control, without over-building? Is the live-smoke deferral recorded truthfully?
8. Anything missing, wrong, duplicated (second writer, parallel subsystem) or over-engineered? Check the CI ratchets (`check_read_layer.py` R1/R3, banned-imports gateway, script inventory) against the planned files.

Every `[Blocker]`/`[Should]` asking for a behaviour change carries `Observed input:`, `Affected scope:`, `Falsifier:`. Do not edit the artifact. Set `STATUS: Approved` only if it passes.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns. Plain blank separators may be added or removed between sections; preserve every substantive line, indentation, and fenced/literal blank line. A historical FAIL→PASS edit or changed fenced example is forbidden.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
