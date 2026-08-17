---
gh_issue: 5
source: https://github.com/HiQS-Suite/rebalanceOS/issues/5
title: "GH-5 subsystem consolidation — finish the campaign, don't restart it"
status: "Working — rewritten 2026-08-16 after discovering this is the resumption of an unfinished campaign, not a new one"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: refactor
related: "#2, #3, #4 · PR #6 (new repo) · old-repo PRs #302/#303/#304/#305 · GH-291 (repo consolidation)"
goal: >
  Finish the rebalance.lib consolidation campaign that began in the old repo and was cut in half
  by the repo migration — recovering the work stranded in unmerged PRs before GH-291 archives it —
  and collapse the remaining duplicated status vocabulary so an operator is never shown two words
  for one condition.
effort: 4
complexity: 4
risk: 3
phases: 6
ratings_provisional: false
roadmap_exempt: false
---

# GH-5 — Subsystem Consolidation

> **This document was rewritten on 2026-08-16.** The previous version described GH-5 as a new
> consolidation campaign. **It is not.** It is the second half of a campaign that started in the
> old repo (GH-292, GH-293, GH-298), whose remaining phases are sitting in unmerged PRs on a repo
> scheduled for archival. Everything below is re-planned around that fact. The prior version's
> phase-by-phase detail survives in git history and in PR [#6](https://github.com/HiQS-Suite/rebalanceOS/pull/6)'s description.

## Status

| What was just completed | What's next |
|---|---|
| **Phase 4 executed** on `feat/gh-5-phase-4-unified-health` (PR #6 merged earlier): 4.1 `--json` (agy: Approved), 4.2 pins + onboarding gate (agy: Approved), 4.3 exit reroute. Two findings en route, recorded in the Phase 4 section: the hand-counted blast radius missed a **sixth site** (caught by the 4.2 AST enumeration), and fresh installs hit the *table-not-present* branch, not the empty branch (sleuth_reminders is created by first sync). `Check.status` deletion **deferred — it still has consumers** (renderers, health.py); goes with PR2's vocabulary unification. | Open the Phase 4 PR, then **Phase R — recover the stranded old-repo PRs before GH-291 archives them.** That is the only phase with an external deadline. Then Phase O2/O3. |

## Orientation for a reader arriving cold

- **The two repos.** *New/current:* [`HiQS-Suite/rebalanceOS`](https://github.com/HiQS-Suite/rebalanceOS)
  — canonical, where this doc lives. *Old/retiring:*
  [`Hypercart-Dev-Tools/rebalance-OS`](https://github.com/Hypercart-Dev-Tools/rebalance-OS) — 1,566
  commits of history, scheduled for archival. Bare `#302/#303/#304/#305` refer to the **old** repo;
  `#6`, `#7` and issues `#1`–`#5` to the **new** one.
- **GH-291** is the repo-consolidation effort *on the old repo*. Its plan is **not in this repo** —
  it is in old-repo PR [#303](https://github.com/Hypercart-Dev-Tools/rebalance-OS/pull/303), itself
  unmerged. That is uncomfortable and deliberate to state: this plan's only deadline is owned by a
  document stranded in the exact place this plan says documents get lost. Merging #303 (Phase M) is
  partly to fix that.
- **"agy" and "Codex"** are AI reviewers (Antigravity/Gemini and OpenAI Codex) driven headlessly
  through a relay harness. Their gradings are advisory; every one cited here was independently
  verified against source before being accepted or rejected — several were rejected as factually
  wrong.
- **`/ponytail`** = a laziness/YAGNI lens (does this need to exist at all; deletion over addition).
  **`/debug-mantra`** = an evidence lens (reproduce before theorising; ask what would disprove it).
- **"Phase 5a"** was a phase of PR #6 that promoted a text-chunking helper into a new module with
  **no caller**, guarded by a 169-line fixture pinning that nothing used it. It was reverted. It is
  referenced below as the canonical example of building something speculative.
- **Phase numbering restarts between documents.** This doc's phases are M, R, 3, 4, 5b (the numbers
  are inherited from PR #6's phases so the mapping stays legible). The PR2 plan has its *own*
  Phases 0–3. "Phase 3" therefore means different things in the two documents; they are always
  named with their document.

## The operator's goals — the bar this is measured against

Stated at the outset of the repo consolidation (GH-291) and restated for this refactor. Nothing
below is scored against anything else.

**From GH-291 (repo/folder consolidation):**

| # | Goal | State |
|---|---|---|
| G1 | **One repo folder on disk** | Not started — GH-291 cutover is pre-Phase-0 |
| G2 | **Collectors and local scripts run without errors** | Partly — #4's supervision gap now surfaced by `doctor` (PR #6, Phase 6); the launchd reload is still an ops action |
| G3 | **One single public repo** | Blocked by Phase R below — archiving today strands three PRs |
| G4 | **Zero private-data leakage** | Unchanged from GH-291's plan |
| G5 | **Verified and reversible** (7-day buffer) | Unchanged from GH-291's plan |

**From this refactor:**

| # | Goal | Honest state after PR #6 | After the full plan |
|---|---|---|---|
| G6 | **Less complexity** | ❌ PR #6 adds a net module and more lines than it deletes | ✅ **Now credible.** Phase 4 was reshaped from a field rename into deleting a duplicate *verdict system* — it removes a system, not a symbol. Owner: this plan; trigger: immediately after Phase M |
| G7 | **More maintainable code** | ✅ Fewer competing definitions | ✅ |
| G8 | **Modules talk to each other** | ⚠️ Exactly one link: `doctor` ← 3-Eyes | ⚠️→✅ **Second link added by Phase 4**: the CLI stops computing its own verdict and consumes `health.py`, the reconciler the dashboards already use. That is the largest remaining instance of the original complaint |
| G9 | **Improved UI — stop explaining similar-but-different concepts** | ⚠️ 2 confusions fixed; the denominator is **not yet known** | ⚠️ Phase 3 *targets* this. It cannot be scored until Phase 3's own Phase 0 inventory runs — the earlier "~4" was a guess, and the last guess about this exact denominator (the badge trio) was wrong |

> **G6 is the goal most at risk of being quietly missed.** This campaign's natural motion is
> *adding* canonical modules. Every phase below states whether it moves net lines up or down, and
> Phase 3 and Phase 4 are the only ones that move them down.

## What we got wrong, and the fix that outlives it

Two findings, both discovered *after* the code was written. They are commonly described as "the same shape". **They are not**, and the difference decides whether the fix works:

1. **`HiQS/tests/test_clean_room.py` already enforced the "duplicate, don't import" rule** —
   mutually, generically, and framed in its own docstring as *"the extraction precondition, not a
   style check."* PR #6 shipped a narrower, one-directional copy of it. **Inside the PR whose
   purpose is removing duplicated concepts.**
2. **`src/rebalance/lib/{git_ops,json_ops,time_ops}.py`, the `tz_utils` deprecation shim, and the
   `now_iso()`/`now_utc()` API all pre-existed.** They came from the old repo's campaign
   (GH-292/293/298). The modules looked like thin stubs because their adoption was stranded in
   unmerged PRs. GH-5 read "thin stub" as "duplication to consolidate" and resumed the campaign
   blind.

Neither was a coding error — but they have **different root causes**:

- **Finding 2 is a genuine discoverability failure.** Unmerged PRs on another repo are invisible to
  any in-tree search. No amount of diligence in this repo would have surfaced them.
- **Finding 1 is not.** `HiQS/tests/test_clean_room.py` was in the tree the whole time and a
  `grep -rn` across `HiQS/` would have found it in seconds. That check was already *mandated* by
  PDDA Phase 0. It simply did not run. That is a **compliance failure**, and calling it
  "discoverability" flatters it — the cure for a skipped mandatory check is not another document
  telling you to run it.

**So there are two root causes, needing two different fixes:** cross-repo work was undiscoverable
(fix: query it), and a mandatory in-tree check was skipped (fix: make it executable, not advisory).

### The fixes, graded honestly

An earlier draft of this section claimed the recurrence was "fixed as mechanism, not exhortation".
A review called that out: the `ROUTER.md` block **is** an exhortation, and this repo already had a
mandated Phase 0 check that failed to fire. Prose an agent must voluntarily obey is not a
safeguard. Graded:

| Fix | Mechanism or exhortation? |
|---|---|
| **`utils/pdda/prior-art-check.sh`** — queries open PRs on **both** repos, `ROADMAP.md`'s in-progress list, and greps `src/ utils/ HiQS/ scripts/`. Exit 3 on a hit. Verified: it fires on **both** duplicates actually shipped (`split_oversized`, `_forbidden_imports`) and stays silent otherwise | **Mechanism.** Runs. Fails loudly if `gh` is unavailable rather than reporting a clean bill |
| **`HiQS/tests` in CI** (its own isolated step) | **Mechanism.** 162 tests and the extraction gate had never run here |
| Duplicated import scanner deleted; `test_clean_room.py` extended to 3-Eyes | **Mechanism.** One concept, enforced in CI |
| `ROUTER.md` opening block + pointers | **Exhortation.** Useful signposting; will not fire on its own. Counted as documentation, not as a control |

**Still open:** wiring `prior-art-check.sh` into something that runs unprompted (a PDDA check, a
pre-plan hook). Until then the gate exists but must still be invoked deliberately.

## Phases

### Phase M — Merges (do first; unblocks everything)

| Repo | PR | Disposition |
|---|---|---|
| new | **[#6](https://github.com/HiQS-Suite/rebalanceOS/pull/6)** — GH-5 PR1 + recovery fixes | **Merge.** 2009 tests green; the 2 failures are pre-existing on `main` |
| old | **#303** — GH-291 consolidation plan (docs only) | **Merge.** CI red is pre-existing on `main` (a missing `mcp` extra), unrelated to a markdown-only diff |
| old | **#302, #304, #305** | **Do not merge into a repo being archived.** Port instead — see Phase R |

### Phase R — Recover the stranded work ⏱ **deadline: before GH-291 Phase 4 archives the old repo**

GH-291's decisions cover transferring **issues**. They say nothing about **open PRs**, which is how
this work came to be stranded. Port each into the new repo on its own branch:

| Source | Contents | Evidence grade |
|---|---|---|
| **#305** (GH-293) | `diagnose.py`'s three PAT probes had **no retries** — one 429/5xx made `diagnose_repo` report a confident false *"PAT cannot see this repo."* Routes them through `GitHubClient` | **Observed user-facing false negative** — outranks anything in PR #6's phases 2/3 |
| **#302** (GH-298) | ruff + CI lint job; 2 real bugs, incl. a `NameError` in the commit-backfill error path (the error handler itself crashed) | **Observed** |
| **#304** (GH-292) | 92 raw clock sites → `now_iso()`/`now_utc()`. **140 such sites remain in the new repo** — measured, not assumed | Inferred (same class as PR #6's Phase 3, and its other half) |

Port order: **#305, #302, #304** — observed-symptom fixes first. Each lands as its own PR.
Net lines: up (#302 adds a lint gate) — accepted; this phase is about *recovering* value, not G6.

**Acceptance criteria per port** (the old PRs were written against a codebase that has since
diverged — this plan itself measures the drift: 92 clock sites then, 140 now):

- Re-derive, do not cherry-pick blind. Each port is re-verified against *current* source; a stale
  hunk that still applies cleanly is not evidence it is still correct.
- **#305 conflicts with shipped work**: it modifies `diagnose.py`, which PR #6 also touched. Reconcile
  deliberately rather than letting git decide.
- Each port carries a regression test that fails pre-change — the campaign-wide QA gate, applied to
  ported code as if it were new.

**Gate — and note where it is written.** "The old repo has no open PR carrying unported work before
GH-291 Phase 4 runs" is stated here, but GH-291's executor does not read this document. A gate on
the wrong side of a boundary is a hope, not a control. **Phase M therefore includes filing this gate
onto GH-291 itself** (a blocking comment on old-repo issue #291 and a checklist line in its plan), so
the archival cannot proceed through the front door without tripping it.

### Phase 3 — One status vocabulary (closes G9)

Three words name the same top tier, all user-visible: `danger` (`web_components.py:98`), `fail`
(`doctor.py:28`), `error` (`doctor.py:32`); plus `warn` vs `warning`, two enum values that look
like a typo of each other and both reach the dashboard. Deletion-forward — visible dashboard
changes accepted by operator decision. Full plan:
[GH-5-PR2-STATUS-VOCABULARY.md](../1-INBOX/GH-5-PR2-STATUS-VOCABULARY.md). **Net lines: down.**

### Phase 4 — One health verdict, consumed by every surface (the real G6 lever)

**Reshaped 2026-08-16.** This phase was scoped as "collapse `Check.status` into `Check.severity`".
That was the symptom. The cause is one layer up.

#### The finding

`src/rebalance/health.py` is **already the unified health system**. Its own docstring:

> *"Reconciled collector-health verdict — **one source of truth for the dashboards**. …so every
> surface (web pulse, TUI, …) renders a *consistent* verdict instead of three independently-computed
> pills that can contradict each other."*

It was built to fix this exact class of defect one level up, and the dashboards already consume it.
**The CLI is the holdout** — `cli/__init__.py:156` exits on `report.failed`, a raw
`any(c.status == FAIL)` scan (`doctor.py:60`) that bypasses the reconciler entirely:

| | Dashboards (`compute_health_status`) | CLI exit code (`report.failed`) |
|---|---|---|
| Suppression window (a recent sync clears a warning) | ✅ | ❌ |
| Config-driven notice demotion | ✅ | ❌ |
| Activity reconciliation | ✅ | ❌ |

So `rebalance doctor` can exit 0 while the dashboard shows errors, and vice versa. **This is the
operator's "systems not talking to each other" complaint at the verdict level, and it is the
largest remaining instance.** The dashboard is not a parallel system; it is the correct consumer.
The CLI simply never adopted it.

#### Target architecture

```
doctor.run_doctor()          →  raw per-check facts        (one producer)
health.compute_health_status →  one reconciled verdict     (one reconciler)
      ├── web pulse / TUI    →  renders it                 (already does)
      └── CLI exit code      →  derives from it            (Phase 4 adds this)
```

One producer, one reconciler, N renderers. `Check.status` then has no remaining consumer — its own
`health.py:201` docstring already calls it *"legacy … kept for CLI compatibility"* — and the field
collapses as a **consequence** rather than as the goal.

#### Why this is the G6 lever

It deletes a whole duplicate verdict path rather than renaming constants. It is the only phase in
this campaign that removes a *system* rather than a *symbol*.

#### The blast radius, measured

Checks that are `WARN` status + `ERROR` severity are shown as errors on the dashboard while the CLI
exits 0 today; under a binary verdict they begin failing it. A local grep found five, listed below —
but **a hand-counted list is not a control.** Codex correctly graded the bare assertion
"five … measured" as unverifiable. **4.2 replaces it with a parameterized test enumerating every
`WARN`+`ERROR` constructor in `doctor.py`**, so the blast radius is derived from source at test time
and a sixth site added later cannot slip in silently.

| Site | Check |
|---|---|
| `doctor.py:442` | a required table is not present |
| `doctor.py:471` | **no data ingested for a source** |
| `doctor.py:957` | Sleuth published export is stale |
| `doctor.py:1238` | auth failure events |
| `doctor.py:1458` | 3-Eyes: a job is unloaded or failing (#4's incident shape) |
| `_check_pulse_collectors` | **found by writing 4.2's enumeration test** — severity flows dynamically from `_PULSE_STATE_TO_CHECK` (ALERT / DEGRADED / NO PUSHES → WARN+ERROR). The hand count above missed it, which is the enumeration test's whole argument, demonstrated on its own plan. |

`:471` fires on **every brand-new install**, so the collapse makes `rebalance doctor` exit 1 on
first run.

> ### ⚠️ Corrected — the reroute does NOT fix this
>
> An earlier version of this plan claimed routing through the reconciler "fixes this for free
> because suppression already handles onboarding", and used that as the argument for reroute over
> rename. **Codex graded it a Blocker and it is false.** Verified by executing the real code:
>
> ```
> Check("vault", WARN, "no vault ingested", severity=ERROR)
> + a status dict showing the source synced just now
> → compute_health_status(...).verdict == "fail"     # CLI would exit 1
> → in problems: ['vault'] · in notices: []
> ```
>
> Suppression applies only to `severity == WARNING` (or `auth:*`), and notice-demotion also
> excludes ERROR — both by design (`health.py:201`: *"Error severity is never demoted"*). A
> WARN+ERROR check is unsuppressable by construction.
>
> **The reroute is still correct** — for the single-verdict-path, G6 and G8 reasons above — but it
> must be argued on those, not on a safety property it does not have.

#### Onboarding policy — DECIDED 2026-08-16

**Decision: gate the empty-source check on whether that source is configured.** An unconfigured
optional integration is a clean skip, not an error. Only a *configured* source with no data is an
error.

**This is not a new pattern — it is already the house pattern**, and extending it is cheaper than
inventing an "ever ingested" signal (the alternative previously recommended here).
`_check_figma` (`doctor.py:1080-1101`) states it outright:

> *"Posture, not nagging: optional+unconfigured is a clean skip (OK), while a half-configured state
> … is a real misconfiguration and warns."*

`_check_figma` returns `Check("figma", OK, "not configured (optional integration)")`. Phase 4
extends that posture to the four `_COLLECTOR_FRESHNESS` sources, which today check emptiness
unconditionally regardless of whether the operator ever opted in.

**Precondition verified** — a per-source configured-signal exists for all four, and each already
has a credential check in `doctor.py` whose resolver can be reused rather than duplicated:

| Source | Signal | Existing check |
|---|---|---|
| github data | `config.get_github_token()` | `doctor.py:208` ("no GitHub token configured") |
| sleuth data | Sleuth Web API credentials | `doctor.py:921` |
| calendar data | `config.get_calendar_oauth_token_json()` / `_google_oauth_source` | `doctor.py:1063` |
| email data | `config.get_gmail_ingest_method()` + OAuth resolution | `doctor.py:1005` |

**Resulting behaviour:**

| Situation | Verdict |
|---|---|
| Fresh install, nothing configured | skip → **exit 0** |
| Gmail never connected, ever | skip → **exit 0** (permanently, correctly) |
| GitHub token configured, no data ingested | **ERROR → exit 1** |
| GitHub was ingesting, now empty | **ERROR → exit 1** |

**Found during 4.2 (would have broken the fresh-install row):** some collector tables
(`sleuth_reminders`) are created by the **first sync, not by migrations** — so a genuine fresh
install hits the *table-not-present* branch of `_check_collector_freshness`, not the empty branch.
The gate therefore covers both branches; unconfigured+missing-table skips, configured+missing-table
stays an error. Discovered because the black-box fresh-install test failed on its first run — the
pin did its job before the reroute ever shipped.

**Known wrinkle to handle explicitly in 4.2:** Gmail's `mcp` ingest mode keeps credentials in the
agent's connector, not locally (`doctor.py:1009-1011`), so "configured" there means only *"the
operator selected mcp mode"* — it cannot distinguish "selected mcp and connected" from "selected
mcp and never connected". Pick and pin one reading; do not leave it implicit.

**Reuse, do not re-derive.** Each of the four resolvers above is already called by an existing
check. Phase 4 must call the same resolver, not write a second "is github configured?" predicate —
that would be this campaign's own failure mode, committed inside its own fix.

#### Sequencing within Phase 4 — the order is the safety property

**4.1 → 4.2 must precede 4.3.** At no point may a binary exit code exist that cannot be diagnosed.

- **4.1 — `rebalance doctor --json`.** Purely additive flag. **Must emit the reconciled verdict and
  each check's disposition (problem / notice / suppressed), not merely the raw check list** — Codex's
  Q4 finding: raw checks cannot explain *why* something was suppressed or demoted, so a JSON of raw
  checks leaves a binary exit code still undiagnosable in exactly the cases the reconciler acts on.
  **Prerequisite for the collapse**, not a follow-up. Risk: near-zero.
- **4.2 — Exit-code pin tests.** Three, not one: (a) a parameterized enumeration of every
  `WARN`+`ERROR` constructor in `doctor.py`; (b) a black-box fresh-install test asserting the chosen
  onboarding exit code; (c) the status-unavailable path. Risk: zero.
- **4.3 — Reroute the CLI exit through `compute_health_status()`**, then delete `Check.status` and
  `__post_init__`'s reconciliation hack once it has no consumer. **The CLI must pass the same status
  snapshot and clock the dashboard uses** — one shared provider. Codex's Q4: ordering alone is not
  sufficient, because a different `now` or a missing status dict makes recovery/suppression evaluate
  differently and the two surfaces disagree again through a new door. **Net lines: down.**

  **Executed 2026-08-16 — with the deletion honestly deferred.** The reroute shipped: exit 1 iff
  reconciled verdict == fail, `DoctorReport.failed`/`.warned` (the raw second verdict path, whose
  only consumer was the CLI) deleted, human mode gained a one-line suppressed-warnings note so a
  visible WARN row can't contradict the summary. But the "no consumer" gate for `Check.status` is
  **false today**: the CLI row renderer, pulse_web, and health.py's own visibility predicate all
  still read it, and `__post_init__`'s FAIL→ERROR promotion turned out to be *load-bearing* for the
  reroute itself (9 `FAIL` constructors carry no explicit severity; without the promotion a FAIL
  check would yield verdict *warn*). Deleting either here would have been the campaign's own
  failure mode — a wide rename disguised as a deletion. Both go with PR2's status-vocabulary
  unification, where `FAIL`-as-a-status disappears entirely.

  Verified live on this machine: `rebalance doctor` now exits 1 on the same two error-severity
  problems the dashboard shows (previously exit 0 while the dashboard showed errors).

## Phase O — Observability, so a binary verdict stays diagnosable

Phase 4 reduces the *verdict* to one bit. That is only safe if the layer underneath explains
itself. Audited state:

**Already sound — do not rebuild:** `Check.name` is a genuine stable ID (`health_issue_reporter.py:686`
depends on it); `detail`/`hint` carry actionable text; `auth_activity.jsonl` persists auth events;
`launchd_crash_state.json` persists crash history across polls; the health reporter auto-files a
deduped GitHub issue per failing check. That is a real alerting pipeline and it stays.

**Gaps, in priority order:**

- **O1 — no machine-readable output.** Delivered by 4.1; listed here so the dependency is explicit.
- **O2 — no history. ~~Build `doctor_history.jsonl`.~~ CUT.** Codex's Q5, accepted: it names no
  reader, no retention query, and no operational trigger — *"repeats the callerless-infrastructure
  risk"*. That is Phase 5a's exact mistake, proposed again three phases later by the same author, in
  the plan that documents Phase 5a as the cautionary example. The laziest thing that answers *"is
  this new / how long"* is **4.1's JSON plus the per-source timestamps and activity records that
  already exist**. Revisit only when a concrete incident cannot be answered from those — and cite
  the incident.
- **O3 — suppression windows are coupled by comment, not by code. KEEP.** `health.py:20` states
  *"Suppression windows MUST track `doctor.py` `warn_days * 24` for each source"* — a MUST enforced
  by a docstring, the same exhortation-instead-of-mechanism pattern this campaign has been bitten by
  twice. **Derive the window from one shared policy value, or test that the two agree — do not
  introduce a second hand-maintained copy** (Codex Q5). Risk: zero.

**Explicitly NOT a quick win — do not attempt as one:** normalising check names to
`subsystem:instance`. Verified: `scripts/health_issue_reporter.py:686` is
`check_id = check["name"]  # stable, registry-level id`, and that id is the GitHub issue key
(`title = f"{ISSUE_TITLE_PREFIX} {check_id}"`, matched against `open_issues` / `recently_closed`).
Renaming therefore re-files a duplicate of every currently-open health issue. It is worth doing, but
it needs a name-migration/alias map and a test proving no re-file, in its own slice.

### Phase 5b — Chunking into live indexing (still deferred, unchanged)

`note_ingester` inserts one `chunks` row per parser chunk and `semantic_index` keys each document
1:1 off that row's id. Splitting without a stable child-key scheme and a stale-child deletion policy
breaks document identity on re-index. Needs its own design pass. Phase 5a — which promoted the
chunker *without* its caller — was reverted; the next attempt promotes it **with** one.

## Out of scope (with reasons, so they stop resurfacing)

- **`_SOURCE_BADGE` / `_KIND_BADGE`** — verified *categorical* (github/gmail/client/channel), not
  severity, despite #5's own body, agy's research, and earlier summaries all claiming otherwise.
- **Internal enums with no user-facing path** (`index_ops._derive_signal_health`, `pulse_health`'s
  5-state model). agy proposed collapsing every internal enum; declined — enums no operator sees are
  not this problem, and unifying them repeats Phase 5a's mistake.
- **HiQS / 3-Eyes internals** — standalone packages; the clean-room gate is now enforced in CI.
- **A cleanroom rewrite from `main`** — a lens-applied replan converges on the same substantive
  phases and differs only by dropping two safe ones: the largest possible diff to reach a
  destination two reverts away.

## QA gate

Every phase ships a regression test that **fails pre-change and passes post-change** — not generic
coverage. Full suite is now `pytest tests/ utils/3-eyes/tests HiQS/tests`.
