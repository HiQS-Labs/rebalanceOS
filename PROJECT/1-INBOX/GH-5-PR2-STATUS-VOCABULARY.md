---
gh_issue: 5
source: https://github.com/HiQS-Suite/rebalanceOS/issues/5
title: "GH-5 PR2 — one status vocabulary across every user-facing surface"
status: "Executed — shipped as PR #18 (0.69.8); Phase 1b field collapse deliberately deferred"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: refactor
related: "PR #6 (GH-5 PR1), #2, #3"
goal: >
  Collapse the three competing words for the same severity tier (danger / fail / error) into one
  taxonomy that every user-facing surface renders from, and delete the duplicate machinery that
  held them apart. Deliberately deletion-forward: visible dashboard changes are accepted, and net
  lines should go DOWN.
effort: 3
complexity: 3
risk: 3
phases: 4
ratings_provisional: true
roadmap_exempt: false
---

# GH-5 PR2 — One Status Vocabulary

> **Why this exists.** PR1 ([#6](https://github.com/HiQS-Suite/rebalanceOS/pull/6)) answered the
> "systems not talking" half of #5 and fixed two specific jargon confusions. It did **not** reduce
> complexity — it added a net module and more lines than it deleted. Post-ship QA by agy and Codex,
> adjudicated through `/ponytail` and `/debug-mantra`, put the remaining problem precisely: this is
> a **presentation** problem, not an internal-enum problem.

## Status

| What was just completed | What's next |
|---|---|
| Executed as [#18](https://github.com/HiQS-Suite/rebalanceOS/pull/18) (0.69.8): Phases 0–3 shipped; Phase 0's DB query found zero stored old literals (no migration); tz_utils deletion required repointing four consumers the plan predates; a pre-existing swapped-argument badge bug was found and fixed en route. Net −124 lines. | Phase 1b (status/severity field collapse) remains deferred — its own scoped change with its own plan. |

## The finding this is built on

Three different words name the **same top severity tier**, and all three are user-visible:

| Word | Defined at | Reaches the user via |
|---|---|---|
| `danger` | `web_components.py:98` `_BADGE_VARIANTS` | `/auth-log` event badges |
| `fail` | `doctor.py:28` `FAIL` (`Check.status`) | `doctor` CLI output, `HealthStatus.verdict` |
| `error` | `doctor.py:32` `ERROR` (`Check.severity`) | dashboard banner counts ("21 notices", "2 errors") |

Same for the middle tier — `warn` (badges, `Check.status`) vs `warning` (`Check.severity`) — which
is worse than a synonym problem: `warn` and `warning` are *different values in different enums that
look like a typo of each other*, and both appear on the dashboard.

### A correction to the earlier framing — do not chase this phantom

Issue #5's body, agy's research, and my own earlier summaries all described
`_EVENT_BADGE`/`_SOURCE_BADGE`/`_KIND_BADGE` as "a competing 5-tier severity vocabulary". **Verified
false.** `_SOURCE_BADGE` (`web.py:230`) and `_KIND_BADGE` (`web.py:391`) map *categorical* values —
`github`, `gmail`, `client`, `channel` — and merely reuse the shared colour variants. They carry no
severity meaning and are **out of scope**. Only `_EVENT_BADGE` (`web.py:201`) mixes severity
(`ok`/`warn`/`danger`) with categorical (`info`) in one table.

Scoping this PR to "collapse the badge trio" would therefore have been mostly wasted work on two
tables that were never the problem.

## Phases

### Phase 0 — Inventory (no code)

Enumerate every surface that renders a status word to a human, and record the exact vocabulary each
one emits: dashboard banner + sync chip (`pulse_web.py`), `/auth-log` badges (`web.py`), Focus 5
tiles, `rebalance doctor` CLI, 3-Eyes CLI (`three_eyes_cli.py health`).

**Gate:** a table showing, for each surface, the literal strings an operator can see. A pair only
qualifies as a defect if an operator can encounter **both** words for **one** condition. Anything
that fails that test is dropped from scope here — this is the `/debug-mantra` rule that an
observation must be verified before a hypothesis inherits its shape, and it is exactly the check
that would have caught the badge-trio phantom above before it reached a plan.

### Phase 1 — Unify the *words* (the whole vocabulary fix, and it is small)

**This is the ponytail answer and it is most of the value.** Adopted from agy's Q3: the shortest
diff that achieves "stop explaining similar but different concepts" is to change the string
*values*, not restructure anything:

- `doctor.py:28` `FAIL = "fail"` → `"error"`, `doctor.py:27` `WARN = "warn"` → `"warning"`
- `web_components.py:98` `_BADGE_VARIANTS`: `danger` → `error`, `warn` → `warning`
- `web.py:201` `_EVENT_BADGE`'s severity entries follow

**Precondition (do not skip):** these strings may be persisted, compared, or matched in CSS class
names (`badge-danger`) and in tests. Grep every literal before changing it — a value rename is only
"one line" if nothing downstream keys off the old value. The CSS rules in particular are named
`.badge-{variant}` and must be renamed in lockstep.

**Grep is not sufficient, and saying "may be persisted" while only prescribing grep is a gap.**
Grep inspects code; it cannot see data at rest. This repo is SQLite-backed, so historical rows may
already store `danger`/`warn`/`fail` literals — after a rename those rows render as unknown
variants (and `badge_html` silently degrades an unknown variant to `neutral`, so the damage is
*invisible*, not loud). **Query the database for stored instances of every old literal before
renaming**, and if any exist, decide explicitly between a migration and a read-side compatibility
map. Neither is free; picking neither is the failure mode.

### Phase 1b — Do NOT collapse `Check.status` into `Check.severity`

**Reversed from this plan's first draft.** The draft called this "the single highest-value
deletion". That was wrong, and agy flagged it as a Blocker — though its stated reasoning ("severity
is a static configured tier") and its citations were both incorrect. The actual mechanism, verified
directly:

1. **`health.py:100`** — `if check.status not in {FAIL, WARN} and check.severity != NOTICE: continue`.
   An **OK-status check is rendered when its severity is NOTICE**. That is literally what the
   dashboard's "21 notices" are. Severity therefore carries real meaning on a passing check.
2. **`cli/__init__.py:156`** — `if report.failed:` → `raise typer.Exit(1)`, where `failed` is
   `any(c.status == FAIL ...)` (`doctor.py:60`). **`status` drives the process exit code**;
   `severity` does not.

So the two fields are two genuine axes: *does this fail the command* (status) and *how loudly does
the dashboard say it* (severity). A naive collapse would silently change either the dashboard's
notice count or `rebalance doctor`'s exit code — the kind of unobserved behavior change this whole
campaign exists to stop making.

A careful collapse to a single 4-value tier (`ok`/`notice`/`warning`/`error`) *is* expressible, but
it requires an explicit, deliberate decision about which tiers exit non-zero. **That is its own
scoped change with its own plan — not a free deletion bundled into a vocabulary fix.** Deferred.

### Phase 2 — Delete the duplicate machinery

Deletion-forward, per the operator's explicit call to accept visible dashboard changes:

- Map `_EVENT_BADGE`'s severity entries onto the canonical tiers; leave its categorical `info`
  entries alone. Rename the `.badge-*` CSS rules in lockstep with Phase 1's value changes.
- **Delete `src/rebalance/tz_utils.py`** and `tests/test_tz_utils.py`. PR1 removed its last
  production caller; it now exists only to be re-exported from, and PR1 deliberately left its test
  alone pending exactly this "separately announced removal" — this is that announcement.

  *agy graded this deletion a Blocker, claiming `tz_utils.py:320` documents backward compatibility
  and that "external downstream dependents (like the HiQS/3-Eyes standalone packages)" still import
  it.* **Rejected — verified false on both counts.** The file is **38 lines** long, so there is no
  line 320. And a repo-wide grep finds **zero** references to `tz_utils` outside the module itself
  and its own test — including none in `HiQS/` or `utils/3-eyes/`, which by the campaign's standing
  rule import nothing from `rebalance` at all (pinned by an AST test added in PR1). The deletion is
  safe. Re-run the grep at execution time regardless; do not take this paragraph on trust either.

**Net lines must go DOWN.** If this phase adds lines, it has gone wrong. With the `status`/`severity`
collapse correctly removed from scope, the deletion budget is `tz_utils.py` (38 lines) plus its test
— modest, and the plan should not pretend otherwise.

### Phase 3 — Pin it

One test asserting no surface emits a word outside the canonical set, so a future surface cannot
quietly invent a fourth synonym. This replaces per-surface assertions rather than adding to them.

## Explicitly out of scope

- `_SOURCE_BADGE` / `_KIND_BADGE` — categorical, not severity (see correction above).
- `pulse_health`'s internal 5-state model — PR1 mapped it at the boundary; it has other consumers
  and its own tests.
- `index_ops._derive_signal_health` — internal per-source freshness, already tested, no user-facing
  path. agy proposed collapsing every internal enum; **declined** — enums no operator ever sees are
  not this problem, and unifying them would repeat Phase 5a's mistake.
- HiQS / 3-Eyes internal vocabularies — standalone packages; the duplicate-don't-import rule holds.

## What this PR will and will NOT deliver

agy's Q6 is right that changing constants does not make modules talk to each other — though that was
never PR2's job (PR1's supervision bridge was). Against the four stated outcomes, honestly:

| Goal | PR2 delivers? |
|---|---|
| Improved UI — stop explaining similar-but-different concepts | **Yes.** This is the whole point: one word per tier, everywhere an operator looks. |
| More maintainable | **Yes, modestly.** One vocabulary to learn; one CSS variant set. |
| Less complexity | **Marginally.** With the field collapse correctly deferred, the deletion is `tz_utils.py` + its test. Net lines go down, but not dramatically. Anyone expecting a large reduction should read this row twice. |
| Modules talk to each other | **No — and it is not scoped to.** PR1 delivered the one real link (doctor ← 3-Eyes). Further integration is separate work. |

## Risk

Medium, and honestly so: this changes what the dashboard *looks like*. That is intended, not
collateral. The mitigation is Phase 0 — no word gets changed until the inventory proves an operator
can actually encounter the conflicting pair.
