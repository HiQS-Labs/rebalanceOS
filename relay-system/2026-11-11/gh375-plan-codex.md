# RELAY · gh375-plan-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-11-11.
-->

NEXT: Producer
STATUS: Approved
ROUND: 2 / 3

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

### Reviewer · Round 1

**What this proposes**
Add a default-disabled T3 metadata collector, two destination tables, a separate activity MCP read tool and a DB-backed doctor check. Collection participates in the existing default refresh recipe; a second default-off flag allows its repos into the watched-repo set. Independent event aggregation and a transactional replacement preserve counts and prior data on failure.

**How the existing system works, per this document**
The collector registry drives refresh and scheduled collection, and the migration runner owns additive schema transactions. Existing work activity records GitHub authorship through a frozen output contract; CLIO captures prompts separately. Shared database, Git and device helpers already supply the integration points.

**What it's not**
Excluded: T3 writes, message text, GitHub activity changes, ranking, new scheduling and thread-ID storage. Deferred: Forge board integration, fleet export and the operator's live flag-on smoke; the proposed substitute is a read-only dry-run. Input boundary for this paraphrase: the entire artifact document only, before evidence/source review. This paraphrase was composed before those reads; the first attempt to persist it failed (`python` unavailable, exit 127), so it is persisted with the completed block.

swept file: yes

VERDICT: FAIL
Basis: sound integration approach, but D5 leaves the cross-provider rollup misleading for the explicitly planned provider-switch fixture. Resolve S1 before implementation. This is plan review, not execution approval or proof of passing tests.

- [Should] **S1 — make the rollup's counting unit explicit.** At `PROJECT/1-INBOX/GH-375-T3-CODE-SESSION-STORE.md:295` and `:328-330`, summing distinct threads from `(day, provider)` buckets is called `thread_days`. A single thread active through two providers on one UTC day contributes 2, although it is one thread-day. D5 correctly rejects a cross-day distinct-thread claim but does not resolve this second dimension. Cheapest fix: call the repo total `thread_provider_days` (per-provider `thread_days` can remain), or explicitly expose the provider-qualified counting definition in the MCP field documentation/output; pin the provider-switch fixture's expected total. No thread IDs or new storage needed.
  Observed input: the plan's provider-switch-within-one-thread acceptance fixture (`:351`), specialized to thread T on day D with one codex run and one claudeAgent run; the specified buckets each have `threads=1`, and their proposed repo `thread_days` sum is 2.
  Affected scope: repo-level sums across providers of the stored daily distinct-thread counters; run and prompt counts are unaffected.
  Falsifier: that same T/D/two-provider fixture must report 2 provider-qualified units, with the field's definition explicitly saying so; a single-provider T/D fixture reports 1. A field promising distinct thread-days would instead need to report 1 for both, which the current storage cannot generally derive.

- [Pass] **D1–D3, D6–D8 are grounded.** Evidence pack sections `Foundation.ts:150-172`, `EventSink.ts:390-410`, and `ProjectionStore.ts:736` name the actual metadata table and version writer. Its live-probe spans “elements: object 71”, “user/agent 620 | user/user 363”, “messages with NULL run_id: 751”, and “completed 643 | failed 11 | interrupted 3 | running 1” support the corresponding corrections. Reading only `createdBy`, branch and pullRequests narrows exposure. D8 is a sound inference from current thread payload plus event timestamps, not evidence of historical branch/PR attribution; the explicit “as of scan” qualification is appropriate (`:298`).

- [Pass] **Aggregation and rollback design.** The evidence pack's runs DDL declares `run_id TEXT PRIMARY KEY`; the D7 message lookup therefore cannot multiply message rows. Independent run/message aggregates and distinct thread sets avoid the row-to-row multiplication described in Acceptance. `:322-325` builds before deleting and encloses delete/insert/ok-health in one `BEGIN IMMEDIATE`; extraction-only error health is separate. Keep that exception boundary extraction-only: an insert failure must not subsequently overwrite health, as `:355` explicitly requires. The version/column guard inside the same `BEGIN` read snapshot (`:314-316`) is appropriately placed; missing metadata/tables/columns must follow the same drift path. These are design conclusions, not executed results.

- [Pass] **D4 and registry consumers.** `index_ops.py:135-159` derives all/default/semantic membership; `tests/test_collector_contracts.py:28` and `tests/test_collector_registry.py:33-58` pin all/default membership. Updating those expectations is the minimal intended consequence. `next_actions.py:707` skips collectors without candidates; `semantic_index.py:684-691` skips those without semantic providers, so this registration alone adds neither ranking nor semantic writes. `index_status` is different: source payloads are explicitly assembled (`index_ops.py:610-639`) and health iterates `_SIGNAL_HEALTH_RULES` (`:354-362`), not all registered collectors. The proposed registration therefore does not automatically add T3 to index-status signal health; the dedicated doctor check is the planned health surface.

- [Pass] **Opt-in union and shared ownership.** `index_ops.py:943-967` is the existing activity membership seam; `get_watched_repos` canonicalizes and deduplicates before applying ignored repos (`:1034-1085`). Appending through the read-layer helper behind the separate default-false flag preserves default membership and reaches the diagnostic caller (`diagnose.py:149`). `db/migrate.py:83-98` already owns migration transactions; `db/connection.py:90-104`, `git_ops.py:310,387`, and `sync_snapshot.py:74` supply the planned connection, remote parsing/execution and device identity. No second registry, writer or scheduling subsystem is proposed.

- [Pass] **Acceptance coverage and ratchets are proportionate.** The map at `:350-362` addresses each issue acceptance item and records the operator-sanctioned flag-on-smoke deferral truthfully. The rollback trigger/mutation and metadata-only SQL trace target material contracts. `check_read_layer.py` restricts R1 to four GitHub tables and exempts the DB read layer; R3 still requires shared time primitives rather than a new local day-window helper. `check_banned_imports.py:10-12,41` requires the existing SQLite gateway and avoids new direct datetime/subprocess imports in ingest; use the shared time module during implementation. The write-set introduces no scripts or plists. No baseline relaxation or exemption is needed by this design.

- [Nit] **Clarify health and dry-run edge states in the existing checks.** `:313-325` promises no dry-run health writes despite listing missing/drift/error writes earlier; make the dry-run guard cover every outcome. `:334-336` should spell out enabled-but-never-scanned versus disabled-with-retained-health, and select this device's health row. These clarify the stated per-device, no-write and successful-empty-versus-no-scan contracts; extend the planned state test rather than adding a suite.

- [Nit] **Pre-existing prose drift in the swept artifact.** The old rollback/risk text says “one CREATE TABLE IF NOT EXISTS plus an index” despite two tables, and the older Blast-radius paragraph says PR #371 uses “the same version check”; the reference `clio-store.py:1079-1096` has column probes, not that version guard. Treat Phase 0 as authoritative and correct these sentences when revising the artifact. No additional pre-existing material defect found in the artifact beyond the findings above; this is not a whole-codebase audit.

- [Unverified — needs clone run] No tests, fixtures, live-store reads, ratchets or Git commands were executed in this reviewer worktree. The full suite, mutation witnesses, tool invocation and live dry-run remain implementation evidence to retain in TESTS-RESULTS. Seeded live counts were reviewed as supplied, not independently remeasured. No probe-derived empirical finding is asserted.

Handing off to Producer (claude-a) — address S1 and disposition the clarifications, then return for review.

### Producer · Round 2 (claude-a)

Dispositions (artifact revised in `PROJECT/1-INBOX/GH-375-T3-CODE-SESSION-STORE.md`, Phase 0 section):

- **S1 — Implemented.** D5 row and step 6 now define two names: per-provider `thread_days` (sum of that provider's daily distinct threads) and the repo-level `thread_provider_days` (sum over (day, provider) buckets; one thread on two providers in one day counts 2). The MCP docstring will state the definition. The provider-switch fixture pins it: thread T2 runs on codex and claudeAgent on 2026-11-11 → those two buckets each have `threads=1`, and the repo's `thread_provider_days` includes 2 for T2 on that day. No storage change.
- **Nit (dry-run / health states) — Implemented.** Step 4 now says every health write (missing / drift / error / ok) is skipped on dry-run. Step 8 now selects this device's row and distinguishes the states: flag off → OK "not enabled (opt-in)", plus the retained status when an earlier row remains; flag on with no row → WARN "enabled, no scan recorded yet"; then missing / drift / error / stale / ok. The planned doctor state test covers these; no new suite.
- **Nit (pre-existing prose) — Implemented.** The Risk line now reads two `CREATE TABLE IF NOT EXISTS` plus one index. The Blast-radius row no longer claims #371 has a version check: it says #371 uses `?mode=ro` + `LIMIT 0` probes, and this issue adds the version guard.
- **Ratchet note from the [Pass] on acceptance/ratchets — Implemented as new step 9a.** `ingest/t3_code.py` imports neither `datetime` nor `subprocess` (GH-126). One shared primitive, `time_ops.utc_date_days_ago(days)`, goes in `src/rebalance/lib/time_ops.py` and is used by both the collector and `fetch_agent_activity`. Its name avoids the R3 `day_(bounds|window)` pattern, and it is not the verbatim `strftime` cutoff. Git calls use `run_git`. No baseline or pragma change.
- Kept as approved: aggregation contract; extraction-only `error` health (a write/insert failure never touches health, as the rollback acceptance requires); guard inside the read snapshot; D4 registration and the two pinned-set updates.

Handing off to Reviewer (codex). Re-check S1 and the Nits against the revised Phase 0 section, then approve or return.

### Reviewer · Round 2

**What this proposes**
Add an opt-in T3 metadata collector through the existing refresh registry, with separate per-device activity and health tables. Independent event streams feed daily provider buckets; the MCP rollup now names the repo total `thread_provider_days` and defines its provider-qualified unit.

**How the existing system works, per this document**
The registry drives the default refresh and scheduled collection, while the existing migration runner and database gateway own transactions and connections. GitHub authorship has a frozen, separate output contract; shared Git, device and read-layer helpers supply the proposed integration seams.

**What it's not**
Excluded: message text, T3 writes, ranking, scheduler changes and changes to GitHub activity. Deferred: Forge board integration, fleet export and the live flag-on smoke; the latter is explicitly replaced for this task by a live read-only dry-run comparison. Input boundary: the entire artifact document only, before opening evidence or source this turn.

swept file: yes

VERDICT: PASS
Basis: S1 is resolved, the health clarifications are explicit, and the full artifact remains a proportionate implementation plan satisfying the Definition of Done. Approval is for the plan; implementation evidence is still outstanding.

- [Pass] **S1 resolved.** `PROJECT/1-INBOX/GH-375-T3-CODE-SESSION-STORE.md:295` defines repo `thread_provider_days` as the sum over (day, provider), explicitly counting one thread on two providers in one day as 2; `:328-331` uses that field in the output contract. Per-provider `thread_days` remains honest. The Producer's pinned T2 example matches that definition; no new storage is required.
- [Pass] **D1–D8 and aggregation remain sound.** D1–D3 and D6–D7 (`:291-297`) match the supplied evidence pack's named metadata DDL/version writer, object-valued PR elements, provenance cross-counts and nullable message run IDs. The evidence's `055_OrchestrationV2.ts:73-82` declares `run_id TEXT PRIMARY KEY`, so the D7 lookup cannot multiply messages. Independent event aggregation plus distinct contributing-thread sets retains the intended counting units. D8 (`:298`) correctly qualifies branch/PR metadata as “as of scan”; it does not claim historical branch attribution. These are source/design assessments, not independent live measurements.
- [Pass] **Guard, write ordering and clarified health.** Artifact `:313-325` puts version/column checks within one read snapshot, builds rows before destination deletion, and places deletion, insertion and success health in one `BEGIN IMMEDIATE`. Extraction-only error health preserves the insertion-failure rollback contract; the second-insert trigger test at `:362` must preserve both prior rows and health. The explicit “Every health write ... is skipped on dry-run” at `:313` closes the clarification. Device-scoped doctor states at `:334-339` distinguish disabled-with-retained-health, enabled-with-no-scan and successful-empty scans. No ordering hole is evident in this plan.
- [Pass] **Registry and opt-in coverage.** `index_ops.py:135-159` derives raw/default/semantic scope membership; the exact-set expectations in `tests/test_collector_contracts.py:28` and `tests/test_collector_registry.py:33-58` are the intended minimal updates. `next_actions.py:707-713` skips absent candidate providers, and `semantic_index.py:684-691` skips absent semantic providers. Index-status source payloads/health remain separately assembled (`index_ops.py:354-362,610-639`); dedicated doctor health is the planned surface, not an automatic index-status extension. The separate default-false watch flag (`artifact :309,332-333`) leaves default membership unchanged, reaches the diagnostic caller, and reuses `get_watched_repos` canonicalization/ignored-repo filtering (`index_ops.py:1034-1085`).
- [Pass] **Shared primitives and ratchets.** Step 9a (`artifact :344-347`) puts the date primitive in the existing shared owner, alongside `time_ops.now_utc` and `parse_utc_iso`, and shares it across collection and reads. This is a suitable small extension, rather than a local window helper. `check_read_layer.py:57-72` limits R1 to GitHub activity tables and defines R3's window patterns; `check_banned_imports.py:24-39` names the existing SQLite gateways and prohibited ingest import families. The proposed gateway, shared time and Git calls fit those contracts without exemptions. Migration transaction ownership is already documented in `ingest/db/migrations/README.md` and implemented at `db/migrate.py:83-98`. No second writer, registry, daemon, script or plist is proposed.
- [Pass] **Acceptance and full-document sweep.** The acceptance map (`artifact :353-369`) retains concrete controls for counts, drift, empty/missing, idempotence, rollback, migrations, frozen GitHub output, SQL privacy, actual MCP invocation and doctor states. The live flag-on smoke is explicitly an operator-sanctioned deferral (`:369`), with a dry-run comparison substituted rather than claimed equivalent to persisted collection. The original issue text remains historical where Phase 0 overrides it. The two prose corrections are present: “two CREATE TABLE IF NOT EXISTS statements plus one index” in Risk, and the Blast-radius row correctly attributes column probes rather than a version guard to #371. No additional material pre-existing defect found in the swept artifact; this is not a whole-codebase audit.
- [Unverified — needs clone run] No tests, executable fixtures, live-store reads or ratchets were run this turn. Implementation, mutation witnesses, privacy tracing and the live dry-run comparison still require the disposable clone and retained TESTS-RESULTS campaign. Source/document reads are not behavioural verification.

Relay closed (Approved), no further turn needed. Producer (claude-a) may proceed with implementation in the authorized task clone.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
