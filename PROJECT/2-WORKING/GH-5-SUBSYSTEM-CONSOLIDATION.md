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
| PR [#6](https://github.com/HiQS-Suite/rebalanceOS/pull/6) open (6 phases + post-ship QA: Phase 5a reverted, `unknown`-state hardened, claims narrowed). Recurrence **mitigated, not closed** — see "What we got wrong". One real mechanism shipped (`utils/pdda/prior-art-check.sh`, plus `HiQS/tests` in CI); the `ROUTER.md` block is documentation and will not fire on its own. | Merge PR #6, then **Phase R — recover the stranded old-repo PRs before GH-291 archives them.** That is the only phase with an external deadline. |

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

Five checks are `WARN` status + `ERROR` severity today — shown as errors on the dashboard while the
CLI exits 0. Under a binary verdict they begin failing the CLI:

| Site | Check |
|---|---|
| `doctor.py:442` | a required table is not present |
| `doctor.py:471` | **no data ingested for a source** |
| `doctor.py:957` | Sleuth published export is stale |
| `doctor.py:1238` | auth failure events |
| `doctor.py:1458` | 3-Eyes: a job is unloaded or failing (#4's incident shape) |

`:471` fires on **every brand-new install**, so a naive collapse makes `rebalance doctor` exit 1 on
first run. Routing through the reconciler fixes this for free — suppression and demotion already
handle onboarding. **This is the argument for doing the reroute instead of the rename:** the rename
introduces the hazard, the reroute removes it.

#### Operator decision, recorded

Binary pass/fail is accepted: **`error` exits 1, everything else exits 0**, evaluated against the
*reconciled* verdict, not raw check status.

#### Sequencing within Phase 4 — the order is the safety property

**4.1 → 4.2 must precede 4.3.** At no point may a binary exit code exist that cannot be diagnosed.

- **4.1 — `rebalance doctor --json`.** Purely additive flag emitting name/status/severity/detail/
  hint per check. **Prerequisite for the collapse**, not a follow-up: a binary exit code is only
  actionable if the failure list is machine-readable. Net lines: up (~20). Risk: near-zero.
- **4.2 — Exit-code pin test.** Asserts exactly which conditions exit non-zero, so the blast radius
  above is visible in the diff and cannot drift silently later. Risk: zero.
- **4.3 — Reroute the CLI exit through `compute_health_status()`**, then delete `Check.status` and
  `__post_init__`'s reconciliation hack once it has no consumer. **Net lines: down.**

## Phase O — Observability, so a binary verdict stays diagnosable

Phase 4 reduces the *verdict* to one bit. That is only safe if the layer underneath explains
itself. Audited state:

**Already sound — do not rebuild:** `Check.name` is a genuine stable ID (`health_issue_reporter.py:686`
depends on it); `detail`/`hint` carry actionable text; `auth_activity.jsonl` persists auth events;
`launchd_crash_state.json` persists crash history across polls; the health reporter auto-files a
deduped GitHub issue per failing check. That is a real alerting pipeline and it stays.

**Gaps, in priority order:**

- **O1 — no machine-readable output.** Delivered by 4.1; listed here so the dependency is explicit.
- **O2 — no history.** Nothing persists a `DoctorReport`, so *"is this new?"* and *"how long?"*
  cannot be answered — which is precisely how #4's collector stayed dead for days without anyone
  noticing. Append each run to a bounded `doctor_history.jsonl` (same shape as the existing auth
  log; BOUNDED per `GUIDING-PRINCIPLES.md`). Risk: low, additive write.
- **O3 — suppression windows are coupled by comment, not by code.** `health.py:20` states
  *"Suppression windows MUST track `doctor.py` `warn_days * 24` for each source"* — a MUST enforced
  by a docstring. This is the same exhortation-instead-of-mechanism pattern this campaign has
  already been bitten by twice. Replace with a test that fails when the two drift. Risk: zero.

**Explicitly NOT a quick win — do not attempt as one:** normalising check names to
`subsystem:instance`. `health_issue_reporter` dedupes filed GitHub issues **on the check name**, so
renaming re-files duplicates of every currently-open health issue. It is worth doing, but it needs
a name-migration map and its own slice.

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
