# Relay — QA the GH-100 header status unification

- **Producer:** Claude (rebalanceOS)
- **Reviewer:** Agy
- **Artifact under review:** commit `3019e9f` on branch `feat/gh100-gh101-web-status-unification`
- **Status:** Changes requested

---

## What changed and why

The Pulse dashboard header carried four status widgets. **Three rendered from the
same `HealthStatus` object**, a few lines apart in one f-string in
`scripts/pulse_web.py`:

| widget | function | text on a live screen |
|---|---|---|
| sync chip | `render_sync_chip(health_status, …)` | `Sync degraded · 2026-08-20 5:16 PM · 22m ago` |
| health banner | `render_health_banner(health_status, …)` | `1 ERROR · 2 WARNINGS · 18 NOTICES` / `Attention needed` / `Last data ingest … 22m ago` |
| sidebar notices | `build_nav_data(notices=health_status.notices, …)` | `Notices · 21` |

One fact, three vocabularies, ingest timestamp printed twice. `src/rebalance/health.py`
already describes `HealthStatus` as *"The one verdict every dashboard surface renders
from"* — the contract held in the data layer and was broken three times in rendering.

**The change:** `render_sync_chip` and `render_health_banner` are deleted and replaced
by `render_status_bar`, which renders in **every** state including healthy. Rendering
when healthy is what retires the chip — the chip existed only to have somewhere to say
"last ingest" when nothing was wrong.

Four sub-defects fixed:

1. **Headline counted notices.** `status_text` folds notices in whenever any exist.
   New `HealthStatus.problem_text` counts errors + warnings only. Notices keep their
   own count in the sidebar; the copy button still carries the complete picture.
2. **The remedy was the first thing clipped.** `check.hint` was truncated to 120 chars
   AND laid out in a non-wrapping flex row inside `overflow-x: auto` — producing
   `→ inspect tem…` on screen. Hint is no longer trimmed; items and their text wrap.
   `.health-banner-fix` had no CSS rule at all; it does now.
3. **`+1 more`** → `N more problems not shown`.
4. **"Attention needed"** deleted — a mood, and the third label for what the badge says.

## Files

- `scripts/pulse_web.py` — `render_status_bar`, CSS, header call site, dead CSS removed
- `src/rebalance/health.py` — new `problem_text` property
- `tests/test_pulse_web_goals.py` — 6 new tests
- `tests/test_pulse_web_timestamp_disambiguation.py` — GH-5 guards ported to the bar

## State

- `pytest tests/` → **1956 passed, 0 failed, 16 skipped, 10 xfailed**
- `ruff check` / `ruff format --check` clean; doc-link guard clean
- `pulse_server` still imports cleanly (`FAIL`/`WARN` were removed from a
  `pulse_web` import that a comment warned is re-export-sensitive; verified
  `pulse_server` does not re-export them)

## Definition of Done for your turn

Read the actual code — do not take this summary's word for anything. Be adversarial.
Answer each, briefly, with a position:

1. **Did anything the deleted widgets did get LOST?** The chip rendered
   `health.verdict` (OK/WARN/FAIL); the bar renders `health.failures`/`.warnings`.
   Name any input where the two disagree. `compute_health_status` can return `WARN`
   for CLI compatibility in cases the docstring hints at — does that matter here?

2. **Is `problem_text` correct at the boundaries?** Zero problems, errors only,
   warnings only, both. Does `"healthy"` as a sentinel string cause trouble for any
   caller? Is excluding notices from the headline defensible, or does it hide
   something an operator needs?

3. **Does the layout actually fix the clipping, or move it?** Hints are now
   unbounded. `.health-banner` still has `overflow: hidden`, and `.health-banner-lead`
   still has `white-space: nowrap`. Can a very long hint, or many problems, still
   produce unreadable or broken output? Is there a case where removing
   `overflow-x: auto` made something WORSE?

4. **Is the always-render decision right?** A healthy system now gets a persistent
   full-width bar. Is that noise? Would you argue for hiding it when healthy — and if
   so, what brings back the chip's job?

5. **Anything else that is actually wrong.** Escaping, aria/accessibility,
   the removed `.synced` CSS being referenced anywhere you can find, the copy-button
   JS selector (`.health-banner-copy-btn[data-copy-text]`) still matching, dead code.

Do **not** rewrite the feature. Report findings; the producer applies fixes.

---

▶ **TAKE YOUR TURN** — append your review below this line as `## Turn 2 — Agy`, then set
`Status:` to `Approved` if you would ship this as-is, or `Changes requested` if not.
Advisory only: report, do not edit source files.

## Turn 2 — Agy

1. **Did anything the deleted widgets did get LOST?**
   No. `HealthStatus.verdict` calculates `FAIL` if `any(c.severity == ERROR)` and `WARN` if `any(c.severity == WARNING)`. This is the exact same logic `health.failures` and `health.warnings` use to filter. Even when a check has a legacy `status=WARN` but `severity=ERROR` (as the docstring mentions for CLI compatibility), the `HealthStatus.verdict` uses the `ERROR` severity to evaluate as `FAIL`, and the bar correctly places it in `health.failures`. They are structurally identical; no divergence.

2. **Is `problem_text` correct at the boundaries?**
   Yes. It correctly yields "1 error", "1 warning", "1 error · 1 warning", and defaults to `"healthy"` at zero counts. `"healthy"` is a safe string and causes no rendering issues. Excluding notices from the headline is defensible: it avoids false alarms for acknowledged issues, while the copy-button (`bucket_text`) preserves them for complete bug reporting.

3. **Does the layout actually fix the clipping, or move it?**
   It fixes the hints clipping (they now wrap correctly with `overflow-wrap: anywhere`), but it **moves** the clipping to the `.health-banner-lead` on very narrow screens. Because `.health-banner` has `overflow: hidden` (without `overflow-x: auto`), and `.health-banner-lead` has `white-space: nowrap` within the grid's `auto` column, a narrow viewport will permanently cut off the lead text and the copy button with no way to scroll to them.

4. **Is the always-render decision right?**
   Yes. It's a sensible tradeoff. Hiding it would force us to invent a second UI component (like the old chip) just to display the latest ingest timestamp. A quiet, subdued gradient (`.health-banner-ok`) avoids being too noisy while keeping the structural consistency of a single state surface.

5. **Anything else that is actually wrong.**
   - **Escaping (Newline Loss)**: `data-copy-text="{_esc(copy_text)}"` uses `html.escape`, which doesn't encode newlines. In HTML, raw newlines in attribute values are normalized to spaces by the parser. This means the copied text (via `dataset.copyText`) will lose all line breaks and collapse into a single giant line. It must be explicitly encoded (e.g., `&#10;`).
   - **aria/accessibility**: The copy button redundantly declares `aria-label="Copy health summary"` while also having a child `<span class="visually-hidden">Copy health summary</span>`. Screen readers will read the label twice. Pick one.
   - **JS Selector**: The `.health-banner-copy-btn[data-copy-text]` selector matches the new button successfully, but due to the newline HTML attribute parsing issue mentioned above, it'll fetch the collapsed space-separated string.
   - **Dead Code**: `forget_goal_completion` and `remember_goal_completion` in `pulse_web.py` are locally unused, though imported by `pulse_server.py`. 

Status: Changes requested

## Turn 3 — Claude (adjudication)

Every checkable claim was tested against the code before acting. **All four findings
fail verification.** No source change was made on the strength of any of them.

**F1 — "newlines collapse in `data-copy-text`" → WRONG.** Measured: 3 newlines emitted,
3 newlines after HTML attribute parsing, value intact and multi-line. The claim confuses
HTML5 with XML: XML normalizes whitespace in attribute values, HTML5 does not — the
tokenizer appends U+000A to the attribute value verbatim (WHATWG §13.2.5.34). Only
`\r\n`/`\r` are folded to `\n`, during input-stream preprocessing. Also note this
escaping predates GH-100; it would have been pre-existing even if real.

**F2 — "narrow viewports permanently clip the lead" → WRONG.** There is a
`@media (max-width: 1100px)` block at pulse_web.py:2364 that sets
`.health-banner { grid-template-columns: 1fr }` and
`.health-banner-lead { flex-wrap: wrap; white-space: normal }` — precisely the
mitigation the finding says is absent. Above that breakpoint the lead occupies an
`auto` grid column against a `1fr` items column, so the items column absorbs the
shortfall; the lead is the protected one.

**F3 — "aria double-read; pick one" → WRONG, and acting on it would break a feature.**
`aria-label` overrides element contents in the accessible-name computation, so the name
is announced once, not twice. More importantly the `.visually-hidden` span is not
decoration: `setCopyButtonStatus` (pulse_web.py:2557) queries and rewrites it on every
copy, so deleting it silently removes the screen-reader feedback path for copy
success/failure.

**F4 — "dead code: `forget_goal_completion` / `remember_goal_completion`" → WRONG**, and
self-refuting — the finding names `pulse_server` as an importer in the same sentence.
The import site carries a comment recording that ruff F401 once deleted these
re-exports and broke `pulse_server` (GH-5 Phase R).

### What the review DID produce

Verifying F3 required reading the copy-button JS, which surfaced a real defect neither
side had listed: three runtime labels still said **"collector"** —
`setCopyButtonStatus('Copied collector warning text', …)` and two siblings. That is the
exact wording GH-5 Phase 4b removed from this surface, and
`test_pulse_web_timestamp_disambiguation` could not see it: the guard asserts against
rendered HTML, and these strings are set by JavaScript at runtime. The static
`aria-label` was correct, so every assertion passed while one click restored the old
wording. Fixed, with a guard that reads the emitted script text (verified red against
the unfixed source).

### Not found by this review

The materially serious regression in the reviewed commit was that GH-100 deleted the
`<span class="synced">` element that `scripts/pulse_warning_watch.py` — a scheduled
launchd job — scrapes for its verdict, leaving it to log `page_state="unknown"` forever
while exiting 0. Found and fixed by the producer before this turn returned
(commit `e01f65b`).

Status: Approved with one producer-originated fix; no reviewer finding was actionable.
