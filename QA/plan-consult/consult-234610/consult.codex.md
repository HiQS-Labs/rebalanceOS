**NO FIRSTHAND VERIFICATION CITED** — treat conclusions as conditional (codex's answer carries an unsupported [Pass]/verified/confirmed-style claim with no quoted span or file:line citation nearby, despite the consult PREAMBLE asking advisors to cite evidence.)

> **ATTESTATION**
> Model: gpt-6-astra
> Provider: openai
> Sandbox: read-only

Reading additional input from stdin...
OpenAI Codex v0.159.1
--------
workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
model: gpt-6-astra
provider: openai
approval: never
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a10083-5bd8-71a3-9eb2-f33bba397f00
--------
user
You are an INDEPENDENT advisor in a one-shot cross-model consult. Another model is answering the SAME question separately and a coordinator will reconcile both answers, so give your own honest, specific read — do not hedge toward a consensus you cannot see. Read any repo files the question references (cite file:line). Respond with: (1) a short direct ANSWER; (2) graded FINDINGS — [Blocker]/[Should]/[Nit]/[Pass] — where applicable; (3) a one-line RECOMMENDATION. You are ADVISORY ONLY: output your analysis as text; do not rely on writing files (you are running in a throwaway copy).

=== CONSULT QUESTION ===
# Plan review request — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter

You are reviewing a PLAN (pre-implementation) for a small, operator-directed naming change in the rebalanceOS repo. Grade against the stated requirements and commensurate complexity — this is a labels-and-aliases change, not a schema migration; do not demand enterprise machinery.

## Task (issue #316, abridged)

Make "HiQS work activity" (HiQS = High Quality Signals) the canonical label and namespace for the per-project GitHub work-activity signal:

1. REQUIRED backwards-compatibility adapter: MCP tool `github_balance` stays registered + functional (docstring marks it deprecated alias); new canonical MCP tool `hiqs_work_activity`; Python `get_hiqs_work_activity()` canonical with `get_github_balance` kept as alias.
2. Contract freeze: SQLite table `github_activity`, SQL reader `fetch_github_balance`, and ALL output keys (`project_name`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `repos_touched`) unchanged — consumed by external experiments (issue #300, Needle-fork#79).
3. Operator-facing strings presenting the SIGNAL relabel to "HiQS work activity"; strings describing ingestion of the raw GitHub data source stay literal.

## Plan doc (review this)

- `PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md` — includes Phase 0 prior-art with file:line cites, requirements, ordered smallest surface, non-goals, risks, test/gate.

## Source paths to verify claims against

- `src/rebalance/mcp/tools/projects.py` (FastMCP tool `github_balance`; `projects.register`)
- `src/rebalance/ingest/github_scan.py` (`get_github_balance`, ~line 741)
- `src/rebalance/ingest/querier.py` (line ~287 "## GitHub Activity (last 7 days)")
- `src/rebalance/cli/query.py` (~line 118), `src/rebalance/cli/github.py` (~64,72), `src/rebalance/cli/onboard.py` (~124)
- `src/rebalance/ingest/db/queries.py` (`fetch_github_balance`, `CLOUD_AGENT_AUTHORS`), `src/rebalance/ingest/db/schema.py` (`github_activity` table)
- `tests/test_mcp_probe.py`, `tests/test_queries_mirror_invariance.py` (guard baselines)
- `README.md`, `AGENTS.md`

## Questions

1. Are the plan's file:line claims grounded in the actual code? Any surface the plan MISSES where the signal is operator-facing (CLI output, pulse/dashboard renderers, MCP descriptions, docs)?
2. Is the adapter design right — is aliasing at the MCP-tool + Python-function boundary sufficient, and is freezing the table/SQL/JSON contract the correct line? Any consumer you can find that would break?
3. Does any relabel risk corrupting the ingestion-vs-signal distinction (the label rule)? Name specific strings if so.
4. Are there existing tests/ratchets (`mirror_invariance`, read-layer, script-inventory) that the change would trip? 
5. Version: plan proposes 0.98.0 → 0.98.1 PATCH (aliases + labels, no behavior change). Agree?
6. Are the ratings (55/15/50/55) grounded for a naming-consistency ask?

Output: verdict APPROVE / CHANGES with numbered findings, each citing file:line evidence.

hook: SessionStart
hook: SessionStart Completed
codex
I’ll read the plan and cited sources, then check for missed operator-facing labels and compatibility risks.
exec
/bin/zsh -lc 'cat /Users/noelsaw/.codex/skills/swe/SKILL.md; cat ARCHITECTURE.md; cat SOP.md; cat PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
 succeeded in 0ms:
---
name: swe
description: Apply software-engineering standards when authoring or reviewing project plans, build/spec/PRD documents, architecture RFCs, or agent governance. Use for "write a plan", "review this build doc", "apply our SWE standards", or "is this plan ready to build"; also apply before drafting a project plan. Grades grounded recon, minimal scope, diagnosis, blast radius, and verifiable acceptance. This is a planning rubric, not a debugging or execution pipeline.
---

# SWE

Vibe the build; engineer the plan. This lens is the discipline that lets a fast v1.x ship without becoming a liability.

A governance overlay for **build/spec documents** — the "build v1.x" doc, the implementation spec, the architecture RFC. It does not debug code or pick a tradeoff in the moment; it reads the *plan* and asks whether the plan already embodies the engineering standards before a single line is written. Run it two ways: as an **authoring gate** (write the doc against it) or as a **review rubric** (read a doc, emit findings + a verdict). The whole bet: most plans fail not on the feature but on the five things below, smuggled past in prose — starting with Pillar 0, where the plan is grounded (or not) in the system as it actually exists.

## Pillar 0: Recon — is the plan grounded in a system anyone actually read?

The four pillars grade what the document *says*. Pillar 0 grades its **provenance**: was it written against the system as it exists, or from the prompt plus three grepped files? This pillar is about evidence, not consequences — what breaks when a *step* runs is Blast's job, below.

- [ ] The current system was traced before the first plan heading: entry points and call paths in, every read *and write* site of the state involved, the contracts crossed, the failure and rollback paths today.
- [ ] Claims about what the change touches cite code somebody read — `file:line`, not "various downstream."
- [ ] What could not be verified is listed as an explicit unknown with the command or file that would settle it, never smoothed into the findings.

**Applicability first.** Pillar 0 does not apply to greenfield work, a non-code plan, or a change contained to files the doc already quotes — mark it N/A and say why. Where it does apply, grade the *evidence*, not the artifact: a [recon](../recon/SKILL.md) Recon Map is the standard form, but a trace embedded in the doc or supplied by the author counts. **Block** only when the doc makes claims about an existing system that nothing behind it verifies; a thin trace on a genuinely small change is a **Fix**, not a Block.

**Pillar 0 feeds Blast; it does not satisfy it.** The trace establishes the *current-state* radius — who depends today on what the plan touches. Blast then asks what each proposed step *adds*: new systems, new data, new people, the shield, the tripwire, the undo class. Copying the map's radius into the Blast section unchanged understates the plan's own impact and fails Blast on its own terms.

## The four pillars

Each pillar is a lens on the document. A v1.x doc that satisfies a pillar contains the thing explicitly; a doc that "implies" it fails the pillar — implied is unbuilt.

### 1. Minimal (Ponytail) — does the plan earn each part it adds?

The plan's default answer to "add a thing" is *no*. Scope, dependencies, and abstractions are all liabilities until justified in the doc.

- [ ] Every new component answers "does this need to exist?" (YAGNI) — speculative scope is cut or deferred, not built.
- [ ] Sourcing ladder is honored to minimize mechanism, not requirements: stdlib → native platform feature → already-installed dep → one line of our own. A new dep names what it buys that the rung above does not. (Security and observability requirements are never simplified away, only implemented via the laziest viable mechanism).
- [ ] No premature abstraction — the plugin layer / framework / generic engine is justified by ≥2 concrete present uses, not one hypothetical future one.
- [ ] Bias is stated: delete > add, boring > clever, shortest diff that works. A complexity cap is named (e.g. stdlib-only, ~600-line ceiling) where it applies.

*Planning translation:* this is the editor pass on scope. Most v1.x bloat is decided here, in the doc, long before code.

### 2. Diagnosable (Mantra) — does the plan say how it will fail and be found?

A build doc that provisions zero observability is a debugging session deferred to production. Bake the diagnosis path into v1.x, not v1.next.

- [ ] Instrumentation is right-sized but explicit: a single actionable error log is better than an unread ELK stack, but silent failures are blocked. The plan names the exact log, metric, or alert that fires when it breaks.
- [ ] Every iterate/retry loop has a **stop condition** (e.g. 5-failure hard stop, 10-total cap). An unbounded "retry until it works" is a defect in the plan.
- [ ] Failures are made reproducible: the plan names how a failure is repro'd, and treats intermittent failure as a *signal* (concurrency / ordering / env / TOCTOU), not noise to retry away.
- [ ] State changes are auditable — append-only event log over in-place mutation where the history matters.
- [ ] **The plan names debug-mantra as its execution-time debugging protocol** — "we'll figure it out when it breaks" is a Diagnosable failure.

*Planning translation:* the runtime debugging ritual, pulled forward. If the doc can't say how you'll see it break, you'll see it break in prod.

### 3. Blast — does the plan price its irreversible moves before committing?

For every wide-impact or hard-to-undo step, the doc must already carry the cost. Don't dress a one-way door as a tweak.

- [ ] Each risky step names its **undo class**: easy / costly / one-way door. One-way doors are flagged, never silent.
- [ ] **Blast radius** is named — the exact systems, data, and people that break if this step goes wrong (not "various downstream").
- [ ] A **shield** is specified — flag, adapter, pilot/canary, dual-write, or an explicit "none."
- [ ] A **tripwire** exists for anything costly or one-way: *how* you'll know to pull it and *by when* (the point of no return). A shield with no tripwire is a brake with no warning light.

For the full per-decision accounting, defer to the **blast-radius** skill — this pillar only enforces that the v1.x doc *contains* that accounting for its irreversible steps.

### 4. Proof (Done) — can the plan prove it's finished, separately from claiming it?

Editor and grader are different roles. The plan must define "done" in terms something other than the author can check.

- [ ] Every task has a **measurable done-criterion** — a checkable output or metric, not "works" / "improved" / "robust."
- [ ] Tests are specified *and the plan requires they actually run* — "tests pass" means an execution artifact, not an assertion.
- [ ] **No orphan tasks**: every step maps to a success criterion, and every success criterion is covered by a step.
- [ ] **Closed loop**: For medium/large efforts, backend/data work must explicitly connect to a user-facing UI plane or final consumer. Fetching data without surfacing it to the user is an incomplete loop.
- [ ] **Observed vs. predicted is kept separate** — the doc never launders a projection ("this will reduce load 40%") as evidence. Predictions are labeled as such.

*Planning translation:* PlanProof's editor/grader separation at document scale. The grader reads only what's written, not what the author meant.

## House invariants

Non-negotiable conventions a v1.x doc must satisfy regardless of pillar. These are cheap to check and expensive to skip.

- [ ] **FSM threshold** — model an explicit state machine only past ~4 states; below that a flag or enum is leaner. Past it, an ad-hoc tangle of booleans is the defect.
- [ ] **Single write path** — one writer per piece of state. Multiple write paths to the same table/file are a race waiting to happen; name the single path.
- [ ] **Append-only event log** only when audit or history is an explicit business requirement (JSONL or equivalent); otherwise, simple in-place updates are the default.
- [ ] **UTC-only** time handling end to end; local time only at the display edge. "Nightly," "daily," "expires in 24h" all imply a timezone — pin it.
- [ ] **Crash-safe / idempotent jobs** — cron and background work are resumable and safe to run twice. A job that corrupts state on a mid-run crash is unshipped.
- [ ] **Checklist standard** — actionable items use the `- [ ]` hyphen prefix in GitHub-flavored Markdown, never bare `[ ]` in tables or lists.
- [ ] **Agent contract current** — for agent-built work, AGENTS.md / CLAUDE.md exists and matches the plan (conventions, loop caps, honesty constraints). The project's AGENTS.md must name SOLID compliance as a coding standard; if it doesn't, the plan has no enforceable code-design contract.

## Zero-Downtime Expand-Contract Schema & State Migration Rubric

When planning online schema changes, state re-encodings, or persistent data migrations across rolling deployments or mixed-version clients, the plan must budget lock/backfill rates, define stop/rollback tripwires, and enforce the 6-stage lifecycle:

1. **Stage 1 — Expand:** Add the new column, field, or data store as nullable or optional, with concurrent write synchronization in place so new writes populate both shapes without breaking existing readers.
2. **Stage 2 — Backfill & Continuous Sync:** Execute an idempotent, rate-limited background backfill. Any concurrent updates occurring during the backfill and mixed-version window MUST reach the new representation with an explicit conflict/ordering strategy.
3. **Stage 3 — Convergence Gate:** Run an automated parity/reconciliation assertion verifying data convergence across old and new representations before cutting over read traffic.
4. **Stage 4 — Switch Reads:** Redirect query and read paths to the new representation, retaining graceful fallback to the legacy shape if read errors occur.
5. **Stage 5 — Dual-Write & Mixed-Version Support:** Continue bidirectional synchronization / updating both representations for every representation still read by active versions, offline clients, or needed by application rollback throughout the entire mixed-version window.
6. **Stage 6 — Contract & Retire:** Ending legacy updates and dropping legacy fields/columns is strictly gated on:
   - (a) Full retirement and migration of all legacy writers.
   - (b) Full retirement of all legacy readers.
   - (c) Full retirement of delayed, queued, or asynchronous consumers.
   - (d) Closure of the application rollback window (or verified reverse synchronization if rollback occurs).

---

## How this differs from the sibling skills

- **swe** — "Does this *plan* embody our engineering standards before we build?" The standard/rubric, applied to a whole document.
- **recon** — "What is actually there?" The read-only trace of the current system that Pillar 0 grades the doc against. It supplies the current-state radius; Blast extends that radius per proposed step. Run recon first in author mode when the plan changes an existing system.
- **phase-0-spike** (an external workflow at `~/.claude/workflows/phase-0-spike.js`, not a skill in this repo) — the deep seam map, contract owners, and rollout invariants for a refactor that is already committed to. `recon` is the cheap universal pass before any plan; phase-0-spike is the expensive one after the refactor is approved. A v1.x doc for a subsystem refactor cites one or the other, never neither.
- **plan-adversarial-serial** — the *pipeline* (generate → review → revise → review → judge). It is the machinery; `swe` is one of the standards the machinery can enforce. Compose them: run the adversarial pipeline with `swe` as the lens content.
- **blast-radius** — "How big is *this one decision* and what breaks?" `swe`'s Blast pillar defers per-decision accounting to it.
- **iron-triangle** — "Which of speed/cost/quality is *this choice* trading?" When a plan forces fast/cheap/good tension, hand that node to it.
- **debug-mantra** — the four-step runtime debugging discipline (reproduce → fail path → falsify → breadcrumb). Diagnosable enforces the plan names it; debug-mantra governs live execution — composing across the doc/session boundary.
- **take-a-step-back** — "Is this the right problem/frame at all?" Runs *before* there is a plan to govern.
- **bottom-line** / **linear** — compress or sequence output. `swe` evaluates a plan's substance; those reshape its presentation.

Reach for `swe` the moment there is a build/spec document to hold to a standard — authoring one or judging one.

## How to apply

**Author mode** — you are writing the v1.x doc. Clear Pillar 0 first (run recon, or state why it was skipped), then use the four pillars and house invariants as the doc's skeleton: each feature passes Minimal before it earns a section; each risky step ships with its Blast block; each task ships with its Proof criterion. The lens is the gate, not a later edit.

**Review mode** — you are handed a v1.x doc. Walk Pillar 0, then the four pillars, then the invariants. For each gap, emit one finding keyed to the doc location (`§section`, or `file:line` for code-adjacent specs), tagged by severity, with the *cheapest* fix first. Close with a verdict. Do not rewrite the doc unless asked — surface the checkable gaps and let the author act.

## Project plan scaffold (Author mode)

When the ask is "write a project plan" / "write a plan" (authoring, not reviewing), clear Pillar 0 first, build the doc against the four pillars **and** lay it out in the fixed structure below. The structure is load-bearing, not decoration: the status table forces an honest "where are we" at a glance, the Table of contents keeps a long plan navigable, observable checklist items *are* the Proof done-criteria, and the per-phase QA checklist is the grader pass made mechanical. Implied is unbuilt — so every field below is written down, not assumed.

Required order, top to bottom: **frontmatter → status table → table of contents → phases (each with observable todos) → per-phase QA checklist**.

````markdown
---
title: <Project> — Build Plan
status: Not started | In progress | Blocked | Shipped
owner: <name>
created: <YYYY-MM-DD>   # UTC
updated: <YYYY-MM-DD>   # UTC — bump every time the plan changes
reversibility: Easy | Costly | One-way door — <one line of why>
---

# <Project> — Build Plan

| Most recently completed phase | What's next |
| --- | --- |
| — (not started) | Phase 1: <name> |

## Table of contents
- [Phase 1: <name>](#phase-1-name)
- [Phase 2: <name>](#phase-2-name)
- [Phase 3: <name>](#phase-3-name)

## Phase 1: <name>
**Goal:** <one observable outcome this phase delivers — not "work on X">

- [ ] <observable todo: names a checkable output or artifact>
- [ ] <observable todo>
- [ ] <observable todo>

### Phase 1 — QA checklist
- [ ] Every todo above produced its checkable output (no orphan tasks)
- [ ] Tests **run**: existing suites, plus new ones only where the repo allows them. Where it does not (XYZ-forge: `AGENTS.md` *No new tests*, GH-831) and no existing suite covers the change, a manual check recorded under `TESTS-RESULTS/` counts. Point to the execution artifact, not an assertion
- [ ] Diagnosable: logs + correlation id present; every loop has a stop condition
- [ ] Blast: each risky step names undo-class + shield + tripwire (or explicit "none")
- [ ] Status table and `updated:` date refreshed before this phase is marked done

## Phase 2: <name>
...
````

Filling it:

- **Frontmatter** — the at-a-glance contract. Keep `status`, `updated`, and `reversibility` honest; a stale `updated` date is the first sign the plan drifted from reality.
- **Status table** — exactly two columns, one row. It is the single source of truth for "where are we"; update it as the *last* step of finishing a phase, never before. Don't expand it into a multi-row log — that's what phases are for.
- **Phases** — split by observable milestone, not by calendar. Apply the Minimal pillar to phase count too: only as many phases as the work earns. Each phase has one `**Goal:**` line stating the outcome it delivers.
- **Observable todos** — every `- [ ]` names a checkable output, not an activity. "Add retry cap of 5 to the reconciler loop" passes; "improve reliability" fails. Use the `- [ ]` hyphen prefix (house Checklist standard), never bare `[ ]`.
- **Per-phase QA checklist** — closes each phase against the four pillars. It is Proof's editor/grader separation per phase: the boxes are checked by running things, not by the author asserting done. A phase isn't complete until its QA checklist is.

## Output format (Review mode)

Lead with the verdict in one line. Then findings, ordered by severity, then quick wins first within a severity. Keep it tight — clean plans get a short list, not a manufactured one.

**Verdict:** **Ship** · **Ship with conditions** · **Block** — [one sentence: the load-bearing reason].

**Findings:**

| Loc | Pillar | Severity | What breaks | Cheapest fix |
| --- | --- | --- | --- | --- |
| §x.y | Blast | Block | One-way migration with no rollback named | Add a dual-write window + a row-count tripwire before cutover |
| §x.z | Proof | Fix | "Improves sync" has no done-criterion | State the measurable signal (e.g. drift count → 0 over 3 runs) |

Severity: **Block** (cannot build safely as written — unguarded one-way door, no done-criteria, unbounded loop) · **Fix** (change before v1.x ships) · **Note** (improvement, optional).

**Quick wins:** [the 1–3 findings fixable in a line of doc, listed as `- [ ]` so the author can tick them off.]

## Principles

**Implied is unbuilt.** A plan gets credit only for what it states. "Obviously we'll log it" is a Diagnosable failure; write it down or it won't exist.

**Editor and grader are different roles.** The strongest constraint in the whole lens is Proof's separation: done is defined by something the author can't fudge. Keep them apart.

**Price the one-way doors loudest.** Reversible mistakes are cheap; irreversible ones are the only ones worth slowing down for. A tweak that can't be undone is not a tweak.

**Cut scope before breaking a corner.** When the plan is overloaded, the Minimal pillar and scope-reduction beat heroics. Defer to `iron-triangle` when the tension is explicitly fast/cheap/good.

**Stop conditions are not optional.** Any loop in the plan — retry, fix-iterate, agent relay — names its cap. Unbounded means undefined.

**Separate what you saw from what you expect.** Observed evidence and predicted behavior are different epistemic objects; a plan that blends them is lying to its future reader.

**Don't manufacture findings.** A genuinely clean v1.x doc gets "Ship" and a short list. The lens enforces a standard, not a quota of objections.

## Example — reviewing a v1.x build doc excerpt

Input (abridged):

> **§3 Nightly order reconciler.** A cron job runs each night to reconcile order state against the upstream system. For each order it pulls upstream status and updates `wp_orders` to match. On mismatch it retries until the write succeeds. This makes order state reliable.

Output:

> **Verdict:** **Block** — a nightly DELETE/UPDATE against the orders table with an unbounded retry, no tripwire, and no measurable "reliable" can corrupt order state with no way to know or stop it.
>
> **Findings:**
>
> | Loc | Pillar | Severity | What breaks | Cheapest fix |
> | --- | --- | --- | --- | --- |
> | §3 | Diagnosable | Block | "retries until the write succeeds" is an unbounded loop | Add a 5-failure hard stop / 10-total cap, then dead-letter the order |
> | §3 | Blast | Block | Bulk overwrite of `wp_orders` is costly-to-one-way with no shield/tripwire | Run in observe mode first; add a row-count + mismatch-rate tripwire before any write mode |
> | §3 | Proof | Fix | "makes order state reliable" has no done-criterion | Define it: drift count → 0 across 3 consecutive runs, logged |
> | §3 | House (UTC) | Fix | "each night" has no timezone | Pin the schedule to UTC; document the local display offset separately |
> | §3 | House (write path) | Note | Reconciler is a second writer to `wp_orders` | Name the single write path, or gate the reconciler behind the same one |
>
> **Quick wins:**
> - [ ] Add the loop cap (§3) — one clause.
> - [ ] Pin "each night" to UTC (§3) — one word.
> - [ ] Replace "reliable" with the drift-count criterion (§3) — one sentence.

## What success looks like

The author sees, before any code exists, exactly where the plan is a wish rather than a build: the loop with no cap, the migration with no rollback, the task that can't prove it's done. The best outcome is a v1.x doc that ships fast *because* its risky parts were priced up front — not one that ships fast and pays later.
# rebalance OS — ARCHITECTURE.md

> **Before building anything, check whether it already exists.** The four prior-art checks (open PRs on *both* repos, `ROADMAP.md` → In progress, a cross-package grep including `HiQS/` and `utils/3-eyes/`, and the full suite including the parts CI skips) are in [ROUTER.md](ROUTER.md) — canonical there, deliberately not restated here.


> How data flows through the system. For execution decisions see the [PROJECT/](PROJECT) docs — canonical detail for a specific effort, governed by [PROJECT/PDDA.md](PROJECT/PDDA.md) — for tool specs see [MCP.md](MCP.md), for the *why* behind these decisions see [GUIDING-PRINCIPLES.md](GUIDING-PRINCIPLES.md).

> **New maintainer? Start with [Maintainer Orientation](#maintainer-orientation-start-here)** — the load-bearing symbols, the two hubs, where to start reading, and one end-to-end trace. **This doc is load-bearing, not decorative:** `audit_modules` (the `audit_modules` MCP tool / [scripts/audit_modules.py](scripts/audit_modules.py)) and the PDDA gate enforce that collectors, render modules, and scheduled jobs stay documented here — update ARCHITECTURE.md in the *same PR* as any structural change.

---

## Core Pipeline

**Opt-in historical projection (GH-230):** `src/rebalance/ingest/clio_journey.py` (run as `rebalance clio-journey-replay`) reads a frozen CLIO JSONL
prefix or canonical marker-backed Markdown export and existing GitHub snapshots via the read-only
DB gateway. It emits a new private run directory with two journey views, source evidence and coverage.
It is not an `all` collector, never updates the index, and does not call a model or publish into a vault.
Its opt-in `--explicit-links-only` policy joins outcomes only through typed qualified GitHub URLs;
other mentions are retained under `unresolved_refs` and excluded from grouping/event attachment.
The independent `--qualified-transitions` option adds a third candidate view for exact new-task
requests naming a different qualified issue. Its grouping and event joins use qualified URLs
regardless of legacy reference settings. Original views and start hints remain unchanged; a split
is not completion. The GH-232 retained-metadata composition recipe is campaign-only, not a new
runtime adapter or collector.
The independent `--issue-evidence` flag appends all qualified trial-issue mentions, including
unassigned prompts, with separate chat labels and visible coverage gaps. It does not alter original
grouping, start hints or evidence membership. Pull-request/foreign/bare-number mentions cannot
supply trial-issue identity; direct issue facts retain event and retrieval times separately.
The campaign-only retained-facts recipe can compose `closingIssuesReferences` via `--delivery-links`
and append three fixed A/B comparisons via `--review-cases`. Whole artifact URLs, typed identities,
merge state/window, retrieval chronology and conflicting records are checked before publication.
This is not the production `github_links` text-matching store or reconciliation scorer. Optional
renderer metadata adds observed relationship receipts, never chat causation or deployment proof.

**INVARIANT**: **Compose, don't mutate**. No new query surfaces (like `semantic_query` vs `ask`) or UI renderers (web server vs static HTML) may be introduced without a plan to deprecate and replace the old one. If extending an existing pipeline, build reusable primitives in `src/rebalance/lib/` instead of duplicating logic in the caller.

```
Signals (data sources)
  │
  ▼
Ingest Layer (source-specific collectors)
  │
  ▼
SQLite + sqlite-vec (unified local store)
  │
  ▼
Query Layer (context gathering + prompt assembly)
  │
  ▼
Two-Layer LLM
  ├── Layer 1: Local Qwen3 (fast first-pass synthesis)
  └── Layer 2: Host Agent (review, adapt, present)
  │
  ▼
User (via MCP host: VS Code, Claude Desktop, etc.)
```

Every raw incoming source follows the same pattern: **collect → normalize → store → query**. The collector registry in `index_ops.py` currently also includes derived local scans and post-ingest/export jobs (`code`, `semantic`, `sync`, `focus5`, `ask_self`), so not every registered scope is a raw upstream signal. The query layer and LLM layers are source-agnostic once data is in SQLite.

### Sync model (in plain English)

Every `refresh_index` run is **incremental** — nothing is re-downloaded from scratch. What "incremental" means depends on what the upstream API lets us ask for cheaply, but three patterns cover every source:

1. **Hash/ID delta** — only fetch or reprocess what actually changed. Used by: vault notes, GitHub artifacts, embeddings.
2. **Window refetch + upsert** — refetch a bounded time-or-count window every run and upsert by ID; nothing is auto-deleted. Used by: GitHub activity (last 30d events), calendar (30d back / 7d forward), email (newest 100 `in:inbox` messages).
3. **Full refetch + column-diff** — refetch the whole upstream set, compare row-by-row, and keep everything as history. Used by: sleuth reminders.

A few caps to know about up-front:

- **Email** is capped at the **newest 100 inbox messages per run** today (Phase 1, shipped 2026-05-12) — default filter `in:inbox`, overridable via `gmail_query_filter` in `temp/rbos.config`. Not "important and starred." See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).
- **Calendar** refetches a **30-day back / 7-day forward window** by default; a 365-day backfill is available on demand via the CLI.
- **GitHub activity** is bounded by the GitHub Events API's own ~30-day retention.
- **Vault, sleuth, embeddings** are unbounded — they cover everything they can see.

Detailed per-source mechanics live in [Storage Layer → Sync semantics per source](#sync-semantics-per-source).

---

## Maintainer Orientation (start here)

New to the codebase? Read this section first — it is the mental model the rest of the doc assumes.

### The two hubs (the model that prevents confusion)

The system has **two** central things with *opposite* roles. Conflating them is the most common newcomer mistake:

- **Orchestration spine — fan-OUT.** `refresh_index()` plus the `COLLECTORS` registry in
  [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py) reach **out** into every collector. This is the
  one intended write/refresh entry point. New ingestion work registers here (`register_collector(Collector(...))`).
- **Persistence base — fan-IN.** [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_database_path()` (answers *which* DB file)
  → `db_connection()` in [src/rebalance/ingest/db/](src/rebalance/ingest/db) (answers *how* to open it). Everything reaches **down** to these.

They compose in a single hop (`refresh_index() → db_connection()`). Keeping orchestration and persistence in
**separate** nodes is *why the codebase has no god-object* despite `db_connection()` being the single most-connected
symbol: it is a thin, stateless connection factory (a dependency *sink*), not a place where logic lives. **Read from it
freely; think twice before changing it** — its blast radius is the whole system.

### Load-bearing symbols (you will see these in almost every file)

| Symbol | Where | What it is / why it's everywhere |
|---|---|---|
| `db_connection()` | `ingest/db/connection.py` | SQLite factory (WAL, foreign keys, 30s busy-timeout, sqlite-vec). Every collector opens its connection here. **High fan-in, zero business logic.** |
| `resolve_database_path()` | `paths.py` | "Which DB file" — layered resolver (`--database` flag → `REBALANCE_DB` → canonical app-data path → user config). Single source of truth for the DB location. |
| `_read_config()` / `_write_config()` | `ingest/config.py` | Layered config + secrets (`temp/rbos.config` + keyring/secret-store). |
| `CalendarConfig` | `ingest/calendar_config.py` | Validated calendar settings (event filters, signal weights). |
| `normalize_github_repo_name()` | `ingest/github_scan.py` | Canonical `owner/repo` string used across every GitHub path. |
| `refresh_index()` | `ingest/index_ops.py` | The orchestrated ingest entry point (see "two hubs" above). |
| `rank_next_actions()` | `ingest/next_actions.py` | Entry point for the "what to do next" engine (see [Query Layer](#the-next-actions-engine-what-to-do-next)). |
| `run_doctor()` | `doctor.py` | Health-check orchestrator; backs `rebalance doctor` (run it before claiming a change works). |

### Where to start reading when touching X

| If you're working on… | Start in | Then read |
|---|---|---|
| A data source (add/fix ingest) | `ingest/index_ops.py` (the `COLLECTORS` registry) + that source's `ingest/<source>.py` | [Adding a New Source](#adding-a-new-source) |
| The read / query side | `ingest/semantic_index.py` (retrieval primitive) + `ingest/querier.py` (`ask()` orchestrator) | [Query Layer](#query-layer) |
| Focus 5 roster / ranking | `ingest/focus5_scan.py` | the `web.py` `/focus-5` route |
| Apple Reminders | `ingest/apple_reminders.py` (read) + `ingest/apple_reminders_write.py` (write, via signed helper) | — |
| "What to do next" | `ingest/next_actions.py` | [The Next Actions engine](#the-next-actions-engine-what-to-do-next) |
| Web dashboard surfaces | `web.py` + `web_components.py` | [Invocation Modes](#invocation-modes) |
| Config / secrets | `ingest/config.py` + `paths.py` | [Credentials](#credentials) |
| Scheduling / launchd jobs | [SCHEDULER.md](SCHEDULER.md) + `scripts/*_sync.sh` | [Invocation Modes](#invocation-modes) |
| The database itself (schema/migrations) | `ingest/db/` (connection, schema, migrations) | [Storage Layer](#storage-layer) |

### One request, end-to-end (worked trace)

A `rebalance refresh` (or the `refresh_index` MCP tool) flows through real symbols like this:

1. **`refresh_index()`** [`index_ops.py`] resolves the scope and iterates the `COLLECTORS` registry (each entry added via `register_collector(Collector(...))`).
2. Each collector's **`sync_*()`** runs fetch → normalize → upsert — e.g. `sync_apple_reminders()`, `github_scan()`, `sync_sleuth_reminders()`.
3. The collector opens storage via **`db_connection(path, ensure_<source>_schema)`** and upserts (e.g. `sync_apple_reminders()` → `upsert_apple_reminders()` → `db_connection()`).
4. **Derived stages** follow (`code`, `semantic`, `sync`): the unified semantic index is rebuilt by `backfill_semantic_documents()` and embedded.
5. **Read side:** `semantic_index.query()` (raw retrieval primitive; MCP `semantic_query`) and `querier.ask()` (broad synthesis orchestrator) read the *same* SQLite via `resolve_database_path()` → `db_connection()`.
6. **Surfaces:** the `web.py` routes (`/focus-5`, `/auth-log`, what's-next), the Typer CLI, and the MCP tools all read through that one persistence base.

---

## Signal Sources

Raw incoming sources have a priority, a collector module, and a target table. The table below is the canonical field spec; for per-effort execution detail see the [PROJECT/](PROJECT) docs, and for current status see [ROADMAP.md](ROADMAP.md).

| Priority | Source | Collector | Storage | Vectorized | Status |
|----------|--------|-----------|---------|------------|--------|
| P1 | GitHub | `github_scan.py` + `github_knowledge.py` + `github_readiness.py` + `github_reconciliation.py` | `github_activity`, `github_repo_meta`, `github_branches`, `github_items`, `github_comments`, `github_documents`, `github_embeddings` | Yes — structured repo signals plus semantic corpus for issues, PRs, comments, reviews, commit messages, and issue/PR reconciliation | Active |
| P1 | Obsidian Vault | `note_ingester.py` + `embedder.py` | `vault_files`, `chunks`, `keywords`, `links`, `embeddings` | **Yes** — Qwen3-Embedding-0.6B, 1024-dim, sqlite-vec | Active |
| P2 | Google Calendar | `calendar.py` | `calendar_events` table (default window 30d back / 7d forward; no auto-deletion) | No — structured event data | Active |
| P3 | Sleuth reminders (Slack) | `sleuth_reminders.py` | `sleuth_reminders` table | No — structured reminder rows | Active |
| P4 | Email (Gmail) | `gmail.py` + `semantic_index.py` | `email_messages` | Yes — subject + snippet participate in the unified semantic index | Active (Phase 1, shipped 2026-05-12): newest 100 `in:inbox` messages per run; metadata + snippet only, no body parsing yet |
| P4 | Figma comments | `figma.py` + `semantic_index.py` | `figma_comments` | Yes — registry-provider semantic docs for comments | Active (opt-in): requires a PAT plus explicit `figma_file_keys` allow-list |

### Other registered collector scopes

These are registered in `index_ops.py` and dispatch through the same `refresh_index()` orchestrator, but they are not raw upstream data sources:

| Scope | Kind | Purpose | Included in `all` |
|---|---|---|---|
| `code` | derived local scan | AST/code chunk collection into the unified semantic index | Yes |
| `semantic` | projection stage | Unified semantic backfill + embed maintenance | Yes |
| `sync` | export stage | Export calendar/email snapshots to the pulse sync repo | Yes |
| `focus5` | derived local scan | Build the device-local Focus 5 roster + signal cache | No |
| `ask_self` | derived local scan | Inventory ask_self indexes on this device | No |

### Source → Table fanout

```
EXTERNAL SOURCES                  INGESTORS (src/rebalance/ingest/)                  STORAGE
                                                                                     (SQLite @ $REBALANCE_DB
                                                                                      + sqlite-vec)

GitHub REST API ─────▶ github_scan.py            user events (last 30d)       ──▶ github_activity
  (api.github.com)   │                                                            github_repo_meta
                     ├▶ github_knowledge.py      per-repo artifacts:           ──▶ github_items (issues/PRs)
                     │                             issues, PRs, comments,          github_comments
                     │                             reviews, commits, checks,       github_commits
                     │                             branches, milestones,           github_check_runs
                     │                             releases                        github_branches
                     │                                                             github_milestones
                     │                                                             github_releases
                     │                                                             github_links
                     │                                                             github_documents
                     │                                                          ─ github_embeddings (vec0)
                     ├▶ github_readiness.py      release-state inference       ── (reads only)
                     └▶ github_reconciliation.py issue ↔ PR matching           ── (reads only)

Obsidian Vault ──────▶ note_ingester.py          walk *.md, chunk, TF-IDF,    ──▶ vault_files, chunks,
  (filesystem)       │                             wikilinks                       keywords, links
                     └▶ embedder.py              Qwen3-Embedding-0.6B         ──▶ embeddings (vec0, 1024-dim)
                                                   via mlx-embeddings

Google Calendar ─────▶ calendar.py               OAuth token (keyring+JSON),  ──▶ calendar_events
  (Calendar API)                                   30d back / 7d forward

Sleuth Web API ──────▶ sleuth_reminders.py       Bearer auth, stdlib urllib,  ──▶ sleuth_reminders
  (Vultr dev :2020)                                GET /workspace/<name>/
                                                   reminders?format=rebalance

Gmail API ───────────▶ gmail.py                  desktop OAuth (gmail.readonly), ──▶ email_messages
  (gmail.googleapis.com)                           filter in:inbox by default,
                                                   newest 100 messages/run

Gmail MCP connector ─▶ gmail.py                  agent-pushed message payloads ─▶ email_messages
  (opt-in push path)                               via ingest_email_messages()

Figma Comments API ───▶ figma.py                 file-key allow-list + PAT    ──▶ figma_comments
  (api.figma.com)                                                                        │
                                                                                         └─▶ semantic_documents
                                                                                             semantic_embeddings

Project Registry ────▶ registry.py +              MD registry → projects.yaml ──▶ project_registry
  (vault markdown)     preflight.py                → SQLite projection
```

### Invocation points

| Source | CLI | MCP tool(s) | Daily-sync step |
|---|---|---|---|
| GitHub activity | `rebalance github-scan` | `github_balance` | 3 |
| GitHub artifacts | `rebalance github-sync-artifacts`, `github-embed`, `github-query` | `semantic_query`, `github_release_readiness`, `github_close_candidates` | on demand |
| Obsidian vault | `rebalance ingest notes`, `ingest embed`, `query`, `search` | `semantic_query`, `search_vault` | 1 + 2 |
| Google Calendar | `rebalance calendar-sync`, `calendar-create-event`, `calendar-snap-edges`, `calendar-daily-report`, `calendar-weekly-report` | `create_calendar_event`, `review_timesheet`, `classify_event`, `snap_calendar_edges` | 4 |
| Sleuth reminders | `rebalance sleuth-sync` | `sleuth_sync_reminders` | 5 |
| Email (Gmail) | `rebalance refresh`, `semantic-backfill`, `semantic-query` | `refresh_index`, `semantic_query`, `ingest_gmail_messages` | 6 |
| Figma comments | `rebalance refresh` | `refresh_index` | opt-in |
| Focus 5 | `refresh_index(scope=["focus5"])`, `rebalance serve` / pulse server | web `/focus-5` route | opt-in |
| ask_self inventory | `refresh_index(scope=["ask_self"])` | `list_ask_self_repos` | opt-in |
| Project registry | `rebalance ingest preflight`, `ingest sync`, `onboard` | `list_projects`, `run_preflight`, `confirm_projects`, `onboarding_status` | on demand |

> Registry write discipline (Phase 5, `ingest/lifecycle.py`): discovery is
> read-only and stamps candidates with `provenance` (remote-activity /
> vault-note; local-scan reserved); `confirm_and_write` is the only curated
> write path; activity inference maintains only rows it created (marked
> `inference.generated_by`) and never touches curated rows; priority rules
> overlay at read time and are never persisted.

> Preferred write path: `refresh_index(scope=[...])` is the orchestrated entry
> point. Several source-specific CLI/MCP write commands still exist for
> historical/operator reasons, but some of them bypass the collector/orchestrator
> layer and call leaf ingest functions directly.

> **Sleuth production is read from a published file — no inbound access.** The
> Sleuth box pushes its reminders to a private git repo
> (`rebalance-git-pulse:sync/sleuth/reminders-<ws>.json`); rebalance-OS reads the
> local clone (`base_url` is a `file://`/local path). No SSH tunnel, no open port.
> See [SLEUTH_SYNC.md](SLEUTH_SYNC.md). (Dev still hits the API directly.)

### Source → Consumer fanout (report & synthesis surfaces)

The GH-150 contract: every surface that reads the activity signal — script entrypoint,
scheduled job, MCP tool — has a row here, so "is this new report needed, and what does
it read?" is answered in the diff instead of buried in a 400-line file.
`tests/test_consumer_catalog.py` enumerates entrypoints (`__main__` under `utils/` +
`scripts/`, minus the pdda tooling and the stood-down 3-Eyes tree), scheduled-job
scripts (the SCHEDULER.md policy table), and MCP tools (`@mcp.tool()` in
`src/rebalance/mcp/tools/`) and fails on any surface without a row
(`uncataloged consumer`). Column rules the test enforces: **LLM primitive** is `querier`,
`none`, or `own (R2-baseline: <path>)` — a private client may only exist by naming the
ratchet baseline that will shrink when it dies; **Input path** containing "own SQL"
must name its `R1-baseline:` file the same way; **Replaces** is `—` or an existing
Surface. When fe1's shared read layer lands, new rows must read `db/queries.py` and the
baseline references become violations.

| Surface | Entrypoint | Cadence | Input path | LLM primitive | Channel | Replaces |
|---|---|---|---|---|---|---|
| Daily full refresh | scripts/daily_sync.sh | daily 06:30 | orchestrator (`refresh_index`) | none | DB write | — |
| Hourly GitHub sync | scripts/github_sync.sh | hourly :45 | orchestrator (`refresh_index`, artifact window 7d) | none | DB write | — |
| Vault embeddings job | scripts/obsidian_vault_embeddings.sh | hourly :15 | orchestrator (`refresh_index` vault+semantic) | none | DB write | — |
| Pulse page | scripts/pulse_sync.sh | hourly :00 | pulse renderer (own SQL R1-baseline: src/rebalance/ingest/pulse.py) | none | pulse repo README | — |
| Pulse web render | scripts/pulse_web_sync.sh, scripts/pulse_web.py | 30 min | pulse renderer (same snapshot) | none | web/pulse.html | Pulse page |
| Pulse server | scripts/pulse_server.sh, scripts/pulse_server.py | daemon | DB read layer + pulse renderer | none | localhost:8767 | — |
| Pulse warning watch | scripts/pulse_warning_watch.py | 15 min | HTTP probe of pulse-server | none | temp JSONL | — |
| Daily work synthesis canary | scripts/daily_work_synthesis.sh, utils/daily_work_synthesis.py | 15 min, opt-in | existing CLIO/calendar/reminder read APIs + Daily repository/CPU scanners | own (R2-baseline: utils/daily_work_synthesis.py) | append-only temp Daily log + sanitized receipt JSONL | — |
| CLIO journey replay | src/rebalance/ingest/clio_journey.py (`rebalance clio-journey-replay`) | manual, opt-in | frozen CLIO export + bounded read-only GitHub snapshot (GH-230 exception) | none | new private replay directory | — |
| Health issue reporter | scripts/health_issue_reporter.py | hourly :10 + 3×/day triage | doctor subprocess + GitHub API | own (R2-baseline: scripts/health_issue_reporter.py) | GitHub issues | — |
| Daily note rollover | utils/obsidian_rollover.sh, utils/obsidian_daily_rollover.py | daily 00:40 | vault filesystem | none | Obsidian daily note | — |
| Progress digest | scripts/hiqs_digest.sh, utils/hiqs_digest.py | 2×/day 13:05/17:05 | own SQL (R1-baseline: utils/hiqs_digest.py) + doctor + semantic | querier | pulse repo digests/ → Slack relay | — |
| Daily synthesis | utils/daily_synthesis.sh, utils/daily_synthesis.py | daily 18:20 | pulse.collect_pulse_snapshot + git-pulse device files | querier | Obsidian note + CLIO log | — |
| Dashboard note | src/rebalance/ingest/note_builder.py | on refresh | own SQL (R1-baseline: src/rebalance/ingest/note_builder.py) + calendar | own (R2-baseline: src/rebalance/ingest/note_builder.py) | vault dashboard note | — |
| Claude Cloud signal grade | utils/claude_cloud_daily_grade.py | daily | ingest/claude_cloud sessions API | none | Obsidian block | — |
| Claude Cloud jobs POC | scripts/cc_cloud_jobs.py | manual | api.anthropic.com fetch (R2-baseline: scripts/cc_cloud_jobs.py) + gh | none | stdout + temp/ | Claude Cloud signal grade |
| Web dashboard data | scripts/dashboard.py | manual | own SQL (R1-baseline: scripts/dashboard.py) | none | dashboard payload | — |
| Chat eval | scripts/chat_eval.py | manual | eval corpus | none | stdout | — |
| Module audit | scripts/audit_modules.py | manual / MCP | repo tree + docs | none | audit report | — |
| Doc link check | scripts/check_doc_links.py | manual | repo docs | none | stdout | — |
| Extension build | scripts/build_extension.py | manual | capabilities tree | none | built artifacts | — |
| Capabilities index | scripts/generate_capabilities_index.py | manual | repo tree | none | capabilities index | — |
| Calendar OAuth setup | scripts/setup_calendar_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Gmail OAuth setup | scripts/setup_gmail_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Cloud daily grade helpers | utils/job_guard.py | per job | process guard | none | job lifecycle | — |
| Vector store reclaim | utils/gh250/reclaim.py | manual (historical) | vector store | none | store maintenance | — |
| Releases ledger CLI | utils/py/releases_app.py | manual | releases.db | none | ledger + dump | — |
| Releases cycle rollup | utils/py/releases_cycle.py | on demand | releases.db (read-only) | none | rollup markdown/dashboard | — |
| MCP: index_status | src/rebalance/mcp/tools/index.py | on demand | status snapshot (coverage probe) | none | MCP | — |
| MCP: refresh_index | src/rebalance/mcp/tools/index.py | on demand | orchestrator | none | MCP | — |
| MCP: diagnose_repo | src/rebalance/mcp/tools/index.py | on demand | own SQL (R1-baseline: src/rebalance/ingest/diagnose.py) | none | MCP | — |
| MCP: list_watched_repos | src/rebalance/mcp/tools/index.py | on demand | watched-set view | none | MCP | — |
| MCP: list_ask_self_repos | src/rebalance/mcp/tools/index.py | on demand | ask_self index | none | MCP | — |
| MCP: publish_pulse | src/rebalance/mcp/tools/index.py | on demand | pulse renderer | none | MCP | — |
| MCP: peek_source | src/rebalance/mcp/tools/index.py | on demand | parameterized table peek | none | MCP | — |
| MCP: get_next_actions | src/rebalance/mcp/tools/index.py | on demand | next_actions engine (R1-baseline: src/rebalance/ingest/next_actions.py) | querier | MCP | — |
| MCP: semantic_query | src/rebalance/mcp/tools/index.py | on demand | semantic index | none | MCP | — |
| MCP: audit_modules | src/rebalance/mcp/tools/hygiene.py | on demand | repo tree + docs | none | MCP | — |
| MCP: calendar tools | src/rebalance/mcp/tools/calendar.py | on demand | calendar_events | none | MCP | — |
| MCP: onboarding tools | src/rebalance/mcp/tools/onboarding.py | on demand | registry/lifecycle + gmail push | none | MCP | — |
| MCP: projects tools | src/rebalance/mcp/tools/projects.py | on demand | registry; github_balance → own SQL (R1-baseline: src/rebalance/ingest/github_scan.py) | none | MCP | — |
| MCP: retrieval tools | src/rebalance/mcp/tools/retrieval.py | on demand | vault FTS; readiness → own SQL (R1-baseline: src/rebalance/ingest/github_readiness.py) | querier | MCP | — |
| MCP: sleuth tools | src/rebalance/mcp/tools/sleuth.py | on demand | sleuth source | none | MCP | — |

Grouped rows (one row covering several same-shape tools, e.g. "MCP: calendar tools")
name their module; the test resolves them. Two surfaced read paths have no entrypoint
of their own and are carried by the rows above: `pulse.collect_pulse_snapshot`
(daily synthesis) and the querier synthesis primitive itself.

### Credentials

| Source | Secret store | Mechanism |
|---|---|---|
| GitHub | OS keyring + out-of-repo secret store (`~/.config/rebalance-os/secrets`, `0600`) fallback; `gh` CLI as last-resort read fallback | PAT: classic `repo` scope, or fine-grained with All-repos read-only Contents/Metadata (public-only tokens hide private work); persisted to keyring + secret store for launchd reachability — no longer written to `temp/rbos.config` |
| Google Calendar | `google-calendar.env` (client credentials) via `resolve_secret_path()` + OAuth user-token in keyring with a JSON fallback at `~/.config/rebalance-os/secrets/google-calendar-oauth` (a legacy pickle migrates to JSON on read) | OAuth 2.0 user consent |
| Sleuth | OS keyring + secret store (`~/.config/rebalance-os/secrets/sleuth_web_api`); legacy `*.env` files still read for un-migrated devices | Bearer token, 64-hex |
| Gmail | Desktop OAuth token in keyring + JSON fallback at `~/.config/rebalance-os/secrets/google-gmail-oauth`, or MCP push-ingest mode | `gmail.readonly` desktop OAuth, or agent-pushed `ingest_gmail_messages` path when `gmail_ingest_method=mcp` |
| Figma | OS keyring + secret store for the PAT; `temp/rbos.config` holds only the (non-secret) file-key allow-list | Personal access token + explicit file selection |
| Obsidian vault | none | filesystem read only |

Env-file paths resolve via [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_secret_path(name)` — the layered chain is `REBALANCE_SECRETS_DIR` env var → `secrets_dir` field in `~/.config/rebalance-os/config.json` (set via `rebalance config set-secrets-dir`) → `~/secrets/` legacy default. The domain CLI loaders (for example, [src/rebalance/cli/calendar.py](src/rebalance/cli/calendar.py) and [src/rebalance/cli/sleuth.py](src/rebalance/cli/sleuth.py)) use this resolver, so the repo is portable across operator home directories without hardcoded env-file paths. Env files should sit at mode 600. Env files are parsed manually (no `python-dotenv`). Nothing with a secret value is committed.

### Adding a New Source

> **The current preferred way to add a source is the collector / `SourceModule`
> contract — see [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py)
> and the developer guide [PLUGINS.md](PLUGINS.md).** It covers the registry
> descriptor, the optional `semantic_docs` provider, secrets/keyring, numbered
> migrations, and tests, with Figma as the worked example. The steps below are
> the practical recipe for the built-in sources.

1. **Collector** — write `src/rebalance/ingest/<source>.py` following the `sleuth_reminders.py` or `github_scan.py` shape: a dataclass for one record, a `sync_*()` function that fetches → normalizes → upserts, and a module-local `ensure_<source>_schema(conn)`. Use `db_connection(path, ensure_fn)` from the `ingest/db/` package.
2. **Schema** — keep the `CREATE TABLE` inside `ensure_<source>_schema`. Only promote to the shared `ingest/db/` package if more than one module needs it. Use existing tables for unstructured text that should be embedded.
3. **Registry** — register the source in `index_ops.py` with `register_collector(Collector(...))`. Add `requires=...`, `semantic_docs=...`, and/or `candidates=...` metadata if the source needs preconditions, participates in the unified semantic index, or contributes next-action candidates to the HiQS ranking. The `candidates=` provider is how a source reaches the ranked "what to do next" verdict — no edit to the ranker's dispatch.
4. **Credentials** — if the source uses env-style secret files, resolve them through `resolve_secret_path()` and a small domain loader (see `cli/calendar.py` / `cli/sleuth.py`). Never hardcode secrets in repo files.
5. **Next-action candidates** — to feed the HiQS ranking, supply a `candidates=` provider on the `Collector` (a function `bundle → list[candidate dict]`, each Attested with `source`/`evidence`/`why`). `_operator_candidates()` walks the registry, so no ranker edit is needed. A source participates in `ask()` automatically once it is in the ranked bundle — `ask()` reads the whole ranking via `_gather_hiqs_context()`.
6. **Prompt section** — the HiQS section in `_build_prompt()` already renders every ranked source; add a bespoke `_build_prompt()` block only for context that is NOT a ranked next-action.
7. **CLI + MCP** — add thin wrappers in `src/rebalance/cli/*` and `src/rebalance/mcp/tools/*` if the source needs direct user-facing operations beyond `refresh_index()`.
8. **Scheduled refresh** — ensure `included_in_all` and any explicit scheduler usage match the source's intended unattended behavior.
9. **Tests** — add `tests/test_<source>.py` that stubs the outbound call (patch `urlopen` for HTTP, filesystem for local sources). Verify insert / unchanged / update semantics.

No changes needed to the query layer, LLM synthesis, or MCP transport.

---

## Storage Layer

Single SQLite file resolved by `src/rebalance/paths.py::resolve_database_path()`. Default canonical location is `~/Library/Application Support/rebalance-os/rebalance.db` on macOS (or `$XDG_DATA_HOME/rebalance-os/rebalance.db` on Linux); `REBALANCE_DB` env var, an `--database` flag, or a user-config override all win against the canonical path when set. sqlite-vec extension loaded for vector operations.

### Write discipline (one writer per table)

The single most important invariant for a new maintainer to preserve:

- **Reads are unrestricted.** Anything may open `db_connection()` and `SELECT`. The "Tables by Domain" list below names the *writer* for each table — that ownership is about **writes**, not reads.
- **One writer per table.** Each table is written by exactly one module (e.g. `github_activity` ← `github_scan.py`, `sleuth_reminders` ← `sleuth_reminders.py`, `semantic_documents` ← the `semantic` stage only). Do not add a second writer; extend the owning collector instead.
- **Writes go through the orchestrator.** New ingestion/refresh writes register as a `Collector` in `index_ops.py` and run under `refresh_index()` — not as a fresh leaf that opens `db_connection()` and upserts on its own.
- **Known, accepted exceptions (direct `db_connection()` writers outside `refresh_index`).** A few interactive/operator commands write directly *by design* — they are human-in-the-loop mutations, not unattended ingest: `rebalance github-sync-artifacts` (`cli/github.py::github_sync_artifacts()`) and the `rebalance apple-reminders` write path (`cli/apple_reminders.py`). Most other direct `db_connection()` calls from `cli/*` (`onboard`, `config-doctor`, `raw`, `dashboard-render`) are **reads**, which are fine. If you add a new direct *writer*, document it here and say why it can't go through the registry.

### Tables by Domain

```
Project Registry (writer: registry.py::sync_db(), the single low-level upsert)
  project_registry          — canonical project metadata. Rows are either curated
                               (write_semantics="confirmation_gated", written only
                               via the onboarding confirm_projects()/confirm_and_write()
                               path — see lifecycle.py) or machine_owned (never
                               clobbers a curated row of the same name). Two
                               machine_owned producers currently call sync_db():
                               project_inference.py's activity/calendar inference
                               (generated_by "activity_inference_v1") and GH-124's
                               commit-threshold auto-promotion (generated_by
                               "commit_threshold_v1", wired into _refresh_github()
                               in index_ops.py, immediately after the watchlist
                               guard). _is_inference_owned() recognizes both markers.

GitHub activity (writer: github_scan.py)
  github_activity            — per-repo event counts, keyed by (login, repo, scan_date)

GitHub artifacts (writer: github_knowledge.py; schema in `ingest/db/`)
  github_repo_meta           — repo-level metadata (default branch, issue/project support)
  github_branches            — local branch inventory for promotion/release inference
  github_labels              — label dictionary per repo
  github_milestones          — open/closed milestones with due dates
  github_releases            — published tags/releases
  github_items               — issues and PRs (unified table, item_type discriminates)
  github_comments            — issue/PR/review comments
  github_commits             — PR commit history
  github_check_runs          — CI check results per head_sha
  github_links               — explicit and inferred issue↔PR cross-references
  github_documents           — per-artifact embeddable document rows
  github_embeddings          — sqlite-vec virtual table for artifact embeddings
  github_embedding_meta      — model name + dim for the GitHub corpus

Unified Semantic Index (single writer: the `semantic` collector stage in index_ops.py)
  semantic_documents         — canonical cross-source document rows (vault chunks +
                               GitHub issues/PRs/comments/commits, Gmail
                               messages, and registry-provider sources such as
                               Figma comments). Written exclusively by
                               _refresh_semantic_only() via
                               semantic_index.py::backfill_semantic_documents().
                               Consumed by semantic_query() and the LLM context layer.
  semantic_embeddings        — sqlite-vec virtual table, float[1024], keyed by
                               semantic_documents.id. Unified ANN search target.
  semantic_embedding_meta    — model name, dimension, embedder_version, last_embed_at

Vault Ingestion (writer: note_ingester.py)
  vault_files                — one row per .md file, with content_hash for delta detection
  chunks                     — heading-based chunks, FK to vault_files (CASCADE delete)
  keywords                   — TF-IDF top-K per chunk, FK to chunks (CASCADE delete)
  links                      — wikilinks and embeds, FK to vault_files (CASCADE delete)

Embeddings (writer: embedder.py)
  embeddings                 — sqlite-vec virtual table, float[1024], keyed by chunk_id
  embedding_meta             — model name, dimension, last embed timestamp

Email (writer: gmail.py)
  email_messages             — message metadata + snippet, keyed by Gmail message_id.
                               Upsert-only rolling window (newest matching messages);
                               also projected into semantic_documents.

Google Calendar (writer: calendar.py)
  calendar_events            — event id, summary, start/end, location, attendees, description
                               Keyed by Google event ID (INSERT OR REPLACE). Default sync window
                               is 30 days back + 7 days forward (365-day backfill available via
                               the CLI). No automatic deletion; manual cleanup if pruning is needed.

Sleuth reminders (writer: sleuth_reminders.py)
  sleuth_reminders           — one row per Slack reminder, keyed by reminder_id (TEXT PK).
                               Upsert with diff-based insert/update/unchanged counts;
                               first_seen_at preserved across syncs. Rows are never
                               deleted — state transitions (scheduled → posted → completed)
                               are mirrored as UPDATEs.

Figma (writer: figma.py)
  figma_comments             — comment rows keyed by Figma comment key, synced from
                               an explicit file-key allow-list. Also projected into
                               semantic_documents via the registry-provider path.

Device-local inventories / derived jobs
  ask_self_indexes           — per-device inventory of ask_self indexes found on disk
  focus5_repo_signals        — cached per-repo Focus 5 signals for the current device
  focus5_roster              — persisted top-5 Focus 5 roster snapshot
```

### Sync semantics per source

Every source is incremental, but the meaning of "incremental" depends on what the upstream API supports. The three patterns from [Sync model](#sync-model-in-plain-english) map cleanly onto the table below:

- **Vault notes** — *hash delta.* SHA-256 of raw file bytes stored in `vault_files.content_hash`. On re-ingest, unchanged-content files have their `last_modified` refreshed if the on-disk mtime moved forward (a "touch") but skip all parsing and embedding work — surfaced as `touched_files` in the ingest result. Changed-content files are deleted (CASCADE clears chunks/keywords/links) and re-inserted.
- **GitHub activity** — *window refetch.* Keyed by `(login, repo_full_name, scan_date)` with `ON CONFLICT REPLACE`. Each scan re-pulls the user's last ~30 days of events and overwrites *today's* row only; older days are left alone.
- **GitHub artifacts** — *hash/ID delta with window.* Keyed by `(repo_full_name, item_type, number)` for items; comments/commits/checks keyed by GitHub ID. `ON CONFLICT REPLACE` on every sync, with a `since_days` lookback to skip artifacts that haven't been touched in that window.
- **Embeddings** — *hash delta.* Chunks (vault) or documents (GitHub corpus) without a corresponding embeddings row get embedded. A model-version change recorded in `embedding_meta` / `github_embedding_meta` triggers a full re-embed of that corpus.
- **Calendar** — *window refetch.* Keyed by Google event ID with `INSERT OR REPLACE`. Re-sync overwrites existing events and adds new ones within the requested window (default 30d back / 7d forward; 365d on demand for backfill). No auto-deletion — events removed upstream stay in the local DB until manually pruned.
- **Sleuth reminders** — *full refetch + column-diff.* Keyed by `reminder_id`. Column-level diff against the stored row decides insert/update/unchanged; `first_seen_at` is set on insert and never overwritten; `last_seen_at` and `last_synced_at` refresh on every sync. Missing reminders are NOT deleted — terminal states (`completed`, `canceled`) remain as history.
- **Email (Gmail)** — *window refetch, count-bounded.* Keyed by Gmail `message_id` with upsert. Each run pulls the newest 100 messages matching the configured filter (default `in:inbox`, override via `gmail_query_filter` in `temp/rbos.config`). Phase 1 stores metadata + Gmail snippet only — no full body, no historical backfill, no auto-delete. See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).

---

## Query Layer

All consumers read from the same SQLite file. The query layer is source-agnostic.

**Read-side ownership model (Phase 3, Option C):**

| Surface | Role | Owner |
|---|---|---|
| `semantic_query()` MCP tool | Unified raw retrieval primitive | `semantic_index.query()` — owns source vocabulary, freshness, hybrid RRF |
| `chat_with_data()` | Citations-first interactive retrieval | `chat.py` — owns scope aliases (`work`/`code`/`all`), citation shaping; delegates retrieval to `semantic_index` |
| `ask()` | Broad mixed-context synthesis/orchestration | `querier.py` — owns project/calendar/temporal framing; not the canonical retrieval primitive |

```
SQLite @ $REBALANCE_DB
   │
   ├──▶ semantic_index.query()     ── unified raw retrieval primitive
   │    (MCP: semantic_query)          source vocab + hybrid RRF
   │         │
   │         ├──▶ chat_with_data() ── citations-first presentation layer
   │         │    (dashboard /api/chat)  scope aliases, citation shaping
   │         │
   │         └──▶ ask() (partial)  ── contributes to synthesis context
   │
   ├──▶ querier.py::ask()          ── broad orchestrator: gathers project,
   │    (MCP: ask, CLI: ask)           calendar, temporal + semantic signals;
   │                                   synthesizes via local Qwen3 (optional)
   │
   ├──▶ daily_report.py /          ── per-day / per-week calendar rollups
   │    weekly_report.py              with project classification
   │
   ├──▶ github_scan.py             ── per-project commit/PR/issue counts
   │    ::get_github_balance()        (surfaced as the github_balance MCP tool)
   │
   ├──▶ github_readiness.py /      ── release-state inference + issue↔PR
   │    github_reconciliation.py       close candidates
   │
   └──▶ mcp/server.py              ── exposes all of the above as MCP tools
                                       to Claude Code, Claude Desktop, etc.
```

`querier.py` is the synthesis orchestrator (not the retrieval primitive). A single `ask()` call:

1. **Gathers context** from all sources in parallel-ready functions:
   - `_gather_project_context()` — registry entries + repos map
   - `_gather_github_context()` — per-project activity summary (from `github_activity`)
   - `_gather_github_semantic_context()` — semantic recall over the GitHub corpus (`github_documents` + `github_embeddings`)
   - `_gather_vault_context()` — semantic search (embed query → ANN)
   - `_gather_vault_activity()` — recently modified files
   - `_gather_calendar_context()` — upcoming + recent events from `calendar_events`
   - `_gather_temporal_context()` — day-of-week / weekend / holiday framing for the prompt
   - `_gather_hiqs_context()` — the persisted **HiQS** ranked verdict (see below). A cheap
     cached read (`load_ranked_next_actions()`); it never recomputes. This is how Sleuth,
     Gmail, and Figma reach `ask()`: they are already in the one ranked bundle, so `ask()`
     surfaces them via the shared ranking rather than a per-source gatherer.

2. **Assembles a prompt** with all context formatted into labeled sections — including a
   `## HiQS — ranked next actions` section carrying each action's receipts. The ranking is
   also returned first-class on `QueryResult.hiqs`.

3. **Synthesizes** via local Qwen3 LLM (mlx-lm). Returns both synthesis and raw context.

### The Next Actions engine ("what to do next")

A distinct read-side subsystem in [src/rebalance/ingest/next_actions.py](src/rebalance/ingest/next_actions.py) — structurally one of the larger clusters in the codebase. It is **HiQS**: the single, unified work-signal pipeline — **one bundle spanning all six sources (GitHub, vault, Calendar, Sleuth/Slack, Gmail, Figma), one ranked verdict, read by every surface**. `ask()` and the dashboard's what's-next view read the *same* persisted ranking, so they cannot drift. It also drives the fixed vault file `Dashboards/What To Do Next.md`.

Pipeline (real symbols):

1. **`assemble_day_bundle()`** gathers the operator's own day signal across all six sources into an `OperatorBundle`, plus teammate deltas (`_gather_teammate_delta()`). Candidates are built by **`_operator_candidates()`, which WALKS the collector registry** — each source owns its candidate shape via the `candidates=` provider on its `Collector` (the same registry seam as `semantic_docs=`). A new work signal reaches the ranked verdict by registering a collector, never by editing this dispatch (GUIDING-PRINCIPLES Principle 3).
2. **`build_rank_prompt()`** formats the candidates; **`rank_next_actions()`** synthesizes the ranking. **Primary path = Gemini** (`get_gemini_api_key()` → `gemini-2.5-flash`); a deterministic local fallback (Qwen) keeps it working offline. `_parse_ranked_synthesis()` rejects placeholder echoes.
3. Output is a **`RankedNextActions`** (list of `RankedAction`), **persisted** to a cache table via `persist_ranked_next_actions()` and read back by `load_ranked_next_actions()`.
4. **`render_next_actions_markdown()`** writes the ranked list to the fixed vault file (single-writer, generated).
5. **Consumers:** the `web.py` what's-next route (`whatsnext_page()`) is the single WRITER (its `?refresh` path ranks + persists); `ask()` is a READER that exposes the persisted ranking as the first-class `QueryResult.hiqs` field. Neither re-ranks inline, so the two surfaces are structurally incapable of drifting.

### Two-Layer LLM Architecture

```
User question
  │
  ▼
ask() tool ──▶ Local Qwen3-0.6B (Layer 1)
  │              - Sees all raw context
  │              - Fast first-pass synthesis
  │              - Runs on-device via MLX
  │
  ▼
Returns to host agent (Layer 2)
  │              - Claude, Copilot, Gemini, etc.
  │              - Reviews synthesis + raw context
  │              - Fact-checks against raw data
  │              - Adapts, refines, presents to user
  │
  ▼
User sees final answer
```

**Why two layers?** The local model is fast and private — it never sends vault content to the cloud. But it's small (0.6B) and makes mistakes. The host agent is larger, smarter, and can fact-check against the raw context that's returned alongside the synthesis. The user gets speed + accuracy + privacy.

**`skip_synthesis=True`** bypasses Layer 1 entirely and returns raw context only. Use this when the host agent is capable enough to do its own synthesis (e.g., Claude).

---

## Invocation Modes

Four ways the pipeline runs:

1. **Interactive CLI** — `rebalance <subcommand>` via the Typer package under `src/rebalance/cli/`. Ad-hoc and one-shot workflows (`calendar-create-event`, `github-release-readiness`, `sleuth-sync --json`, `profile-sync`, `raw`, etc.). `rebalance` invoked with no arguments launches the live dashboard (mode 4). `rebalance raw [--minutes N] [--watch S] [--json]` is a calibration probe: 1 GitHub API request per invocation, classifies recent events as captured / pending / unwatched against the local pipeline state, used to verify that commits/PRs/issues are making it into rebalanceOS.

2. **Unattended scheduled syncs** — a launchd fleet of ten jobs. [SCHEDULER.md](SCHEDULER.md) is the policy table (single source of truth for labels, cadences, scopes, prerequisites, and outputs; enforced by `tests/test_scheduler_policy.py`). The six data/render jobs, conceptually:

   - **Daily all-scope sync** ([scripts/daily_sync.sh](scripts/daily_sync.sh) / [scripts/com.rebalance-os.daily-sync.plist.template](scripts/com.rebalance-os.daily-sync.plist.template)) at 06:30 local time, plus on boot/login if 06:30 was missed. Calls `refresh_index()` with no scope (the **default recipe**): all raw sources (`vault`, `github`, `calendar`, `sleuth`, `email`) followed by the derived/projection/export stages (`code`, `semantic`, `sync`). Note: `scope=["all"]` is *not* the same as the default recipe — after Phase 1b, `all` expands to raw sources only; the default no-scope path runs the full recipe including follow-on stages. Opt-in scopes (`figma`, `focus5`, `ask_self`) are never included automatically. Per-scope failures are captured in `errors` rather than aborting the run.
   - **Hourly obsidian vault embeddings refresh** ([scripts/obsidian_vault_embeddings.sh](scripts/obsidian_vault_embeddings.sh) / [scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template](scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template)) at HH:15 from 06:15 to 23:15. Calls `refresh_index(scope=["vault", "semantic"])` — keeps notes edited mid-day visible in **both** the dashboard/pulse (vault ingest) and **semantic search** (semantic projection stage). Vault ingest with no changes is ~0.02s; the lightweight BGE-Small (384-dim, ~20MB) semantic stage embeds rows where content changed in milliseconds.
   - **Hourly pulse publish** ([scripts/pulse_sync.sh](scripts/pulse_sync.sh) / [scripts/com.rebalance-os.pulse-sync.plist.template](scripts/com.rebalance-os.pulse-sync.plist.template)) on the hour, 06:00 to 23:00. Renders the operator pulse markdown and pushes it to the configured private repo, but only when the rendered content actually changed since the previous run.
   - **30-minute pulse-web refresh** ([scripts/pulse_web_sync.sh](scripts/pulse_web_sync.sh) / [scripts/com.rebalance-os.pulse-web-sync.plist.template](scripts/com.rebalance-os.pulse-web-sync.plist.template)) every 30 minutes from 06:00 to 23:30. Calls [scripts/pulse_web.py](scripts/pulse_web.py) to regenerate the local `web/pulse.html` mirror of the dashboard. Atomic via tmp+replace (a crashed run leaves the previous HTML intact). No network, no git push — separate from the markdown→private-repo flow above.
   - **Hourly GitHub sync** ([scripts/github_sync.sh](scripts/github_sync.sh) / [scripts/com.rebalance-os.github-sync.plist.template](scripts/com.rebalance-os.github-sync.plist.template)) — a narrower github-only refresh independent of the daily full sync, for environments that want fresher GitHub data without paying the full multi-source cost.
   - **Pulse server (long-running, not scheduled)** ([scripts/pulse_server.sh](scripts/pulse_server.sh) / [scripts/com.rebalance-os.pulse-server.plist.template](scripts/com.rebalance-os.pulse-server.plist.template)) — a FastAPI/uvicorn server on `127.0.0.1:8767` with `RunAtLoad` + `KeepAlive` (autostart at login, restart on crash, `ThrottleInterval=30s`). Adds an interactive layer (real Refresh button + filter) on top of the static `web/pulse.html` the pulse-web job regenerates, **and is the always-on JSON backend for the macOS Focus 5 Float app** ([macOS/Apps/Focus5Float](macOS/Apps/Focus5Float)) — it serves `/focus-5.json` (roster), `/focus-5/goals`, and `/focus-5/note` so the app works without a separate `rebalance serve` on `:8787`. Loopback bind is enforced in [scripts/pulse_server.py](scripts/pulse_server.py). Unlike the five scheduled jobs above, it runs continuously rather than firing on a calendar interval.

     **Drift gotcha (has bitten the Focus 5 app twice):** [scripts/pulse_server.py](scripts/pulse_server.py) does *not* mount `rebalance.web`'s app — it hand-re-declares a chosen *subset* of its routes by importing the renderers. Two consequences: (1) a route added to `web.py` is invisible on `:8767` until a matching wrapper is added to `pulse_server.py` (this is how `/focus-5.json` was missed); (2) because it's a `KeepAlive` daemon, any route change requires `launchctl kickstart -k gui/$UID/com.rebalance-os.pulse-server` to take effect — a long-running process keeps serving its old route table otherwise (this is how a freshly-added `/focus-5/goals` still 404'd).

   The remaining four jobs (health-check hourly, health-check-triage 3×/day, pulse-warning-watch every 15 min, obsidian-rollover at midnight) plus **daily-synthesis** at 18:20 are operational/maintenance agents — see [SCHEDULER.md](SCHEDULER.md). The **daily-synthesis** job ([utils/daily_synthesis.sh](utils/daily_synthesis.sh) / [scripts/com.rebalance-os.daily-synthesis.plist.template](scripts/com.rebalance-os.daily-synthesis.plist.template), GH-74) does two syntheses in one process, in order: first a Gemini daily-activity summary from the structured `collect_pulse_snapshot()` output, then a Gemini synthesis of multi-device git commit logs aggregated via `experimental/git-pulse/view.sh --today`. Each lands in its own idempotent sentinel-bracketed block at the bottom of the vault's `0. Today's Notes.md`, pulse block first. (It replaces two formerly separate jobs, obsidian-daily-sync at 18:20 and git-pulse-daily-synthesis at 18:30, which existed as two launchd jobs only so the second could fire after the first — see `utils/daily_synthesis.py`'s module docstring.) Both syntheses use Gemini-or-skip logic (no Qwen fallback) and the merged job carries one late-run guard to prevent colliding with the 00:00 rollover.

   Wrapper scripts source [scripts/lib/scheduler_common.sh](scripts/lib/scheduler_common.sh) for env bootstrap (repo root, venv python, `PYTHONPATH`), per-day logs under `temp/logs/`, job-lifecycle events into `auth_activity.jsonl`, and log retention. Installers source [scripts/lib/install_common.sh](scripts/lib/install_common.sh) for one normalized flow: always-unload, render the `.plist.template` (`{{REBALANCE_DIR}}`, `{{PYTHON}}`, `{{HOME}}`), `plutil -lint`, load, poll-verify registration. The rendered plists in `~/Library/LaunchAgents/` are gitignored — the templates are the only checked-in form, so a clone on any machine installs cleanly with no per-user editing.

3. **MCP tool handlers** — [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py) registers the tools; [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) remains as the backward-compatibility shim for older launch commands. Host agents (Claude Code / Claude Desktop) call these on demand. `REBALANCE_DB` env var resolves the shared DB path.

4. **Live dashboard** — [scripts/dashboard.py](scripts/dashboard.py) is a Rich Live monitor that polls the local SQLite every 2 seconds (cheap; no network) and runs `refresh_index(scope=["github"])` in a background thread every 10 minutes so the underlying data actually changes. Launch via `rebalance` (no args) or `rebalance dashboard`. Press `r` to trigger an immediate GitHub refresh, `q` (or Ctrl+C) to quit. Theming and cadence are env-var controlled (`PULSE_INVERSE`, `PULSE_TICK`, `PULSE_AUTO_MIN`, `REBALANCE_TZ`). The dashboard is intentionally read-only against the same DB the MCP server and the launchd jobs write to.

---

## MCP Tool Surface

Tools are registered in [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py)::`create_server()`. [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) is a backward-compatibility shim so older launch commands still work. All tools share the same `database_path` resolved at server startup from `REBALANCE_DB`.

| Category | Tool | Purpose |
|----------|------|---------|
| Query | `ask` | Natural language query across all sources (with optional local LLM synthesis) |
| Query | `search_vault` | Vault keyword search (TF-IDF) |
| Query | `github_balance` | Per-project GitHub activity summary |
| Query | `github_release_readiness` | Infer milestone/release readiness from the local GitHub corpus |
| Query | `github_close_candidates` | Suggest open issues that likely map to merged PRs |
| Query | `semantic_query` | Unified vector search across indexed sources (single ranked result set; filter with `sources`) |
| Diagnostics | `index_status` | Snapshot of every source + semantic index freshness (read-only) |
| Diagnostics | `refresh_index` | Orchestrated refresh of the local knowledge base (single entry point) |
| Diagnostics | `list_watched_repos` | Show merged set of repos being monitored (project registry ∪ activity − ignored) |
| Diagnostics | `diagnose_repo` | Walk the watched-repos + sync funnel for a single repo (optionally a `sha` or `pr`) and explain coverage + freshness gaps; opt-in `live=True` distinguishes "we never synced" from "PAT can't see it" |
| Registry | `list_projects` | Query project registry |
| Onboarding | `onboarding_status` | Check setup completion |
| Onboarding | `setup_github_token` | Validate and store GitHub PAT |
| Onboarding | `run_preflight` | Discover project candidates (read-only) |
| Onboarding | `confirm_projects` | Write registry and sync |
| Onboarding | `ingest_gmail_messages` | Agent-pushed Gmail ingest path for installs using `gmail_ingest_method=mcp` |
| Calendar | `create_calendar_event` | Create a Google Calendar event via local OAuth |
| Calendar | `review_timesheet` | Surface unclassified calendar events that need a project decision |
| Calendar | `classify_event` | Persist an include/exclude/project classification for an event |
| Calendar | `snap_calendar_edges` | Detect and (optionally) fix slightly overlapping events |
| Sync | `sleuth_sync_reminders` | Pull Slack reminders from the Sleuth Web API and upsert to SQLite |
| Sync | `publish_pulse` | Render today+yesterday activity to markdown and push to private pulse repo |
| Hygiene | `audit_modules` | Run [scripts/audit_modules.py](scripts/audit_modules.py) and return the structured JSON result. Verifies that ingest collectors / render modules / scheduled-job infrastructure are documented in ARCHITECTURE.md and CHANGELOG.md, and that recent commits' file changes appear in the latest CHANGELOG version section. Supports `init=True` to snapshot the baseline lockfile and `include_uncommitted=True` for a pre-commit working-tree preview |

Tool specs (params, returns, dependencies): see [MCP.md](MCP.md).

---

## Module Map

```
src/rebalance/
  __init__.py              — package version
  __main__.py              — CLI entry point
  cli/                     — Typer command package split by domain
  mcp/                     — FastMCP server + tool modules
  mcp_server.py            — backward-compatibility shim to rebalance.mcp.server
  paths.py                 — centralized path resolver. `resolve_database_path()` and
                              `resolve_secret_path()` walk a layered chain (explicit
                              flag → env var → canonical app-data path → user
                              config → cwd walk-up for project marker). Single
                              source of truth for "where is the DB / secrets dir?"
                              `resolve_project_root(Path(__file__))` (walk-up) is the
                              stable repo-root resolver used throughout the codebase —
                              replaces all `parents[N]` hacks. `resolve_oauth_token_path(service)`
                              returns the canonical launchd-reachable token path for
                              Google OAuth services. Configure user defaults via
                              `rebalance config set-default-database` and `set-secrets-dir`.
  web.py                   — FastAPI local dashboard/web surfaces (`/`, `/focus-5`, `/auth-log`, etc.)
  ingest/health_log.py     — doctor check TRANSITIONS into the unified system log (GH-101)
  doctor.py                — installation health checks; backs `rebalance doctor`
  ingest/
    config.py              — secrets storage (temp/rbos.config)
    registry.py            — project registry sync (Markdown ↔ YAML ↔ SQLite);
                              read_registry (pure read) vs load_registry (write-path)
    preflight.py           — onboarding discovery (read-only, provenance-stamped)
                              + confirmation — the only curated registry write path
    lifecycle.py           — Phase 5/6 lifecycle contract: setup stage map with
                              done/now/next/blocked/skipped statuses, executor
                              hints, and remediation (backs onboarding_status and
                              the /welcome skill), plus the project-lifecycle
                              ownership table (write semantics per stage —
                              discovery read_only, confirmation gated, inference
                              machine-owned, prioritization read-time overlay)
    local_repos.py         — local checkout discovery (Phase 6.1): scan
                              local_repo_roots for git checkouts, GitHub identity
                              from origin, unpushed-commit counts; feeds
                              provenance=local-scan candidates + the doctor's
                              unpushed-work check
    github_scan.py         — GitHub Events API collector + per-project balance query
    github_knowledge.py    — per-repo artifact sync (issues/PRs/comments/commits/checks) + embedding
    github_watch.py        — watched/external repo reconciliation and repo-watch logic
    github_readiness.py    — release-readiness inference over the local GitHub corpus (read-only)
    github_reconciliation.py — issue ↔ PR close-candidate inference (read-only)
    db/                    — shared DB connection, schema, migrations, sqlite-vec loading
    md_parser.py           — pure markdown parsing (frontmatter, wikilinks, tags, chunking)
    note_ingester.py       — vault walker, delta detection, TF-IDF keywords
    embedder.py            — mlx-embeddings batch embed + ANN query
    semantic_index.py      — unified semantic index: backfill, embed, and query across
                              vault + GitHub + email, plus registry-provider sources
                              such as Figma (semantic_documents / semantic_embeddings)
    index_ops.py           — single entry point for refresh_index() and index_status();
                              orchestrates the full ingest pipeline so agents don't
                              need to know individual CLI command ordering
    calendar.py            — Google Calendar API collector + SQLite persistence
    calendar_config.py     — OAuth token storage, classification rules, review-decision persistence
    calendar_helpers.py    — duration/math utilities consumed by calendar tools
    calendar_snap.py       — edge-snapping logic for slightly overlapping calendar events
    sleuth_reminders.py    — Sleuth Web API collector (Bearer auth, urllib) + upsert
    gmail.py               — Gmail collector / MCP push-ingest write path into email_messages
    figma.py               — Figma comments collector + registry-provider semantic_docs
    ask_self_scan.py       — device-local ask_self index inventory collector
    focus5_scan.py         — Focus 5 repo-signal scan + roster builder
    slack_users.py         — Slack user-id → friendly-name lookup, file-mtime cached;
                              feeds the dashboard sleuth panel and the pulse markdown
    diagnose.py            — repo-level diagnostic that walks the watched-repos +
                              sync funnel for one repo (optionally sha/PR) — backs
                              the diagnose_repo MCP tool
    profile_sync.py        — daily-sync log parser that surfaces per-repo GitHub
                              timings; backs the rebalance profile-sync subcommand
    pulse.py               — pulse markdown renderer; backs publish_pulse MCP tool
    agent_tags.py          — source-tagging for pulse rows (claude-cloud, codex-cloud,
                              lovable, local-vscode, human)
    project_classifier.py  — calendar event → project matcher for timesheet reports
    project_inference.py   — project inference from note titles / calendar summaries
    note_builder.py        — dashboard markdown renderer / write-back for the vault note
    audit.py               — structured audit logging (append_audit_entry)
    querier.py             — multi-source context gathering + local LLM synthesis

scripts/                   — Operator entry points (not part of the importable package)
  dashboard.py             — Rich Live terminal dashboard (mode 4 above)
  pulse_web.py             — render module: regenerates web/pulse.html (the local
                              browser mirror of the dashboard) from the same SQLite
                              knowledge base; atomic via tmp+replace; supports --watch
  _bootstrap.py            — single sys.path shim for directly-run scripts (src/ + scripts/)
  lib/scheduler_common.sh  — shared launchd job runtime: env bootstrap, dated logs,
                              job-lifecycle events, retention (sourced by *_sync.sh)
  lib/install_common.sh    — shared installer flow: always-unload, render template,
                              plutil -lint, load, poll-verify (sourced by install_*.sh)
  daily_sync.sh            — daily_sync launchd entry (mode 2)
  vault_sync.sh            — hourly vault-only launchd entry (mode 2)
  pulse_sync.sh            — hourly pulse-publish (markdown→private repo) launchd entry (mode 2)
  pulse_web_sync.sh        — 30-minute pulse-web (web/pulse.html) launchd entry (mode 2)
  github_sync.sh           — github-only launchd entry (mode 2)
  install_*.sh             — one installer per launchd job (see SCHEDULER.md for the
                              job ↔ installer table; all delegate to lib/install_common.sh)
  setup_calendar_oauth.py  — interactive OAuth consent flow for Google Calendar
  build_extension.py       — native extension builder
  ask-self-ingest.sh       — self-ingest shell wrapper (portable mode, requires ASK_SELF_PATH)
  ask-self-query.sh        — self-query shell wrapper (portable mode, requires ASK_SELF_PATH)
  audit_modules.py         — repository hygiene audit (Approach A): verifies ingest
                              collectors / render modules / scheduled-job infrastructure
                              are documented in ARCHITECTURE.md + CHANGELOG.md; supports a
                              baseline lockfile (audit_modules.lock), recent-commit coverage
                              against the live CHANGELOG version section, and a pre-commit
                              working-tree preview (--include-uncommitted). JSON output for
                              orchestrating agents; also exposed as the audit_modules MCP tool
```

---

## License

Copyright 2025-2026 Hypercart DBA Neochrome, Inc.

rebalance is dual-licensed, matching the rest of the HiQS suite. **AGPL-3.0-only** is the
default and covers nearly every use — see [`LICENSE`](LICENSE). A commercial license is
available for use that AGPL-3.0 does not fit; see [`LICENSE-COMMERCIAL.md`](LICENSE-COMMERCIAL.md).


## Opt-in fleet Pulse delivery (GH-282)

Rebalance producers → device-owned files/exact local commits → existing Git Pulse collector →
private Git remote → each Mac's checkout/SQLite replica → combined human-readable views.
No Mac is a permanent hub. `git_ops.fleet_settings` validates the configured collector identity,
checkout and sync subdirectory. Generated live pulse, daily synthesis and digests use
`devices/<id>/`; calendar/email keep `sync/<source>/<id>.json`. Historical shared files are retained
for rollback and no longer written in fleet mode. `read_latest_snapshot` chooses validated payloads
on read; `pulse.fleet_view` derives delivered pages and is returned by fleet publishing through the
existing CLI/MCP result. These are readers of existing data, not new stores or writer daemons.

CLIO's capture UUID is independent of the friendly collector ID. Its canonical helper exports only
its owner snapshot to `devices/<UUID>/clio.jsonl`; the collector validates it before atomic publication.
Reconcile imports committed blobs into private SQLite without re-exporting foreign origins. Existing
semantic indexing, publishers and readonly XYZ ledger integrations retain their contracts. The same
Obsidian filename/header and five-minute renderer remain, backed by full history on every installed
Mac. Live fleet qualification remains tracked in the canonical GH-282 plan.
# SOP — Standard Operating Procedure

Do not store any credentials or secrets in this file, other repo files, or any PII in public facing GH issues. The same rule covers machine-specific absolute paths (e.g. a deploy runtime folder's real location) — keep those in your own gitignored `temp/RUNTIME.md`, never in a tracked file. See the pattern in `AGENTS.md` § "Deploy runtime folder".

This document codifies how work in this repo gets **evidenced**. It is written for
whoever picks up the next task, human or model, and it is binding on both.

---

## 1. The rule

> **Verified beats plausible. A claim whose evidence is unpublished is an assertion.**

If you state that something was measured — in a GitHub issue, a PR body, a commit
message, `ROADMAP.md`, a code comment, or a reply to the operator — the measurement
must be retained in [`TESTS-RESULTS/`](TESTS-RESULTS) where a reader can check it
without access to your machine.

This exists because it has already failed here. A retrieval change was tested on 5
queries with no ground truth, the result looked negative, the improvement was
reverted, and the conclusion was reported as settled. It was noise. Re-run properly
(39 queries, hand-established targets, paired significance test) the same change won
decisively — 14 improved, 0 regressed, p=0.0137 — and the earlier call had been
suppressing a real fix for weeks. See
[`TESTS-RESULTS/2026-08-20+GH-81/`](TESTS-RESULTS/2026-08-20+GH-81).

The lesson is not "test more." It is: **a small unverifiable test is worse than no
test**, because it manufactures false confidence and then gets cited.

## 2. When a campaign is required

Run one — and publish it — before any of these:

- **Choosing or replacing a model, library, or algorithm** where the claim is that one performs better than another.
- **Reverting or rejecting a change on empirical grounds.** "I tried it, it didn't help" is a claim and needs the same evidence as "I tried it, it helped." This is the specific failure above.
- **Any performance, retrieval-quality, or accuracy number** that will appear in an issue, PR, or doc.
- **Declaring a system healthy or a defect fixed** where the proof is behavioural rather than a passing unit test.

Not required for: ordinary code changes covered by the test suite, refactors with no
behavioural claim, or documentation.

**If it is not worth a campaign, it is not worth an empirical claim.** Say "not
measured" instead. That is a legitimate and useful thing to write.

## 3. How to run one

### 3.1 Write the protocol first, and freeze it

Before generating a single number, write down: the question, what is being compared,
the dataset, the metrics, and — critically — **the decision rule**: what result would
lead to which action, including the results that would embarrass the current design.

Put it in `PROJECT/2-WORKING/`. A decision rule written after seeing results is not a
decision rule; it is a rationalisation.

### 3.2 Establish ground truth by hand

For retrieval, ranking, or classification work, the correct answer must be determined
by a person **reading the artifact** — not by another model, and not by the system
under test. Discard any item whose correct answer cannot be established; do not guess
it. Record how many you discarded.

Watch for near-duplicates. If several items would legitimately satisfy the same query,
single-target scoring is invalid and will silently penalise every system equally
while looking like a real measurement.

### 3.3 Get the protocol reviewed before running it

Use `/relay-xyz` (or an equivalent independent review) on the **protocol**, not just
the results. Review after the fact can only rationalise; review before can still
change the experiment.

On GH-81 it changed the experiment twice, and one of those changes is why the
headline finding was detectable at all — the original significance rule would have
returned "no measurable difference, keep the incumbent" almost regardless of the
data. Transcripts: [`qa/`](TESTS-RESULTS/2026-08-20+GH-81/qa).

### 3.4 Include a dumb baseline

Always score the boring option — keyword search, the previous version, a constant, a
coin flip. Without it you cannot tell "our system is good" from "this task is easy."
On GH-81 the shipped configuration scored **below plain SQLite full-text search**,
which is not a fact any amount of comparing sophisticated options to each other would
have surfaced.

### 3.5 Use a paired test when systems answer the same inputs

Comparing independent per-system confidence intervals throws away the pairing and
buries real effects under between-item difficulty. Use a paired test (Wilcoxon
signed-rank for bounded/tied metrics), correct for multiple comparisons (Holm), and
report **effect size alongside p** — a significant tiny effect is a real and
reportable outcome.

Report "no significant difference" plainly when that is the answer. It is a result.

### 3.6 Prove the instrument constrains

Before trusting a new test, **make it fail on purpose.** Revert the fix and confirm
the test goes red. A test that passes against broken code measures nothing, and a
green suite full of them is worse than no suite because it is trusted.

### 3.7 Publish

Follow [`TESTS-RESULTS/README.md`](TESTS-RESULTS/README.md): campaign folder named
`YYYY-MM-DD+GH-<issue>`, `SUMMARY.md`, the primitive `.jsonl`, the scripts as run,
the QA transcripts verbatim, the raw console output.

Every aggregate in the summary must be recomputable from the primitive records. If it
isn't, the primitive is incomplete or the number is unsupported.

## 4. Reporting

### 4.1 Threats to validity are mandatory

Every `SUMMARY.md` ends with what would make the result wrong: sample size, sampling
bias, lack of blinding, deviations from protocol, what was *not* measured. Write them
even when — especially when — the result came out the way you hoped.

State deviations explicitly. On GH-81, one model ran at a reduced context window
because the full one exhausted GPU memory; that is recorded, along with the check
showing it did not explain the outcome.

### 4.2 Retract loudly

If a campaign overturns an earlier published conclusion, **say so in the same place
the original was published**, link both, and state what was wrong with the first
attempt. Do not quietly supersede it. Someone is relying on the old claim.

### 4.3 Do not overstate scope

Say what was measured, not what it implies. GH-81 measured the vector retriever in
isolation, while production fuses vector and lexical search — so "no model beat
keyword search" was a component-level result and would have been badly misleading
stated as a system-level one. That correction is in the summary because it was caught
before publication; catching it after would have meant a retraction under §4.2.

## 5. Naming things precisely

Ambiguous names cost real time and cause real errors. When identifying a model,
library, or version, use the **full identifier**, and verify it against the artifact
rather than repeating it from memory or a doc.

- Not "BGE small" → **`BAAI/bge-small-en-v1.5`**
- Not "the embedding model" → the full repo ID and dimension

Model families use several independent axes at once — family, size tier, language,
and release version — and collapsing any of them creates questions like "is this the
small one or the v1.5 one?" when the answer is *both*. See
[`docs/EMBEDDING-MODELS.md`](docs/EMBEDDING-MODELS.md) for this repo's naming
conventions and the current model's exact identity.

Verify from ground truth: the code constant, the recorded run metadata, and the
downloaded artifact should agree. Where they disagree, say which one governs.

## 6. The same thing collected twice is a defect, not a rounding error

> **One real-world entity must contribute to a metric exactly once. If an alias, a rename,
> a mirror, a fork, or a casing variant causes it to be counted twice, that is a defect —
> catch it, fix the read path, and remove the duplicate rows from the store.**

This is the source of truth for the rule. `AGENTS.md` and `GUIDING-PRINCIPLES.md` point here.

### Why it has its own section

A GitHub org rename put the same repository in `github_activity` under two spellings on the
same `scan_date`. Every read path that aggregated those rows **summed** them, so one day's
48 commits and 13 PRs were reported as 86 and 26. Nothing failed, no error was raised, and
the number was simply wrong in every ranking built on it — `top_active_repos`, the
`github_balance` MCP tool, Focus 5, the dashboard, the morning brief.

The test written to catch exactly this inserted the duplicate row with **every metric set to
zero**, so summing it changed nothing and the test passed. It could never have failed. That
is the part worth remembering: the duplicate was known about, a guard was written for it, and
the guard was inert.

### The rule, concretely

The three controls are **detect, reconcile, repair**. All three are required and none substitutes
for another: detection is the only proactive step, reconciliation is what stops a wrong number
being published, and repair is what protects every consumer that does not use the canonical read
path. They are a set, not a sequence — repair the store before or after fixing reads, but do both.

1. **Read the schema to decide the semantics — then do not expect it to enforce them.** If a table
   carries a snapshot — `UNIQUE(...) ON CONFLICT REPLACE` is the tell — then **one row wins**
   (latest `scanned_at`), and summing across aliases is wrong. If rows are genuinely disjoint
   increments, summing is right. The schema tells you which, and that is all it does: a uniqueness
   key built on a **mutable** identifier does not prevent duplicates, it *creates* them. In
   `github_activity` the key includes `repo_full_name`, so an org rename produced a new key, both
   spellings coexisted, and the constraint never fired. That is the whole origin of this defect.
2. **Reconcile at read.** Every aggregate over an entity that can have aliases maps to a canonical
   identity *before* grouping, never after, and never sums across aliases of one entity.
3. **Repair the store too.** Reconciling reads leaves wrong rows in the database for any consumer
   that does not use the canonical path — MCP tools, dashboards, exports. Re-key the stale rows to
   the canonical identity and drop superseded snapshots.
4. **Order matters when de-duplicating.** On a table declared `ON CONFLICT REPLACE`, renaming
   a row onto an existing key **silently destroys the row already there**. Delete the
   superseded rows *first*, then rename. Back up before either.
5. **Never let a de-dup test assert on zeros.** The duplicate fixture must carry the same
   non-zero values as the row it duplicates, and the test must be witnessed failing before the
   fix. A de-dup test that has never gone red is not evidence.
6. **Purge the metric, not just the source.** A number already published from doubled data is
   wrong and gets cited. Correct it, or say plainly that it was not recomputed.

### What this applies to

Any identity with more than one spelling: renamed GitHub orgs and repos, mirrors, forks,
casing variants, email aliases, Slack user IDs versus display names, project aliases in
`project_priority_rules`, and vault note paths that moved. It is not a GitHub-specific rule.

### Enforcement

`tests/test_alias_dedup_invariant.py` pins the invariant with synthetic fixtures and no
dependency on any operator's configuration or org names. It is a deterministic suite test, not
a check against live data.

---

**Related:** [`TESTS-RESULTS/README.md`](TESTS-RESULTS/README.md) (structure and
conventions) · [`AGENTS.md`](AGENTS.md) (working agreements) ·
[`ROUTER.md`](ROUTER.md) (prior-art checks before building)

## 7. A merge is not a deploy

> **Scheduled jobs run from the runtime folder, not from the branch you merged. Until
> someone pulls, the fix does not exist.**

The fleet (`launchd`) is pinned to one checkout — the path in
`~/.config/rebalance/runtime-root`, shown as `Target root` by `scripts/stack.sh status`
— and that checkout is updated deliberately, by hand, with

```
git -C "$(cat ~/.config/rebalance/runtime-root)" pull --ff-only origin development
```

This exists because it has already failed here. On 2026-09-04 eight PRs merged to
`development` in one day, including the digest filter (#163) and the compressor-gate
fix (#171). The runtime had last been pulled on 2026-09-02. Both 13:05 and 17:05
digests went to Slack still leading with the repo #163 removes, and
`obsidian-vault-embeddings` kept failing on the gate #171 relaxes — 51 commits of
merged, CI-green, verifiably working code, none of it running. Nothing reported the
gap; it was found by reading the digest by hand.

**The rule, concretely**

- After merging to `development`, run `bash scripts/stack.sh drift`. It prints how many
  commits the runtime trails and the exact pull command. Exit 1 means behind.
- `stack.sh status` prints the same line at the bottom, so the check rides along with
  the tool ROUTER.md already names as ground truth.
- The `.githooks/post-merge` hook prints it after every `git pull` in your dev
  checkout. Enable once per clone: `git config core.hooksPath .githooks`. It is a
  reminder, never a gate — it cannot fail a merge.
- A deploy is done when `stack.sh drift` says `up to date`, not when the PR says
  `Merged`. Say which in the PR or issue if it matters — "merged" and "deployed" are
  different claims (§ 5).

**Enforcement.** `tests/test_runtime_drift.py` pins the check with two throwaway
repositories and no dependency on any operator's machine — including that it still
measures the runtime when run from inside a git hook, where `GIT_DIR` points elsewhere.

## 8. Which GitHub repos get monitored

> **Authorship monitors a repo. Participation does not. There is no watchlist file.**

Settled on 2026-09-06 under GH-158. The monitored set is recomputed from scratch on
every refresh by `get_watched_repos()` in `src/rebalance/ingest/index_ops.py`:

```
watched = (project ∪ external ∪ activity ∪ pushed) − ignored
```

**A repo is monitored when any ONE of these holds:**

1. **You listed it.** It is in `repos:` on an active project in the project registry.
   This is the only manual list, and it never ages out.
2. **You flagged it external.** A project marked `external: true` is monitored for
   *everyone's* activity, not just yours. Never ages out.
3. **You authored in it recently** — a commit, a push, or a pull request opened or
   merged. One event is enough. "Recently" means the repo appeared in a GitHub scan
   run in the last 14 days; each scan aggregates a 30-day event window, so a repo can
   stay eligible up to roughly 44 days after your last contribution. Expiry is by scan
   date, not contribution date.
4. **Someone pushed to it in the last 14 days** and you can see it, per GitHub's own
   pushed-repos list. This path is *not* authorship-checked: a collaborator's push to a
   private org repo you have access to monitors it too. It exists because the events
   feed drops collaborator pushes and caps at 300 events. If that catches a repo you do
   not want, ignore it (below); tightening this path is a separate decision.

**These do NOT monitor a repo:** starring or watching it, forking it (your first push
to the fork does), opening an issue, commenting on an issue, or reviewing a pull
request. Those are participation, and monitoring a stranger's repo because you left a
comment ingests its entire history and reports other people's work as yours
(`PARKED/2026-09-03-digest-repo-contamination.md`). Editing a project board is not in
GitHub's events feed at all and is not a signal.

**A repo stops being monitored when:**

- it is explicitly ignored — `rebalance config add-github-ignored-repo <owner/repo>`.
  Ignore always wins, over every rule above; or
- it ages out — if activity or a push was its only reason to be monitored, it leaves
  the set silently once no scan in the last 14 days has carried it (see rule 3 for why
  that is later than 14 days after your last commit). There is no other drop mechanism,
  and none is planned. Note this does not drop a repo that has been promoted to a
  project or listed in `repos:` — those stay until you remove or ignore them.

**A repo becomes a project on its own** once 3 or more commits to it (all-time in
collected data, threshold configurable) are attributed to you or to a configured
cloud-agent author (`CLOUD_AGENT_AUTHORS` in `pulse.py`). The promoted row is
machine-owned and never overwrites a curated project of the same name, and from then
on the repo is monitored through the registry, so it no longer ages out. See
"Auto-promotion" in `AGENTS.md`.

**Enforcement.** `tests/test_watched_repos.py::test_participation_only_does_not_auto_watch_repo`
pins that a repo with only issues, comments and reviews stays out while a repo with a
single pull request comes in.


## GH-282 — fleet delivery deployment and lessons

Fleet mode reuses the existing collector, common publication lock and schedules. It does not
select a central Mac. Every participating Mac owns its generated paths and full-history SQLite
replica; remote delivery is eventual on the existing Git Pulse cadence. The Obsidian note is a
combined human-readable projection and is never the capture/control plane.

1. Verify canonical collector identity before opting in: configured `device_id` must be present,
   lower-case and safe, with no pending legacy migration. Inventory local writers, including manual
   CLI/MCP callers, and verify the private checkout is clean and its pending commits are accounted for.
2. Back up the declared runtime revision, configs, copied collector executable, canonical CLIO
   helper, private DB (SQLite backup API), original note and personal header. Verify hashes and DB
   integrity. Keep machine paths and original private content in ignored local deployment receipts.
3. Fast-forward the stable runtime to landed `development`. Update the already installed collector
   copy if it is not a symlink. Keep launchd labels and intervals unchanged; refresh existing long-running
   runtime processes as needed. Do not activate 3-Eyes or disabled jobs as part of this deployment.
4. In collector config set `fleet_mode=true`, the existing canonical `device_id`, and
   `fleet_sync_subdir` matching Rebalance's `sync_subdir`. Set Rebalance `pulse_fleet_enabled=true`
   and `pulse_device_id` to that same ID. Python validates literal collector settings on every publish.
   Fleet mode overrides caller `push=True` and `PULSE_PUSH`; a successful local commit is `queued`,
   never labelled remotely pushed. Shared historical files/pointers are retained but not updated.
5. For CLIO, install the separately reviewed canonical helper, configure its fleet inventory, and set
   explicit `clio_store_path`, `clio_database`, `clio_owner_uuid` in collector config. Export only
   `devices/<CLIO-UUID>/clio.jsonl`; imported origins stay in private SQLite, outside all staged paths.
   The pre-existing `snapshots/` relay remains separate. Never derive a CLIO UUID from a hostname.
6. Run actual local rendering, collector delivery and canonical reconcile; verify upstream objects,
   DB integrity/history preservation, header and the same note path. A fake fixture is useful for
   contract proof but does not qualify an actual offline/rejoin or all-Mac pilot. Other Macs remain
   disabled until their individual installation/source-coverage and archive-capacity checks pass.
7. Rollback disables Python fleet mode and restores the backed-up collector/config/runtime only
   once the private checkout is clean and no fleet commits are unpushed. Otherwise keep the new
   collector and preserved pending history until reconciled; never reset, stash or discard it.

The collector staggers once before its inherited lock. Network operations have a 900-second total
budget and per-call 120-second default timeout, with up to five extra seconds for termination;
local scanning/export overhead adds to lock time. Busy producers skip with 75 and retry on their
existing schedule. They cannot record an attempt while another process holds the lock; age of the
last delivered status remains the signal. Failed network delivery cannot report its failure remotely
until a later delivery succeeds. Fleet health adds bounded local Git reads to the legacy pure-YAML
reader; missing or unverifiable upstream evidence is conservatively not publishing. Experimental
health-check reuses that canonical reader when installed, and otherwise warns for opted-in devices.

Lessons: a merged PR is not a deployed runtime; a copied collector is a second deployment surface;
Python hostname IDs and collector IDs were different; an inherited-lock re-exec must not repeat the
stagger inside the lock. Empty repository inventories must work under macOS Bash 3.2. Preserve
pending commits and use exact owner paths; a heartbeat alone never attests application output.

Fleet render aging uses a named 10-hour bound: 7 hours of scheduled overnight pause, one hour
for fall-back DST, the producer's half-hour budget, one collector interval and half-hour network/
stagger grace. Explicit failed attempts and queued output are visible immediately; a silently
stopped renderer can take that long to age out. Doctor/health detail distinguishes queued, failed
(exit N), unavailable proof and old delivered output. A CLIO export/validation fault deliberately
stops that Mac's collector before a new heartbeat; preserve the previous snapshot, inspect the
backup/DB and cumulative guard, then rerun the existing collector after repair.

A successful local render waiting for the next collector delivery intentionally reports a temporary
doctor WARN (`queued, awaiting collector`). Warning-level health triage may report it during that
window. Observe the installed collector phase across three real intervals before changing alert
policy; this warning does not mean the render failed or its queued commit was lost.

Studio activation lessons: bootstrap all known preserved CLIO origins once with explicit origin
selection, then configure normal exports for the local owner only. Imported records must never
be echoed by routine exports. The first upgraded collector heartbeat advertises fleet mode; an
old unmarked heartbeat still uses legacy health until that delivery. Verify queue-to-delivered
health after this first check-in, not before it. Test missing/mismatched settings as well as valid
configuration: a refusal must return a structured error or doctor configuration failure, with no
Git writes. Briefly unload only loaded local delivery jobs, then restore the identical plists.
Keep capture and same-note export running, and verify preserved record payloads as well as counts.

### CLIO fleet consumer qualification

The canonical CLIO SQLite remains authoritative; the existing configured compatibility export contains full history across known origins. Verify the resolved source before adding a second reader. Raw history totals differ from filtered consumer totals: reconcile eligible projection keys and canonical source references, including multiple origins sharing one filtered prompt. JSONL records are separated by LF, not Unicode line separators. Preserve existing consumer keys and attach provenance additively. Use the existing semantic maintenance facade for selected, nonembedding projection; neither an empty result nor a guard skip proves consumer readiness. Keep scheduled memory deferral separate from delivery failure and never relax the whole stack to obtain a green receipt.

Studio follow-through (0.97.2): source and package metadata can disagree in an editable install; confirm both after deployment. Restart only existing owned long-running consumers so they import the landed code. A manual named-source refresh proves the local consumer, not the guarded schedule. Read-only XYZ facts may be useful while explicitly partial; record errors and unchanged ledger bytes without repairing unrelated history.

1. Verify a clean runtime and retain a verified SQLite backup plus the affected local configuration before activation.
2. Fast-forward the runtime to the tested, independently reviewed landing; refresh its editable package metadata without changing dependencies.
3. Restart existing long-running consumers only; preserve the note identity, installed job plists and exporter/collector cadences.
4. Preview and run the existing named CLIO refresh and selected nonembedding semantic maintenance facade. Reconcile eligible keys and every origin reference, and compare prior consumer IDs and prompt payloads to the backup.
5. Verify Daily citations, same-note/header preservation and delivered transport. For the optional XYZ seam, use existing explicit roots and prove the ledger is unchanged; retain the partial flag.
6. Observe normal guarded jobs before declaring scheduled consumer readiness. On rollback, restore the previous approved runtime and package metadata; restore only the changed config keys. Additive provenance columns are compatible with the previous reader. Use the verified consumer backup only for an observed data regression, with consumer writers paused; never rewind canonical CLIO history to undo a projection change.
---
gh_issue: 316
source: https://github.com/HiQS-Labs/rebalanceOS/issues/316
title: "Rename the work-activity signal to \"HiQS work activity\" (labels + namespace) with a backwards-compatibility adapter"
status: Implemented — plan pending Codex QA; PR open for review
created: 2026-10-03
updated: 2026-10-03
owner: Noel (start-task)
goal: Make "HiQS work activity" (HiQS = High Quality Signals) the canonical label and namespace for the per-project work-activity signal, with a backwards-compatibility adapter so no existing consumer breaks.
doc_type: project
branch: feat/hiqs-work-activity-naming
effort: 2
complexity: 2
risk: 1
phases: 1
---

# HiQS work activity — canonical naming with a compatibility adapter

## Status

| What was just completed | What's next |
|---|---|
| Recon of every surface complete; intake captured and promoted; plan drafted. | Codex plan QA, then implementation of the rename + adapter with a parity test, gate, final QA, PR. |

Rating: **rated 55/15/50/55**.
- **Priority 55:** user-directed; aligns code vocabulary with marketing (HiQS = High Quality Signals); newer work (#315) already adopts the term organically.
- **Severity 15:** naming-consistency debt, no defect or data consequence.
- **Appeal 50:** neutral; the operator didn't set a score.
- **Effort 55:** mechanical but broad — many small string surfaces plus two alias seams.

## Phase 0 — Prior art review

- `src/rebalance/mcp/tools/projects.py:26` — FastMCP tool `github_balance`, registered via `projects.register(mcp, db)` (`mcp/server.py:15`). **Extend:** add the canonical `hiqs_work_activity` tool beside it; keep the old name as a deprecated alias calling the same implementation.
- `src/rebalance/ingest/github_scan.py:741` — `get_github_balance()`, the public ingest-layer API. **Rename to `get_hiqs_work_activity()` and keep `get_github_balance` as a module-level alias** (zero callers break).
- `src/rebalance/ingest/db/queries.py` — `fetch_github_balance` + table `github_activity`. **Unchanged:** internal transport names, guarded by `test_queries_mirror_invariance.py:264` and the read-layer ratchet; renaming would be a schema/migration concern with zero operator value (AGENTS.md: function over transport — internals keep transport names).
- `src/rebalance/ingest/querier.py:287` — `"## GitHub Activity (last 7 days)"` header in the gathered context (surfaces in dashboard/pulse output). **Relabel.**
- `src/rebalance/cli/query.py:118` — `"\n--- GitHub Activity ---"`. **Relabel.**
- `src/rebalance/cli/github.py:64,72` — `github-scan` help strings. **Relabel** ("Scan HiQS work activity (GitHub) …").
- `src/rebalance/cli/onboard.py:124` — discovery string. **Relabel.**
- `README.md` / `AGENTS.md` — signal-presenting mentions (`github_balance` rows). **Relabel** where they name the signal; keep "GitHub activity" where it names the raw ingested data source (ingestion vs signal distinction, stated below).
- MCP test pattern: `tests/test_mcp_probe.py`. **Extend** with an alias-parity check (both tool names resolve; identical output for the same DB).
- Nearest prior work: #315 (already says "HiQS activity"), #313 (rename family), #124 (org-rename precedent).

## Requirements

1. **Canonical name:** `hiqs_work_activity` (MCP tool), `get_hiqs_work_activity()` (Python), label "HiQS work activity" (operator-facing strings).
2. **Backwards-compatibility adapter (required):** `github_balance` MCP tool remains registered and functional, its docstring marking it the deprecated alias of `hiqs_work_activity`; `get_github_balance` remains as an alias of the canonical function. Both tools return byte-identical shapes for the same inputs.
3. **Contract freeze:** table `github_activity`, SQL reader `fetch_github_balance`, and all output keys (`project_name`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `repos_touched`) unchanged — consumed by #300 / Needle-fork#79.
4. **Label rule:** strings that present the *signal* say "HiQS work activity"; strings that describe *ingesting the raw GitHub data source* stay literal ("GitHub activity"). This keeps the diff honest instead of blind-replacing.

## Smallest surface (ordered)

1. `ingest/github_scan.py` — rename `get_github_balance` → `get_hiqs_work_activity` (+ docstring), add `get_github_balance = get_hiqs_work_activity` alias line with a deprecation note.
2. `mcp/tools/projects.py` — add `hiqs_work_activity` tool (canonical docstring); reduce `github_balance` to a deprecated alias calling the same function.
3. `ingest/querier.py:287` + `cli/query.py:118` + `cli/github.py:64,72` + `cli/onboard.py:124` — relabel to "HiQS work activity".
4. `README.md`, `AGENTS.md` — relabel signal-presenting mentions of `github_balance` / "GitHub activity".
5. `tests/test_mcp_probe.py` (or a focused new test file following its pattern) — alias parity: both tool names registered; same DB → identical rows; `get_github_balance is get_hiqs_work_activity` alias assertion.
6. Version bump 0.98.0 → 0.98.1 + CHANGELOG entry.

## Non-goals

- No table rename, no schema migration, no JSON key changes, no `agent_tags` value changes, no SOP §8 contract changes, no close-loop (#308) renaming.

## Risks and rollback

- **Consumer drift:** external MCP clients referencing `github_balance` keep working (alias) — the only risk is them never migrating; acceptable, the alias docstring steers them.
- **Over-replacement:** blind string replacement could corrupt the ingestion-vs-signal distinction; mitigated by the label rule above and surgical per-file edits.
- **Rollback:** purely additive aliases + label strings; revert the PR.

## Tests and gate

- Focused: alias parity test + `tests/test_mcp_probe.py` + `tests/test_queries_mirror_invariance.py`.
- Gate once on the final commit: `pytest tests/`, `utils/pdda/pdda.sh run`, `check_script_inventory.py --check`, `check_read_layer.py`.

## Acceptance

- Both MCP tool names live with identical shapes; `get_github_balance` alias intact.
- No signal-presenting operator string says bare "GitHub activity"; storage and JSON keys unchanged.
- Full suite + ratchets green; issue #316 acceptance boxes checkable.

exec
/bin/zsh -lc "nl -ba PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md; nl -ba src/rebalance/mcp/tools/projects.py; sed -n '730,785p' src/rebalance/ingest/github_scan.py; rg -n 'GitHub [Aa]ctivity|github_balance|get_hiqs_work_activity|hiqs_work_activity' src tests README.md AGENTS.md MCP.md; cat tests/test_mcp_probe.py" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
 succeeded in 0ms:
     1	---
     2	gh_issue: 316
     3	source: https://github.com/HiQS-Labs/rebalanceOS/issues/316
     4	title: "Rename the work-activity signal to \"HiQS work activity\" (labels + namespace) with a backwards-compatibility adapter"
     5	status: Implemented — plan pending Codex QA; PR open for review
     6	created: 2026-10-03
     7	updated: 2026-10-03
     8	owner: Noel (start-task)
     9	goal: Make "HiQS work activity" (HiQS = High Quality Signals) the canonical label and namespace for the per-project work-activity signal, with a backwards-compatibility adapter so no existing consumer breaks.
    10	doc_type: project
    11	branch: feat/hiqs-work-activity-naming
    12	effort: 2
    13	complexity: 2
    14	risk: 1
    15	phases: 1
    16	---
    17	
    18	# HiQS work activity — canonical naming with a compatibility adapter
    19	
    20	## Status
    21	
    22	| What was just completed | What's next |
    23	|---|---|
    24	| Recon of every surface complete; intake captured and promoted; plan drafted. | Codex plan QA, then implementation of the rename + adapter with a parity test, gate, final QA, PR. |
    25	
    26	Rating: **rated 55/15/50/55**.
    27	- **Priority 55:** user-directed; aligns code vocabulary with marketing (HiQS = High Quality Signals); newer work (#315) already adopts the term organically.
    28	- **Severity 15:** naming-consistency debt, no defect or data consequence.
    29	- **Appeal 50:** neutral; the operator didn't set a score.
    30	- **Effort 55:** mechanical but broad — many small string surfaces plus two alias seams.
    31	
    32	## Phase 0 — Prior art review
    33	
    34	- `src/rebalance/mcp/tools/projects.py:26` — FastMCP tool `github_balance`, registered via `projects.register(mcp, db)` (`mcp/server.py:15`). **Extend:** add the canonical `hiqs_work_activity` tool beside it; keep the old name as a deprecated alias calling the same implementation.
    35	- `src/rebalance/ingest/github_scan.py:741` — `get_github_balance()`, the public ingest-layer API. **Rename to `get_hiqs_work_activity()` and keep `get_github_balance` as a module-level alias** (zero callers break).
    36	- `src/rebalance/ingest/db/queries.py` — `fetch_github_balance` + table `github_activity`. **Unchanged:** internal transport names, guarded by `test_queries_mirror_invariance.py:264` and the read-layer ratchet; renaming would be a schema/migration concern with zero operator value (AGENTS.md: function over transport — internals keep transport names).
    37	- `src/rebalance/ingest/querier.py:287` — `"## GitHub Activity (last 7 days)"` header in the gathered context (surfaces in dashboard/pulse output). **Relabel.**
    38	- `src/rebalance/cli/query.py:118` — `"\n--- GitHub Activity ---"`. **Relabel.**
    39	- `src/rebalance/cli/github.py:64,72` — `github-scan` help strings. **Relabel** ("Scan HiQS work activity (GitHub) …").
    40	- `src/rebalance/cli/onboard.py:124` — discovery string. **Relabel.**
    41	- `README.md` / `AGENTS.md` — signal-presenting mentions (`github_balance` rows). **Relabel** where they name the signal; keep "GitHub activity" where it names the raw ingested data source (ingestion vs signal distinction, stated below).
    42	- MCP test pattern: `tests/test_mcp_probe.py`. **Extend** with an alias-parity check (both tool names resolve; identical output for the same DB).
    43	- Nearest prior work: #315 (already says "HiQS activity"), #313 (rename family), #124 (org-rename precedent).
    44	
    45	## Requirements
    46	
    47	1. **Canonical name:** `hiqs_work_activity` (MCP tool), `get_hiqs_work_activity()` (Python), label "HiQS work activity" (operator-facing strings).
    48	2. **Backwards-compatibility adapter (required):** `github_balance` MCP tool remains registered and functional, its docstring marking it the deprecated alias of `hiqs_work_activity`; `get_github_balance` remains as an alias of the canonical function. Both tools return byte-identical shapes for the same inputs.
    49	3. **Contract freeze:** table `github_activity`, SQL reader `fetch_github_balance`, and all output keys (`project_name`, `total_commits`, `prs_opened`, `prs_merged`, `issues_opened`, `last_active_at`, `repos_touched`) unchanged — consumed by #300 / Needle-fork#79.
    50	4. **Label rule:** strings that present the *signal* say "HiQS work activity"; strings that describe *ingesting the raw GitHub data source* stay literal ("GitHub activity"). This keeps the diff honest instead of blind-replacing.
    51	
    52	## Smallest surface (ordered)
    53	
    54	1. `ingest/github_scan.py` — rename `get_github_balance` → `get_hiqs_work_activity` (+ docstring), add `get_github_balance = get_hiqs_work_activity` alias line with a deprecation note.
    55	2. `mcp/tools/projects.py` — add `hiqs_work_activity` tool (canonical docstring); reduce `github_balance` to a deprecated alias calling the same function.
    56	3. `ingest/querier.py:287` + `cli/query.py:118` + `cli/github.py:64,72` + `cli/onboard.py:124` — relabel to "HiQS work activity".
    57	4. `README.md`, `AGENTS.md` — relabel signal-presenting mentions of `github_balance` / "GitHub activity".
    58	5. `tests/test_mcp_probe.py` (or a focused new test file following its pattern) — alias parity: both tool names registered; same DB → identical rows; `get_github_balance is get_hiqs_work_activity` alias assertion.
    59	6. Version bump 0.98.0 → 0.98.1 + CHANGELOG entry.
    60	
    61	## Non-goals
    62	
    63	- No table rename, no schema migration, no JSON key changes, no `agent_tags` value changes, no SOP §8 contract changes, no close-loop (#308) renaming.
    64	
    65	## Risks and rollback
    66	
    67	- **Consumer drift:** external MCP clients referencing `github_balance` keep working (alias) — the only risk is them never migrating; acceptable, the alias docstring steers them.
    68	- **Over-replacement:** blind string replacement could corrupt the ingestion-vs-signal distinction; mitigated by the label rule above and surgical per-file edits.
    69	- **Rollback:** purely additive aliases + label strings; revert the PR.
    70	
    71	## Tests and gate
    72	
    73	- Focused: alias parity test + `tests/test_mcp_probe.py` + `tests/test_queries_mirror_invariance.py`.
    74	- Gate once on the final commit: `pytest tests/`, `utils/pdda/pdda.sh run`, `check_script_inventory.py --check`, `check_read_layer.py`.
    75	
    76	## Acceptance
    77	
    78	- Both MCP tool names live with identical shapes; `get_github_balance` alias intact.
    79	- No signal-presenting operator string says bare "GitHub activity"; storage and JSON keys unchanged.
    80	- Full suite + ratchets green; issue #316 acceptance boxes checkable.
     1	from __future__ import annotations
     2	
     3	from pathlib import Path
     4	from typing import Any
     5	
     6	from mcp.server.fastmcp import FastMCP
     7	
     8	from rebalance.ingest.github_scan import get_github_balance
     9	from rebalance.ingest.registry import get_projects
    10	
    11	
    12	def _project_repos_map(database_path: Path) -> dict[str, list[str]]:
    13	    """Return {project_name: [repo, ...]} for all active projects."""
    14	    projects = get_projects(database_path, status="active")
    15	    return {p["name"]: p.get("repos") or [] for p in projects}
    16	
    17	
    18	def register(mcp: FastMCP, database_path: Path) -> None:
    19	    @mcp.tool()
    20	    def list_projects(status: str = "active") -> list[dict[str, Any]]:
    21	        """List projects from the local project_registry table."""
    22	        normalized = status.strip().lower() if status else ""
    23	        return get_projects(database_path, status=normalized or None)
    24	
    25	    @mcp.tool()
    26	    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
    27	        """
    28	        Show GitHub activity balance across active projects.
    29	
    30	        Returns one row per project with commit/PR/issue counts over the last
    31	        `since_days` days.  Projects with no GitHub activity are flagged as
    32	        idle (is_idle=true).  Requires a prior `rebalance github-scan` run.
    33	        """
    34	        project_repos = _project_repos_map(database_path)
    35	        return get_github_balance(
    36	            database_path=database_path,
    37	            project_repos=project_repos,
    38	            since_days=since_days,
    39	        )
        kept[repo_full_name] = activity

    result.repo_activity = kept
    return sorted(skipped)


# ---------------------------------------------------------------------------
# Balance query — used by MCP tool
# ---------------------------------------------------------------------------


def get_github_balance(
    database_path: Path,
    project_repos: dict[str, list[str]],
    since_days: int = 14,
) -> list[dict[str, Any]]:
    """
    Return GitHub activity summary per project using the project→repos mapping.

    Args:
        database_path:  Path to the SQLite database.
        project_repos:  {project_name: [repo_full_name, ...]} mapping.
        since_days:     How many days back to aggregate.

    Returns:
        List of dicts with project_name, total_commits, prs_opened, prs_merged,
        issues_opened, last_active_at, repos_touched.
    """
    if not database_path.exists():
        return []

    from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_github_balance

    with db_connection(database_path, ensure_github_schema) as conn:
        return fetch_github_balance(conn, project_repos, since_days=since_days)


# ---------------------------------------------------------------------------
# Preflight discovery — GitHub repositories
# ---------------------------------------------------------------------------


@dataclass
class RepoCandidate:
    """A repository discovered from recent GitHub activity."""

    repo_full_name: str
    last_active_at: str | None
    activity_score: int  # Total events in scan window
    commit_count: int
    bands: list[str] = field(default_factory=list)  # e.g. ["A", "B", "C"]


def discover_repos_from_activity(
    token: str,
    days: int = 30,
MCP.md:68:### `github_balance`
MCP.md:84:General-purpose natural language query across all data sources. Gathers context from vault embeddings, GitHub activity, project registry, calendar events, and recent vault modifications. Optionally synthesizes a first-pass answer via a local Qwen3 LLM.
MCP.md:282:| `run_preflight` | Discovers project candidates from vault titles + GitHub activity (read-only, no registry writes) | `vault_path: str` | `{most_likely_active_projects, semi_active_projects, dormant_projects, potential_projects}` — each a list of candidate objects | GitHub scanner, vault file scan |
MCP.md:293:| `weekly_rebalance` | Weekly verdict-first report across active projects with `verdict`, `evidence`, `next_move`, target share, actual share, and confidence | Attention ledger, project targets, calendar classification, git-pulse rollups, GitHub activity, reminders |
MCP.md:294:| `project_attention` | Single-project drilldown showing attention sources, target gap, pressure, progress, and recommended next move | Attention ledger, project registry, GitHub activity, calendar classification |
MCP.md:345:   Claude should call the `ask` tool and return your project context, GitHub activity, and calendar events.
MCP.md:429:Live tools: `ask`, `list_projects`, `github_balance`, `query_notes`, `query_github_context`, `github_release_readiness`, `github_close_candidates`, `search_vault`, `create_calendar_event`, `review_timesheet`, `classify_event`, `snap_calendar_edges`, `sleuth_sync_reminders`, `onboarding_status`, `setup_github_token`, `run_preflight`, `confirm_projects`
README.md:123:AI assistants could help — but they can't see your Obsidian vault, your GitHub activity, or your Google Calendar. And sending all of that to a cloud LLM isn't an option for client work.
README.md:131:**rebalance OS** is a local-first work operating system that ingests your Obsidian vault, GitHub activity and artifacts, recent git history, calendar, and email into a queryable SQLite database — then lets any MCP-capable host or agent (ChatGPT, Gemini, Claude, Copilot, Cursor, Continue, and others where MCP is supported) answer questions about your own work, surface where your attention is actually going across projects, and trigger self-repairing background collectors when something goes wrong — all from your local machine, without sending private data to a cloud service.
README.md:150:"Where did my attention actually go this week?" — calendar hours, email threads, Slack mentions, and GitHub activity are all indexed per project. The signal-agnostic prioritization layer (in progress) will aggregate these into a transparent per-project count, narrated by AI summary rather than hard-coded verdict labels.
README.md:162:  GitHub activity   ──┤
README.md:176:                             Projects  list_projects · github_balance
README.md:245:- [x] GitHub activity scanner + 30-day A/B/C band classification
README.md:614:Claude Code calls the `ask` tool behind the scenes — it gathers your project registry, GitHub activity, vault notes, and calendar events, synthesizes a first-pass answer via a local Qwen3 model, then Claude reviews and presents a refined answer.
AGENTS.md:14:**"Find my recent work" queries.** When the user asks to find, summarize, or locate recent work/activity (what they've been doing, which project touched X recently, etc.), use `ask()`, `get_next_actions()`, `github_balance()`, `peek_source()`, or `publish_pulse()` — not Spotlight (`mdfind`) or ad-hoc filesystem search. The MCP's SQLite index is purpose-built for this and stays current via `refresh_index`. Reserve Spotlight/`find` for pure disk-location questions the registry doesn't track (e.g. "where did this repo get moved to on disk").
AGENTS.md:45:6. **Initial refresh:** Call `refresh_index(scope=["all"])` to populate the SQLite knowledge base. Use `dry_run=True` first for a preview. After it completes, `github_balance()` will return per-project commit/PR/issue counts.
AGENTS.md:56:| `github_balance(since_days?)` | GitHub activity per project (requires prior refresh) |
src/rebalance/cli/github.py:64:    """Fetch GitHub activity and persist to database for use by github_balance MCP tool."""
src/rebalance/cli/github.py:72:    typer.echo(f"Scanning GitHub activity for last {days} days...")
src/rebalance/cli/ingest_cmds.py:29:    include_github: bool = typer.Option(False, help="Scan GitHub activity for repo discovery"),
src/rebalance/cli/ingest_cmds.py:32:    """Discover potential projects from vault page titles and optional GitHub activity."""
src/rebalance/cli/onboard.py:124:    typer.echo("Discovering project candidates from vault + GitHub activity...")
src/rebalance/cli/query.py:118:        typer.echo("\n--- GitHub Activity ---")
src/rebalance/ingest/note_builder.py:374:        "- [Recent GitHub Activity](#recent-github-activity)",
src/rebalance/ingest/note_builder.py:419:    lines.extend(["", "## Recent GitHub Activity"])
src/rebalance/ingest/note_builder.py:434:        lines.append(f"- No GitHub activity in the last {payload.since_days} days.")
tests/test_health_issue_reporter.py:989:                "present; all GitHub activity ingestion has stopped"
tests/test_health_issue_reporter.py:1015:        """10-day-old GitHub activity — should be file or downgrade, rarely skip."""
src/rebalance/mcp/tools/projects.py:8:from rebalance.ingest.github_scan import get_github_balance
src/rebalance/mcp/tools/projects.py:26:    def github_balance(since_days: int = 30) -> list[dict[str, Any]]:
src/rebalance/mcp/tools/projects.py:28:        Show GitHub activity balance across active projects.
src/rebalance/mcp/tools/projects.py:31:        `since_days` days.  Projects with no GitHub activity are flagged as
src/rebalance/mcp/tools/projects.py:35:        return get_github_balance(
src/rebalance/mcp/tools/retrieval.py:65:        Gathers context from vault embeddings, GitHub activity, project
src/rebalance/ingest/next_actions.py:197:    Calendar blocks are OPERATOR_CALENDAR_ID-scoped; GitHub activity has the
src/rebalance/ingest/preflight.py:230:    Discover project candidates from vault titles and GitHub activity.
src/rebalance/ingest/lifecycle.py:95:            "Candidates assembled from remote GitHub activity and vault note "
src/rebalance/ingest/registry.py:26:    # "remote-activity" (GitHub activity discovery), "vault-note" (vault title
src/rebalance/ingest/registry.py:95:- `most_likely_active_projects`: GitHub activity last 14 days
src/rebalance/ingest/registry.py:96:- `semi_active_projects`: GitHub activity 15-30 days ago
src/rebalance/ingest/registry.py:97:- `dormant_projects`: GitHub activity 31+ days ago
src/rebalance/ingest/registry.py:153:- `most_likely_active_projects`: GitHub activity last 14 days
src/rebalance/ingest/registry.py:154:- `semi_active_projects`: GitHub activity 15-30 days ago
src/rebalance/ingest/registry.py:155:- `dormant_projects`: GitHub activity 31+ days ago
src/rebalance/ingest/project_inference.py:517:            github_bits.append(f"last GitHub activity {seed.github_last_active_at[:10]}")
src/rebalance/ingest/project_inference.py:851:    overwritten — see the "GitHub activity — window refetch" sync semantics
src/rebalance/ingest/project_inference.py:953:    GitHub activity/push signal that are not already in ANY active project's
src/rebalance/ingest/agent_tags.py:2:Classify a unit of GitHub activity by its likely originator.
src/rebalance/ingest/querier.py:4:Gathers context from all data sources (vault embeddings, GitHub activity,
src/rebalance/ingest/querier.py:199:    """Per-project GitHub activity summary."""
src/rebalance/ingest/querier.py:200:    from rebalance.ingest.github_scan import get_github_balance
src/rebalance/ingest/querier.py:203:        return get_github_balance(
src/rebalance/ingest/querier.py:285:    # GitHub activity
src/rebalance/ingest/querier.py:287:        lines = ["## GitHub Activity (last 7 days)"]
src/rebalance/ingest/querier.py:534:    Gathers context from vault embeddings, GitHub activity, project registry,
src/rebalance/ingest/github_scan.py:2:GitHub activity scanner — ported from gitdaily (TypeScript → Python).
src/rebalance/ingest/github_scan.py:472:    """Source-owned entry point for the GitHub activity scan: scan -> filter
src/rebalance/ingest/github_scan.py:741:def get_github_balance(
src/rebalance/ingest/github_scan.py:747:    Return GitHub activity summary per project using the project→repos mapping.
src/rebalance/ingest/github_scan.py:761:    from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_github_balance
src/rebalance/ingest/github_scan.py:764:        return fetch_github_balance(conn, project_repos, since_days=since_days)
src/rebalance/ingest/github_scan.py:774:    """A repository discovered from recent GitHub activity."""
src/rebalance/ingest/github_scan.py:788:    Scan GitHub activity for the past N days and return discovered repositories
tests/test_queries_mirror_invariance.py:264:        "fetch_github_balance": {
tests/test_queries_mirror_invariance.py:531:        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
tests/test_queries_mirror_invariance.py:565:        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
tests/test_client_gapfill.py:112:        self.assertIn("last GitHub activity 2026-06-29", prompt)
tests/test_github_scan.py:1:"""Tests for GitHub activity scan filtering and persistence."""
src/rebalance/ingest/db/schema.py:303:# GitHub activity schema
src/rebalance/ingest/db/schema.py:308:    """Daily per-repo/login activity rollups (powers ``github_balance``)."""
src/rebalance/ingest/db/schema.py:734:    """Create GitHub activity and local knowledge tables if they don't exist.
src/rebalance/ingest/db/queries.py:336:def fetch_github_balance(
src/rebalance/ingest/db/queries.py:341:    """Return GitHub activity balance per project using canonical repo identity.
src/rebalance/ingest/db/queries.py:1436:    "fetch_github_balance",
src/rebalance/ingest/db/__init__.py:32:    fetch_github_balance,
src/rebalance/ingest/db/__init__.py:70:    "fetch_github_balance",
"""GH-93 MCP probe tools: peek_source (raw rows) + get_next_actions (persisted ranking).

Drives the tools through the real FastMCP server (create_server) so the registration,
allowlist guard, limit clamp, and None-safety are all exercised end to end.
"""

from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from rebalance.ingest.db import db_connection, ensure_github_schema
from rebalance.mcp.server import create_server


def _call(server, name: str, args: dict) -> dict:
    """Invoke an MCP tool and decode its JSON content block to a dict."""
    content, _ = asyncio.run(server.call_tool(name, args))
    return json.loads(content[0].text)


class McpProbeTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db = Path(self._tmp.name) / "rebalance.db"

    def _seed_github_row(self) -> None:
        with db_connection(self.db) as conn:
            ensure_github_schema(conn)
            conn.execute(
                "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, "
                "pushes, prs_opened, prs_merged, issues_opened, issue_comments, reviews, "
                "last_active_at, scanned_at) VALUES "
                "('me','a/b','2026-06-01',1,0,0,0,0,0,0,'2026-06-01T00:00:00Z','2026-06-01T00:00:00Z')"
            )
            conn.commit()

    def test_peek_source_returns_rows_for_known_source(self) -> None:
        self._seed_github_row()
        server = create_server(self.db)
        out = _call(server, "peek_source", {"source": "github_activity", "limit": 5})
        self.assertEqual(out["source"], "github_activity")
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["rows"][0]["repo_full_name"], "a/b")

    def test_peek_source_rejects_unknown_source(self) -> None:
        server = create_server(self.db)
        out = _call(server, "peek_source", {"source": "secrets; DROP TABLE x"})
        self.assertIn("error", out)
        self.assertIn("github_activity", out["valid_sources"])
        self.assertNotIn("rows", out)

    def test_peek_source_clamps_limit(self) -> None:
        self._seed_github_row()
        server = create_server(self.db)
        # 9999 must not raise and must clamp (only 1 row exists, so count==1).
        out = _call(server, "peek_source", {"source": "github_activity", "limit": 9999})
        self.assertEqual(out["count"], 1)

    def test_get_next_actions_none_safe_on_fresh_db(self) -> None:
        server = create_server(self.db)
        out = _call(server, "get_next_actions", {})
        self.assertEqual(out["ranked"], [])
        self.assertIn("note", out)


if __name__ == "__main__":
    unittest.main()

codex
I’m applying the SWE plan-review rubric. The alias design looks sound, but the plan relabels raw-data scan messages despite its own label rule and misses the MCP reference. Graph tools aren’t available in this session, so I’m checking the source directly.
exec
/bin/zsh -lc "nl -ba src/rebalance/ingest/db/queries.py | sed -n '330,410p'; nl -ba src/rebalance/cli/github.py | sed -n '55,90p'; nl -ba src/rebalance/cli/onboard.py | sed -n '115,138p'; nl -ba src/rebalance/ingest/note_builder.py | sed -n '360,440p'; nl -ba MCP.md | sed -n '65,84p'; rg -n -i 'github.{0,12}activity|activity.{0,12}github|github_balance|build_context' src/rebalance/ingest/pulse* src/rebalance/web* utils/pdda/check_read_layer.py utils/pdda/*baseline* tests/test_queries_mirror_invariance.py; nl -ba src/rebalance/ingest/querier.py | sed -n '190,214p;270,310p'; rg -n '0.98.0|effort|cheapness' pyproject.toml src/rebalance/__init__.py PRS.md ROUTER.md; nl -ba src/rebalance/mcp/server.py | head -55; nl -ba src/rebalance/cli/query.py | sed -n '108,136p'" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
 succeeded in 0ms:
   330	            resolved[key] = row
   331	        return resolved
   332	    finally:
   333	        conn.set_progress_handler(None, 0)
   334	
   335	
   336	def fetch_github_balance(
   337	    conn: sqlite3.Connection,
   338	    project_repos: dict[str, list[str]],
   339	    since_days: int = 14,
   340	) -> list[dict[str, Any]]:
   341	    """Return GitHub activity balance per project using canonical repo identity.
   342	
   343	    Collapses mirror-org spellings into one canonical entity and reconciles
   344	    snapshot rows latest-scan-wins (SOP §6), so projects listing either or both
   345	    spellings of a repo get complete, undoubled stats.
   346	    """
   347	    since_date = (now_utc() - timedelta(days=since_days)).strftime(
   348	        "%Y-%m-%d"
   349	    )  # READ-LAYER-OK: P1 read layer destination for since_cutoff (GH-150)
   350	    alias_map = _get_alias_map()
   351	
   352	    canonical_stats: dict[str, dict[str, Any]] = {}
   353	    for row in _latest_activity_snapshots(conn, since_date, alias_map):
   354	        canon_key = _canonical_lower(row["repo_full_name"], alias_map)
   355	        if canon_key not in canonical_stats:
   356	            canonical_stats[canon_key] = {
   357	                "commits": 0,
   358	                "pushes": 0,
   359	                "prs_opened": 0,
   360	                "prs_merged": 0,
   361	                "issues_opened": 0,
   362	                "issue_comments": 0,
   363	                "reviews": 0,
   364	                "last_active_at": None,
   365	            }
   366	        cs = canonical_stats[canon_key]
   367	        cs["commits"] += row["commits"] or 0
   368	        cs["pushes"] += row["pushes"] or 0
   369	        cs["prs_opened"] += row["prs_opened"] or 0
   370	        cs["prs_merged"] += row["prs_merged"] or 0
   371	        cs["issues_opened"] += row["issues_opened"] or 0
   372	        cs["issue_comments"] += row["issue_comments"] or 0
   373	        cs["reviews"] += row["reviews"] or 0
   374	        la = row["last_active_at"]
   375	        if la and (cs["last_active_at"] is None or la > cs["last_active_at"]):
   376	            cs["last_active_at"] = la
   377	
   378	    results: list[dict[str, Any]] = []
   379	    for project_name, repos in project_repos.items():
   380	        total_commits = 0
   381	        total_prs_opened = 0
   382	        total_prs_merged = 0
   383	        total_issues = 0
   384	        repos_touched: list[str] = []
   385	        last_active: str | None = None
   386	
   387	        seen_canon_repos: set[str] = set()
   388	        for repo in repos:
   389	            canon_repo = _canonical_lower(repo, alias_map)
   390	            if canon_repo in seen_canon_repos:
   391	                continue
   392	            seen_canon_repos.add(canon_repo)
   393	            stats = canonical_stats.get(canon_repo)
   394	            if not stats:
   395	                continue
   396	            repos_touched.append(repo)
   397	            total_commits += stats.get("commits") or 0
   398	            total_prs_opened += stats.get("prs_opened") or 0
   399	            total_prs_merged += stats.get("prs_merged") or 0
   400	            total_issues += stats.get("issues_opened") or 0
   401	            la = stats.get("last_active_at")
   402	            if la and (last_active is None or la > last_active):
   403	                last_active = la
   404	
   405	        results.append(
   406	            {
   407	                "project_name": project_name,
   408	                "repos_linked": repos,
   409	                "repos_touched": repos_touched,
   410	                "total_commits": total_commits,
    55	    )
    56	
    57	
    58	@app.command("github-scan")
    59	def github_scan(
    60	    token: str = typer.Option(..., envvar="GITHUB_TOKEN", help="GitHub Personal Access Token"),
    61	    days: int = typer.Option(30, help="Number of days to look back (supports 30-day A/B/C band classification)"),
    62	    database: Path | None = DBOption(),
    63	) -> None:
    64	    """Fetch GitHub activity and persist to database for use by github_balance MCP tool."""
    65	    from rebalance.ingest.github_scan import scan_and_store_github_activity
    66	
    67	    try:
    68	        db_path = resolve_database_path(database)
    69	    except DatabaseNotFoundError as exc:
    70	        typer.echo(str(exc))
    71	        raise typer.Exit(2) from exc
    72	    typer.echo(f"Scanning GitHub activity for last {days} days...")
    73	    result, skipped_repos = scan_and_store_github_activity(db_path, token=token, since_days=days)
    74	    typer.echo(
    75	        f"Done: login={result.login}, events={result.total_events}, "
    76	        f"repos={len(result.repo_activity)}, skipped={len(skipped_repos)}, stored to {db_path}"
    77	    )
    78	
    79	
    80	@app.command("github-sync-artifacts")
    81	def github_sync_artifacts(
    82	    repos: list[str] = typer.Option(
    83	        [],
    84	        "--repo",
    85	        help="GitHub repo in owner/name form. Repeat the flag to sync multiple repos.",
    86	    ),
    87	    token: str = typer.Option("", envvar="GITHUB_TOKEN", help="GitHub Personal Access Token"),
    88	    days: int = typer.Option(90, help="Lookback window for changed issues and PRs"),
    89	    database: Path | None = DBOption(),
    90	) -> None:
   115	        raise typer.Exit(1)
   116	    if source != "config":
   117	        set_github_token(token)
   118	        typer.echo(f"Persisted GitHub token to config (was reachable only via '{source}').")
   119	    else:
   120	        typer.echo("GitHub token already stored in config.")
   121	
   122	    # 3. Discover candidates.
   123	    registry_path = vp / "Projects" / "00-project-registry.md"
   124	    typer.echo("Discovering project candidates from vault + GitHub activity...")
   125	    discovery = discover_candidates(vault_path=vp, registry_path=registry_path, github_token=token)
   126	    if getattr(discovery, "github_error", None):
   127	        typer.echo(f"  ! GitHub discovery error: {discovery.github_error}", err=True)
   128	
   129	    candidates = [
   130	        c
   131	        for bucket in (
   132	            discovery.most_likely_active_projects,
   133	            discovery.semi_active_projects,
   134	            discovery.dormant_projects,
   135	        )
   136	        for c in bucket
   137	    ]
   138	    if not candidates:
   360	        "generated_by: rebalance",
   361	        "tags:",
   362	        "  - dashboard",
   363	        "  - autogenerated",
   364	        "---",
   365	        "",
   366	        "# rebalanceOS Dashboard",
   367	        f"_Last generated: {generated_at}_",
   368	        "",
   369	        "## Table of Contents",
   370	        "- [Now](#now)",
   371	        "- [Recent Highlights](#recent-highlights)",
   372	        "- [Current Focus](#current-focus)",
   373	        "- [Project Rebalance](#project-rebalance)",
   374	        "- [Recent GitHub Activity](#recent-github-activity)",
   375	        "- [Needs Review](#needs-review)",
   376	        "- [Source Window](#source-window)",
   377	        "",
   378	        "## Now",
   379	        f"- {payload.operator_summary}",
   380	    ]
   381	
   382	    if synthesized_summary:
   383	        lines.extend(["", synthesized_summary.strip()])
   384	
   385	    lines.extend(["", "## Recent Highlights"])
   386	    if payload.highlights:
   387	        lines.extend([f"- {item}" for item in payload.highlights])
   388	    else:
   389	        lines.append("- No recent changelog highlights found.")
   390	
   391	    lines.extend(["", "## Current Focus"])
   392	    if payload.current_goals:
   393	        lines.extend([f"- {item}" for item in payload.current_goals])
   394	    else:
   395	        lines.append("- No current-week goals found in 4X4.")
   396	
   397	    lines.extend(["", "## Project Rebalance"])
   398	    if not payload.projects:
   399	        lines.append("- No active projects found in the local registry.")
   400	    else:
   401	        for project in payload.projects:
   402	            tier = project.priority_tier if project.priority_tier is not None else "n/a"
   403	            value_str = project.value_level or "n/a"
   404	            if project.value_score is not None:
   405	                value_str += f" ({project.value_score}/10)"
   406	            lines.extend(
   407	                [
   408	                    "",
   409	                    f"### {project.name}",
   410	                    f"- Priority tier: {tier}",
   411	                    f"- Client: {project.client or 'n/a'}",
   412	                    f"- Value: {value_str}",
   413	                    f"- Risk: {project.risk_level or 'n/a'}",
   414	                ]
   415	            )
   416	            if project.summary:
   417	                lines.append(f"- Summary: {project.summary}")
   418	
   419	    lines.extend(["", "## Recent GitHub Activity"])
   420	    if payload.org_activity:
   421	        for org, repos in sorted(payload.org_activity.items()):
   422	            lines.append(f"\n### {org}")
   423	            for repo in repos:
   424	                commits = repo["commits"]
   425	                last_active = (repo["last_active_at"] or "")[:10]
   426	                prs = repo["prs_merged"]
   427	                parts = [f"{commits} commit(s)"]
   428	                if prs:
   429	                    parts.append(f"{prs} PR(s) merged")
   430	                if last_active:
   431	                    parts.append(f"last active {last_active}")
   432	                lines.append(f"- {repo['repo_full_name']} — {' · '.join(parts)}")
   433	    else:
   434	        lines.append(f"- No GitHub activity in the last {payload.since_days} days.")
   435	
   436	    lines.extend(["", "## Needs Review"])
   437	    if payload.needs_review:
   438	        lines.extend([f"- {item}" for item in payload.needs_review])
   439	    else:
   440	        lines.append("- No unattributed or low-confidence calendar items in the current window.")
    65	
    66	---
    67	
    68	### `github_balance`
    69	
    70	Shows GitHub commit/PR/issue activity per project over a rolling window.
    71	
    72	**Prerequisite:** run `rebalance github-scan` via CLI first to populate the `github_activity` table. See PROJECT.md — Step 6 for setup.
    73	
    74	| Param | Type | Default | Description |
    75	|---|---|---|---|
    76	| `since_days` | `int` | `30` | Rolling window in calendar days |
    77	
    78	**Returns:** `list[{project_name, repos_linked, repos_touched, total_commits, prs_opened, prs_merged, issues_opened, last_active_at, is_idle}]`
    79	
    80	---
    81	
    82	### `ask`
    83	
    84	General-purpose natural language query across all data sources. Gathers context from vault embeddings, GitHub activity, project registry, calendar events, and recent vault modifications. Optionally synthesizes a first-pass answer via a local Qwen3 LLM.
tests/test_queries_mirror_invariance.py:112:        INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes, prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)
tests/test_queries_mirror_invariance.py:210:        INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes, prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)
tests/test_queries_mirror_invariance.py:264:        "fetch_github_balance": {
tests/test_queries_mirror_invariance.py:448:        INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes,
tests/test_queries_mirror_invariance.py:531:        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
tests/test_queries_mirror_invariance.py:565:        balance = queries_mod.fetch_github_balance(conn, {"P": [canonical]}, since_days=14)
utils/pdda/check_read_layer.py:17:  R1  SQL emitters  — ``FROM``/``JOIN`` over the four github activity tables
utils/pdda/check_read_layer.py:58:# R1: direct SQL over the four github ACTIVITY tables outside the db/ storage layer.
utils/pdda/check_read_layer.py:61:R1_SQL_RE = re.compile(r"\b(?:FROM|JOIN)\s+github_(?:activity|commits|direct_commits|items)\b")
   190	        logger.warning("calendar context unavailable: %s", e)
   191	        return {"upcoming": [], "recent": []}
   192	
   193	
   194	def _gather_github_context(
   195	    database_path: Path,
   196	    project_repos: dict[str, list[str]],
   197	    since_days: int = 7,
   198	) -> list[dict[str, Any]]:
   199	    """Per-project GitHub activity summary."""
   200	    from rebalance.ingest.github_scan import get_github_balance
   201	
   202	    try:
   203	        return get_github_balance(
   204	            database_path=database_path,
   205	            project_repos=project_repos,
   206	            since_days=since_days,
   207	        )
   208	    except Exception as e:
   209	        logger.warning("github context unavailable: %s", e)
   210	        return []
   211	
   212	
   213	def _gather_project_context(database_path: Path) -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
   214	    """Project registry entries + repos map."""
   270	        if tomorrow.get("is_vacation"):
   271	            lines.append(f"  Vacation: {tomorrow.get('vacation_event', '')}")
   272	        if tomorrow.get("day_type") == "off":
   273	            lines.append("  (Weekend — no work recommendations unless explicitly asked)")
   274	        sections.append("\n".join(lines))
   275	
   276	    # Project registry
   277	    if project_context:
   278	        lines = ["## Projects (by priority tier)"]
   279	        for p in project_context:
   280	            lines.append(
   281	                f"- **{p['name']}** (Tier {p['priority_tier']}, {p['risk_level']} risk): {p['summary'] or 'No summary'}"
   282	            )
   283	        sections.append("\n".join(lines))
   284	
   285	    # GitHub activity
   286	    if github_context:
   287	        lines = ["## GitHub Activity (last 7 days)"]
   288	        for g in github_context:
   289	            if g.get("is_idle"):
   290	                lines.append(f"- {g['project_name']}: IDLE (no activity)")
   291	            else:
   292	                lines.append(
   293	                    f"- {g['project_name']}: {g['total_commits']} commits, "
   294	                    f"{g['prs_opened']} PRs opened, {g['prs_merged']} merged, "
   295	                    f"{g['issues_opened']} issues opened"
   296	                )
   297	        sections.append("\n".join(lines))
   298	
   299	    if github_semantic_context:
   300	        lines = ["## Relevant GitHub Artifacts"]
   301	        for item in github_semantic_context[:5]:
   302	            md = item.get("metadata") or {}
   303	            meta = f"{md.get('repo_full_name', '')} {md.get('item_type', '')} #{md.get('source_number', '')}"
   304	            if md.get("state"):
   305	                meta += f" ({md['state']})"
   306	            if md.get("milestone_title"):
   307	                meta += f" milestone={md['milestone_title']}"
   308	            lines.append(f"### {meta}")
   309	            lines.append(item.get("title", ""))
   310	            lines.append(item.get("body_preview", "")[:320])
rg: PRS.md: No such file or directory (os error 2)
pyproject.toml:7:version = "0.98.0"
ROUTER.md:40:- `PROJECT/**` docs = canonical execution detail for a specific effort
ROUTER.md:48:4. Read `ROADMAP.md` to find the active effort. -> expect links outward to the canonical `PROJECT/**` docs; `ROADMAP.md` is a pointer ledger, not a plan body.
src/rebalance/__init__.py:31:__version__ = "0.98.0"
     1	from __future__ import annotations
     2	
     3	import logging
     4	from pathlib import Path
     5	
     6	from mcp.server.fastmcp import FastMCP
     7	
     8	from rebalance.mcp.tools import calendar, hygiene, index, onboarding, projects, retrieval, sleuth
     9	
    10	logger = logging.getLogger(__name__)
    11	
    12	
    13	def create_server(database_path: Path) -> FastMCP:
    14	    mcp = FastMCP("rebalance")
    15	    projects.register(mcp, database_path)
    16	    onboarding.register(mcp, database_path)
    17	    retrieval.register(mcp, database_path)
    18	    calendar.register(mcp, database_path)
    19	    index.register(mcp, database_path)
    20	    hygiene.register(mcp, database_path)
    21	    sleuth.register(mcp, database_path)
    22	    return mcp
    23	
    24	
    25	def main() -> None:
    26	    from rebalance.paths import DatabaseNotFoundError, canonical_database_path, resolve_database_path
    27	
    28	    try:
    29	        database_path = resolve_database_path()
    30	    except DatabaseNotFoundError:
    31	        # First run: no database exists yet. Create the canonical path so
    32	        # MCP-driven onboarding can proceed — the onboarding tools need
    33	        # the server to be running before any data exists.
    34	        from rebalance.ingest.db.connection import get_connection
    35	
    36	        database_path = canonical_database_path()
    37	        get_connection(database_path).close()
    38	        logger.info("Created empty database at %s", database_path)
    39	    server = create_server(database_path=database_path)
    40	    server.run()
    41	
    42	
    43	if __name__ == "__main__":
    44	    main()
   108	        typer.echo(f"  Today:    {today.get('day_name', '')} — {today.get('day_type', '')}")
   109	        typer.echo(f"  Tomorrow: {tomorrow.get('day_name', '')} — {tomorrow.get('day_type', '')}")
   110	
   111	    if result.synthesis:
   112	        typer.echo(f"\n--- Synthesis ({result.model_used}, {result.elapsed_seconds}s) ---\n")
   113	        typer.echo(result.synthesis)
   114	    else:
   115	        typer.echo(f"\n--- Raw context ({result.elapsed_seconds}s) ---\n")
   116	
   117	    if result.github_context:
   118	        typer.echo("\n--- GitHub Activity ---")
   119	        for g in result.github_context:
   120	            if g.get("is_idle"):
   121	                typer.echo(f"  {g['project_name']:25s}  IDLE")
   122	            else:
   123	                typer.echo(
   124	                    f"  {g['project_name']:25s}  {g['total_commits']:3d} commits  {g['prs_opened']} PRs  {g['issues_opened']} issues"
   125	                )
   126	
   127	    if result.github_semantic_context:
   128	        typer.echo("\n--- Relevant GitHub Artifacts ---")
   129	        for item in result.github_semantic_context[:8]:
   130	            # `metadata` is where repo_full_name/item_type/source_number actually live —
   131	            # querier._build_prompt already reads it this way (the LLM prompt path never
   132	            # crashed); this CLI printer read them as top-level keys instead and raised
   133	            # KeyError on every call that returned a GitHub hit, since the initial commit.
   134	            md = item.get("metadata") or {}
   135	            score = item.get("similarity_score")
   136	            score_str = f"{score:.3f}" if score is not None else "n/a"

exec
/bin/zsh -lc "nl -ba src/rebalance/ingest/db/queries.py | sed -n '405,430p'; nl -ba tests/test_queries_mirror_invariance.py | sed -n '250,283p'; nl -ba utils/pdda/check_read_layer.py | head -85; nl -ba utils/pdda/check_script_inventory.py | head -45; rg -n -i 'activity|commits' src/rebalance/ingest/pulse/render*.py src/rebalance/ingest/pulse.py | head -45; rg -n 'CLOUD_AGENT_AUTHORS' src/rebalance/ingest/db/queries.py; nl -ba src/rebalance/ingest/db/schema.py | sed -n '303,323p'; rg -n 'effort.*cheap|Appeal.*50|Severity.*15' .agents .claude utils/pdda | head -20; rg -n 'org_activity|fetch_.*activity' src/rebalance/ingest/note_builder.py" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
 succeeded in 0ms:
   405	        results.append(
   406	            {
   407	                "project_name": project_name,
   408	                "repos_linked": repos,
   409	                "repos_touched": repos_touched,
   410	                "total_commits": total_commits,
   411	                "prs_opened": total_prs_opened,
   412	                "prs_merged": total_prs_merged,
   413	                "issues_opened": total_issues,
   414	                "last_active_at": last_active,
   415	                "is_idle": len(repos_touched) == 0,
   416	            }
   417	        )
   418	
   419	    results.sort(key=lambda x: (x["is_idle"], -(len(x["repos_touched"]))), reverse=False)
   420	    return results
   421	
   422	
   423	# ---------------------------------------------------------------------------
   424	# 2. Org Activity Rollup (Dashboard Org Table)
   425	# ---------------------------------------------------------------------------
   426	
   427	
   428	def fetch_org_activity(
   429	    conn: sqlite3.Connection,
   430	    since_days: int = 14,
   250	@pytest.mark.parametrize("fn_name", PUBLIC_QUERY_FUNCTIONS)
   251	def test_query_function_mirror_invariance(db_pair, org_alias, fn_name):
   252	    """Every public query function in db/queries.py must return byte-identical results
   253	
   254	    with and without mirror org rows in the database.
   255	    """
   256	    db_clean, db_mirror = db_pair
   257	    fn = getattr(queries_mod, fn_name)
   258	
   259	    start = datetime(2026, 9, 2, 0, 0, 0, tzinfo=PACIFIC)
   260	    end = datetime(2026, 9, 3, 0, 0, 0, tzinfo=PACIFIC)
   261	
   262	    # Build function-specific arguments
   263	    kwargs_by_fn = {
   264	        "fetch_github_balance": {
   265	            "project_repos": {"XYZ Forge": ["HiQS-Labs/xyz-forge"]},
   266	            "since_days": 14,
   267	        },
   268	        "fetch_org_activity": {
   269	            "since_days": 14,
   270	            "ignored_repos": [],
   271	        },
   272	        "fetch_day_commits": {
   273	            "start": start,
   274	            "end": end,
   275	            "github_login": "noelsaw1",
   276	        },
   277	        "fetch_day_items": {
   278	            "start": start,
   279	            "end": end,
   280	            "github_login": "noelsaw1",
   281	        },
   282	        "fetch_day_comments": {
   283	            "start": start,
     1	"""Read-layer sprawl ratchets (GH-150): SQL emitters, LLM clients, day windows.
     2	
     3	Three ratchets of the exact GH-136 ``check_banned_imports.py`` contract: scan the
     4	tree, compare to an exact per-file baseline (``read_layer_baseline.json``), fail on
     5	growth AND on shrink — a file that got clean must tighten the baseline via
     6	``--update-baseline`` so the win is recorded and cannot silently regress. A same-line
     7	``# READ-LAYER-OK: <reason>`` pragma exempts a site and puts the justification in the
     8	diff; a pragma with an empty reason still counts (fail closed, per #126's pragma
     9	contract). Finding identity is relative path + occurrence count; line numbers are
    10	diagnostic only.
    11	
    12	The ratchets freeze TODAY's sprawl at its measured count so it cannot grow while the
    13	0.75.0 fe1 shared read layer (``db/queries.py``) is built; each surface migration
    14	tightens R1 by one file, F2's client deletions tighten R2, and the time-helper
    15	consolidation tightens R3. Targets per the GH-150 audit:
    16	
    17	  R1  SQL emitters  — ``FROM``/``JOIN`` over the four github activity tables
    18	                      outside ``src/rebalance/ingest/db/`` (the storage layer's
    19	                      own home). Target after fe1: zero read surfaces; ingest
    20	                      writers keep their single-writer tables via pragma.
    21	  R2  LLM clients   — LLM endpoint literals outside the two canonical clients:
    22	                      ``querier.py`` (Gemini synthesis primitive) and
    23	                      ``claude_cloud.py`` (the Claude Cloud sessions SOURCE — an
    24	                      approved collector, not a synthesis client). Measured at
    25	                      freeze time: THREE extra Gemini implementations beyond
    26	                      querier (note_builder, health_issue_reporter, repair) plus
    27	                      the cc_cloud_jobs POC's Anthropic fetch — the audit
    28	                      originally counted one of these.
    29	  R3  day windows   — reimplementations of day-bounds/window derivation (the F3
    30	                      family): ``def ...day_bounds/day_window`` helpers, the
    31	                      verbatim ``timedelta(days=since_days)).strftime("%Y-%m-%d")``
    32	                      rolling cutoff, and the naive ``datetime.now().astimezone()``
    33	                      idiom the digest's own design notes call out as DST-blind.
    34	
    35	Bare ``.astimezone()`` and ``date.today()`` are deliberately NOT ratcheted: both
    36	have far too many legitimate uses for a per-file count to be meaningful signal.
    37	The three patterns above are the audit's actual findings.
    38	"""
    39	
    40	from __future__ import annotations
    41	
    42	import json
    43	import os
    44	import re
    45	import sys
    46	from pathlib import Path
    47	
    48	ROOTS = ("src", "utils", "scripts")
    49	PRUNED_DIRS = {"tests", "__pycache__", "3-eyes"}
    50	PRUNED_PREFIXES = ("utils/pdda/",)  # the checkers themselves
    51	SQL_GATEWAY_PREFIXES = ("src/rebalance/ingest/db/",)
    52	GEMINI_CANONICAL = "src/rebalance/ingest/querier.py"
    53	ANTHROPIC_CANONICAL = "src/rebalance/ingest/claude_cloud.py"
    54	SELF_EXEMPT = "utils/pdda/check_read_layer.py"
    55	PRAGMA_RE = re.compile(r"#\s*READ-LAYER-OK:\s*(.*)$")
    56	BASELINE_PATH = Path(__file__).with_name("read_layer_baseline.json")
    57	
    58	# R1: direct SQL over the four github ACTIVITY tables outside the db/ storage layer.
    59	# (comments/repo_meta are deliberately out of scope — they pull in ingest writers
    60	# whose single-writer table access is legitimate, drowning the signal.)
    61	R1_SQL_RE = re.compile(r"\b(?:FROM|JOIN)\s+github_(?:activity|commits|direct_commits|items)\b")
    62	# R2: LLM endpoint host literals. Anything matching these outside the two canonical
    63	# clients is a synthesis/LLM HTTP implementation that must reach querier instead.
    64	R2_GEMINI_RE = re.compile(r"generativelanguage\.googleapis\.com")
    65	R2_ANTHROPIC_RE = re.compile(r"api\.anthropic\.com")
    66	# R3: the F3 day-window family.
    67	R3_DEF_BOUNDS_RE = re.compile(r"\bdef\s+_?\w*day_(?:bounds|window)\s*\(")
    68	R3_SINCE_CUTOFF_RE = re.compile(r'timedelta\(days=since_days\)\)\.strftime\("%Y-%m-%d"\)')
    69	R3_NAIVE_NOW_RE = re.compile(r"datetime\.now\(\)\.astimezone\(\)")
    70	
    71	
    72	def _iter_files(root: Path):
    73	    for top in ROOTS:
    74	        top_dir = root / top
    75	        if not top_dir.is_dir():
    76	            continue
    77	        for dirpath, dirnames, filenames in os.walk(top_dir):
    78	            dirnames[:] = [d for d in dirnames if d not in PRUNED_DIRS and not d.startswith(".")]
    79	            for name in filenames:
    80	                if not name.endswith(".py"):
    81	                    continue
    82	                file_path = Path(dirpath) / name
    83	                rel = file_path.relative_to(root).as_posix()
    84	                if rel == SELF_EXEMPT or rel.startswith(PRUNED_PREFIXES):
    85	                    continue
     1	"""Script and LaunchAgent inventory sprawl ratchet (GH-241).
     2	
     3	Freezes the inventory of shell, python, swift, and LaunchAgent template scripts
     4	under ``scripts/`` and ``utils/`` to prevent architectural sprawl and background
     5	item accumulation.
     6	
     7	Contract mirrors GH-136 (``check_banned_imports.py``) and GH-150 (``check_read_layer.py``):
     8	- Compares live tree against an exact baseline (``script_inventory_baseline.json``).
     9	- Additions fail (new debt): no new loose scripts allowed. New operator CLI verbs must
    10	  be added to ``src/rebalance/cli/``, MCP tools to ``src/rebalance/mcp/``, and background
    11	  work to the central orchestrator (``index_ops.py``).
    12	- Shrinks fail (stale baseline): when scripts or LaunchAgents are consolidated or retired,
    13	  the test fails until deliberately updated via ``--update-baseline``, permanently locking
    14	  in the reduction (enforcing the 'deleting code counts as progress' KPI).
    15	- LaunchAgent ceiling: ``launchd_templates`` count is capped at <= 13 (and ratchets downward).
    16	- Pragma exemption: A file whose first 10 lines contain ``# SCRIPT-INVENTORY-OK: <reason>``
    17	  (or ``// SCRIPT-INVENTORY-OK: <reason>`` or ``<!-- SCRIPT-INVENTORY-OK: <reason> -->``)
    18	  is exempted from script counts, BUT must be explicitly recorded in
    19	  ``script_inventory_baseline.json`` under ``exemptions`` with operator review.
    20	  An empty reason fails closed; an unrecorded exemption fails CI.
    21	"""
    22	
    23	from __future__ import annotations
    24	
    25	import argparse
    26	import json
    27	import re
    28	import sys
    29	from pathlib import Path
    30	
    31	
    32	def _resolve_repo_root() -> Path:
    33	    """Resolve project root using shared paths resolver or upward marker walk (no parents[N])."""
    34	    try:
    35	        from rebalance.paths import resolve_project_root
    36	
    37	        return resolve_project_root(Path(__file__))
    38	    except (ImportError, RuntimeError):
    39	        cur = Path(__file__).resolve().parent
    40	        while cur != cur.parent:
    41	            if (cur / ".git").is_dir() or (cur / "pyproject.toml").is_file():
    42	                return cur
    43	            cur = cur.parent
    44	        raise RuntimeError("Could not resolve repo root from " + str(__file__))
    45	
zsh:1: no matches found: src/rebalance/ingest/pulse/render*.py
46:CLOUD_AGENT_AUTHORS: tuple[str, ...] = (
107:def _author_filter_sql(column: str, cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS) -> str:
494:    cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS,
602:    cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS,
668:    cloud_authors: tuple[str, ...] = CLOUD_AGENT_AUTHORS,
   303	# GitHub activity schema
   304	# ---------------------------------------------------------------------------
   305	
   306	
   307	def _ensure_github_activity_schema(conn: sqlite3.Connection) -> None:
   308	    """Daily per-repo/login activity rollups (powers ``github_balance``)."""
   309	    conn.execute("""
   310	        CREATE TABLE IF NOT EXISTS github_activity (
   311	            id              INTEGER PRIMARY KEY AUTOINCREMENT,
   312	            login           TEXT    NOT NULL,
   313	            repo_full_name  TEXT    NOT NULL,
   314	            scan_date       TEXT    NOT NULL,
   315	            commits         INTEGER NOT NULL DEFAULT 0,
   316	            pushes          INTEGER NOT NULL DEFAULT 0,
   317	            prs_opened      INTEGER NOT NULL DEFAULT 0,
   318	            prs_merged      INTEGER NOT NULL DEFAULT 0,
   319	            issues_opened   INTEGER NOT NULL DEFAULT 0,
   320	            issue_comments  INTEGER NOT NULL DEFAULT 0,
   321	            reviews         INTEGER NOT NULL DEFAULT 0,
   322	            last_active_at  TEXT,
   323	            scanned_at      TEXT    NOT NULL,
49:    from rebalance.ingest.db import db_connection, ensure_github_schema, fetch_org_activity
52:        return fetch_org_activity(conn, since_days=since_days, ignored_repos=get_github_ignored_repos())
78:    org_activity: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
220:    org_activity = get_all_repo_activity_by_org(database_path, since_days=since_days)
256:    total_repos = sum(len(repos) for repos in org_activity.values())
259:        f"{len(org_activity)} org(s) in the last {since_days} days; "
278:        org_activity=org_activity,
420:    if payload.org_activity:
421:        for org, repos in sorted(payload.org_activity.items()):

codex
**CHANGES — the adapter is appropriate; correct the label scope and tighten the compatibility acceptance before implementation.** No architectural blocker.

1. **[Should] Preserve raw-source scan/discovery wording.** The plan explicitly relabels strings that violate its own ingestion-versus-signal rule (`PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md:39`, `:50`). Keep “Scanning GitHub activity…” in `src/rebalance/cli/github.py:72` and “Discovering project candidates from vault + GitHub activity…” in `src/rebalance/cli/onboard.py:124`. At `cli/github.py:64`, change only the referenced MCP tool to `hiqs_work_activity`; fetching and persisting GitHub activity remains literal.

2. **[Should] Expand the frozen-key list to the actual contract.** The plan’s list omits **`repos_linked` and `is_idle`**, both returned today (`src/rebalance/ingest/db/queries.py:405`). `is_idle` is actively consumed by the CLI and query renderer (`src/rebalance/cli/query.py:120`; `src/rebalance/ingest/querier.py:289`). Preserve all nine keys. Make the parity test assert a populated expected row and exact keys—not merely equality between two aliases, which could share the same regression. The existing MCP test pattern supplies real server invocation (`tests/test_mcp_probe.py:20`).

3. **[Should] Include the MCP reference and explicitly classify the dashboard surface.** `MCP.md:68` documents only `github_balance`; its live-tool list at `MCP.md:429` also needs the canonical name plus compatibility note. The dashboard separately renders “Recent GitHub Activity,” its TOC anchor, and an empty-state message (`src/rebalance/ingest/note_builder.py:374`, `:419`, `:434`). This is an org/repo rollup from `fetch_org_activity`, not the per-project adapter (`note_builder.py:49`). Explicitly classify it as either signal presentation to relabel or a distinct source view to retain. Changing `querier.py:287` does not change that dashboard heading; the plan’s dashboard/pulse propagation claim at line 37 is insufficiently grounded.

4. **[Pass] The adapter boundaries are sufficient.** The cited MCP registration and Python function locations are accurate (`src/rebalance/mcp/server.py:15`; `src/rebalance/mcp/tools/projects.py:26`; `src/rebalance/ingest/github_scan.py:741`). Keeping a module-level Python alias protects the existing querier import (`src/rebalance/ingest/querier.py:200`). Both MCP tools should share the same implementation and retain **30-day MCP defaults**, while Python retains its **14-day default**. Freezing the SQL reader and table is the correct boundary; no migration is needed (`github_scan.py:764`; `db/schema.py:310`). I found no local consumer that would break under those conditions; external experiment code was not verified.

5. **[Pass] No indicated ratchet conflict.** Mirror invariance explicitly exercises `fetch_github_balance` (`tests/test_queries_mirror_invariance.py:264`). The read-layer checker tracks SQL/client/time-window patterns, not public function names (`utils/pdda/check_read_layer.py:17`); script inventory governs additions under `scripts/` and `utils/` (`utils/pdda/check_script_inventory.py:3`). Aliases and labels should require no baseline changes. This is source review, not a claim that tests ran.

6. **[Pass/Nit] PATCH and ratings are reasonable.** `0.98.1` is proportionate to a naming correction exposing identical behavior; both current version declarations are `0.98.0` (`pyproject.toml:7`; `src/rebalance/__init__.py:31`). The 55/15/50/55 rationale is reasonable prioritization judgment, not measured evidence (plan lines 26–30). Label the last axis **effort cheapness** to avoid ambiguity.

7. **[Nit] Correct contradictory status.** The frontmatter says “Implemented,” while the status table says implementation follows plan QA (plan lines 5 and 24). The inspected source still exposes only the old names.

**RECOMMENDATION:** Approve after these small plan corrections; retain the two alias seams and avoid expanding into storage changes.
tokens used
58,356
**CHANGES — the adapter is appropriate; correct the label scope and tighten the compatibility acceptance before implementation.** No architectural blocker.

1. **[Should] Preserve raw-source scan/discovery wording.** The plan explicitly relabels strings that violate its own ingestion-versus-signal rule (`PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md:39`, `:50`). Keep “Scanning GitHub activity…” in `src/rebalance/cli/github.py:72` and “Discovering project candidates from vault + GitHub activity…” in `src/rebalance/cli/onboard.py:124`. At `cli/github.py:64`, change only the referenced MCP tool to `hiqs_work_activity`; fetching and persisting GitHub activity remains literal.

2. **[Should] Expand the frozen-key list to the actual contract.** The plan’s list omits **`repos_linked` and `is_idle`**, both returned today (`src/rebalance/ingest/db/queries.py:405`). `is_idle` is actively consumed by the CLI and query renderer (`src/rebalance/cli/query.py:120`; `src/rebalance/ingest/querier.py:289`). Preserve all nine keys. Make the parity test assert a populated expected row and exact keys—not merely equality between two aliases, which could share the same regression. The existing MCP test pattern supplies real server invocation (`tests/test_mcp_probe.py:20`).

3. **[Should] Include the MCP reference and explicitly classify the dashboard surface.** `MCP.md:68` documents only `github_balance`; its live-tool list at `MCP.md:429` also needs the canonical name plus compatibility note. The dashboard separately renders “Recent GitHub Activity,” its TOC anchor, and an empty-state message (`src/rebalance/ingest/note_builder.py:374`, `:419`, `:434`). This is an org/repo rollup from `fetch_org_activity`, not the per-project adapter (`note_builder.py:49`). Explicitly classify it as either signal presentation to relabel or a distinct source view to retain. Changing `querier.py:287` does not change that dashboard heading; the plan’s dashboard/pulse propagation claim at line 37 is insufficiently grounded.

4. **[Pass] The adapter boundaries are sufficient.** The cited MCP registration and Python function locations are accurate (`src/rebalance/mcp/server.py:15`; `src/rebalance/mcp/tools/projects.py:26`; `src/rebalance/ingest/github_scan.py:741`). Keeping a module-level Python alias protects the existing querier import (`src/rebalance/ingest/querier.py:200`). Both MCP tools should share the same implementation and retain **30-day MCP defaults**, while Python retains its **14-day default**. Freezing the SQL reader and table is the correct boundary; no migration is needed (`github_scan.py:764`; `db/schema.py:310`). I found no local consumer that would break under those conditions; external experiment code was not verified.

5. **[Pass] No indicated ratchet conflict.** Mirror invariance explicitly exercises `fetch_github_balance` (`tests/test_queries_mirror_invariance.py:264`). The read-layer checker tracks SQL/client/time-window patterns, not public function names (`utils/pdda/check_read_layer.py:17`); script inventory governs additions under `scripts/` and `utils/` (`utils/pdda/check_script_inventory.py:3`). Aliases and labels should require no baseline changes. This is source review, not a claim that tests ran.

6. **[Pass/Nit] PATCH and ratings are reasonable.** `0.98.1` is proportionate to a naming correction exposing identical behavior; both current version declarations are `0.98.0` (`pyproject.toml:7`; `src/rebalance/__init__.py:31`). The 55/15/50/55 rationale is reasonable prioritization judgment, not measured evidence (plan lines 26–30). Label the last axis **effort cheapness** to avoid ambiguity.

7. **[Nit] Correct contradictory status.** The frontmatter says “Implemented,” while the status table says implementation follows plan QA (plan lines 5 and 24). The inspected source still exposes only the old names.

**RECOMMENDATION:** Approve after these small plan corrections; retain the two alias seams and avoid expanding into storage changes.
