# Relay — independent review of GH-100 (dashboard header status unification)

- **Producer:** Claude (rebalanceOS)
- **Reviewer:** CommandCode → deepseek/deepseek-v4-pro
- **Repo under review:** `/Users/noelsaw/Documents/GH Repos/rebalanceOS`, branch
  `feat/gh100-gh101-web-status-unification`
- **Commits:** `3019e9f`, `e01f65b`, `a720dfd`
- **Status:** Approved

This is a SECOND, independent review. A prior reviewer's four findings were all
disproved on verification, so treat that as evidence the surface has NOT been
adequately reviewed rather than that it is clean.

---

## The defect that was fixed

`scripts/pulse_web.py` rendered four status widgets in the dashboard header.
**Three of them read the same `HealthStatus` object**, a few lines apart in one
f-string:

| widget | function | text on a live screen |
|---|---|---|
| sync chip | `render_sync_chip(health_status, …)` | `Sync degraded · 5:16 PM · 22m ago` |
| health banner | `render_health_banner(health_status, …)` | `1 ERROR · 2 WARNINGS · 18 NOTICES` / `Attention needed` / `Last data ingest … 22m ago` |
| sidebar notices | `build_nav_data(notices=health_status.notices, …)` | `Notices · 21` |

`src/rebalance/health.py` already describes `HealthStatus` as *"The one verdict
every dashboard surface renders from."* The contract held in the data layer and
was broken three times in rendering.

## What changed

1. **`render_sync_chip` and `render_health_banner` deleted**, replaced by
   `render_status_bar` (`scripts/pulse_web.py`), which renders in **every** state
   including healthy. Rendering when healthy is what retires the chip — the chip
   existed only to have somewhere to say "last ingest" when nothing was wrong.

2. **`HealthStatus.problem_text`** (new, `src/rebalance/health.py`) counts errors
   and warnings only. `status_text` folds notices in whenever any exist, so the
   headline read "21 items need attention" when one did. Both `health.py:148` and
   `pulse_web.py` already describe notices as non-actionable.

3. **Hint no longer truncated.** `check.hint` is the only string that says what to
   DO. It was cut to 120 chars AND laid out in a non-wrapping flex row inside
   `overflow-x: auto`, producing `→ inspect tem…` on screen. Items now wrap, and
   `.health-banner-fix` got a CSS rule (it had none).

4. **`scripts/pulse_warning_watch.py` repointed.** It is a scheduled launchd job
   that SCRAPES the rendered page; it read the `<span class="synced">` element
   that change 1 deleted. Fed the real page it returned `page_state="unknown"` in
   every state while exiting 0. Its tests passed throughout because they embedded
   hand-typed HTML. They now parse `pulse_web.render_status_bar` directly.

5. **Copy-button runtime labels** stopped saying "collector" (wording removed in an
   earlier fix; these are set by JS so an HTML-asserting guard never saw them).

## Definition of Done for your turn

Read the actual code in the repo. Be adversarial and specific — cite `file:line`.
A finding with no file:line is not usable.

1. **Did deleting the chip lose information or behaviour?** The chip branched on
   `health.verdict`; the bar branches on `health.failures` / `health.warnings`.
   Name any input where these disagree. Check `compute_health_status` — it can
   return `WARN` for CLI compatibility in cases the docstring hints at.

2. **`problem_text` at the boundaries.** Zero problems, errors only, warnings
   only, both. It returns the literal string `"healthy"` as a sentinel — does any
   caller or downstream consumer break on that? Is excluding notices from the
   headline defensible, or does it hide something an operator needs?

3. **The scraper repoint (change 4) is the highest-risk edit.** It changes what a
   scheduled job records. Read `extract_banner_text` and `_PulseHTMLParser`
   closely. Is the new `page_state` mapping correct in every branch? An absent bar
   now returns `"unknown"` rather than `"healthy"` — is that right, and does any
   consumer of `temp/pulse-warning-watch.jsonl` depend on the old values?
   `sync_tone`/`sync_text` kept their names as persisted JSONL fields — is their
   MEANING now different in a way that silently splits historical records?

4. **Layout.** Hints are unbounded now. `.health-banner` still has
   `overflow: hidden` and `.health-banner-lead` still has `white-space: nowrap`.
   There is a `@media (max-width: 1100px)` block. Can a long hint, a large number
   of problems, or a width just above that breakpoint still produce clipped or
   broken output?

5. **Anything else actually wrong** — HTML escaping, the copy-button JS, dead CSS
   or dead code left behind, accessibility, or a test that cannot fail.

If you find nothing real, say so plainly. A fabricated finding is worse than none:
the previous review cost more to disprove than it returned.

Do **not** rewrite the feature. Report findings; the producer applies fixes.

---

▶ **TAKE YOUR TURN** — append your review below this line as
`## Turn 2 — CommandCode (deepseek-v4-pro)`, then set `Status:` to `Approved` if
you would ship this as-is, or `Changes requested` if not. Advisory only: report,
do not edit source files.

## Turn 2 — CommandCode (deepseek-v4-pro)

I read the three changed files (`src/rebalance/health.py`, `scripts/pulse_web.py`,
`scripts/pulse_warning_watch.py`) plus the watcher tests. The change is correct.
Four of the five DoD probes come back clean; one surfaces two trivial dead-code
leftovers, neither of which blocks ship.

**1. Chip → bar verdict divergence: none.** The old chip branched on
`health.verdict`; the bar branches on `health.failures`/`health.warnings`. Both
reduce to the same two buckets. `compute_health_status` (health.py:251-256)
derives `verdict` from `any(c.severity == ERROR)` → FAIL, else `any(c.severity ==
WARNING)` → WARN, else OK, over `problems`. `problems` holds only ERROR/WARNING
severity (NOTICE checks are routed to `notices`, health.py:246-249, and non-
attention OK checks are dropped by `_is_attention`, health.py:103-106). So
`failures` nonempty ⟺ verdict FAIL, `warnings` nonempty ⟺ verdict WARN, both empty
⟺ OK — `render_status_bar`'s `tone = "danger" if health.failures else ("warn" if
health.warnings else "ok")` (pulse_web.py:447) is the same classification, word
for word. The "WARN for CLI compatibility" case is a `Check(status=WARN,
severity=ERROR)` (e.g. doctor.py:471); those land in `failures` because the bar
filters on `severity`, and in `verdict == FAIL` for the same reason — no
disagreement. The only surface-level loss is the chip's *labels* "Sync degraded" /
"Sync warnings", and those were moods, not facts; the tone survives via the
`health-banner-danger`/`-warn` classes and the badge text.

**2. `problem_text` boundaries: correct.** Zero → `"healthy"`; errors only → `"N
error(s)"`; warnings only → `"N warning(s)"`; both → `"N errors · M warnings"`
(health.py:198-200). `"healthy"` as a sentinel is consumed literally, never as a
truthy/falsy branch: `render_status_bar` renders it into the badge
(pulse_web.py:481), and the scraper test asserts `sync_text == "healthy"`
(test_pulse_warning_watch.py:75). No caller breaks on it. Excluding notices from
the headline is defensible — the sidebar carries its own `Notices · N` count
(build_nav_data, pulse_web.py:1711-1716) and the copy button uses `bucket_text`,
which keeps them (pulse_web.py:473).

**3. Scraper repoint: sound.** `extract_banner_text` maps the bar's tone class
directly: `warn`/`danger` → `"warning"`, `ok` → `"healthy"`, else `"unknown"`
(pulse_warning_watch.py:208-213); an absent bar is `"unknown"` (line 191-196).
Absent-bar → unknown rather than healthy is correct and well-pinned: the bar now
renders in every state, so absence means the page failed, and calling that
"healthy" would be the watcher inventing the all-clear it exists to disprove
(test_pulse_warning_watch.py:79-90). `sync_tone`'s vocabulary is unchanged
(`ok`/`warn`/`danger`, same three values as the old `.synced-{tone}` chip), so no
historical split there. `sync_text`'s *meaning* does change — it was the chip's
sentence ("Sync degraded · 5:16 PM · 22m ago"), now it is the badge's compact
verdict ("1 error · 2 warnings") — but this is a log-only artifact: nothing in
`src/` reads `temp/pulse-warning-watch.jsonl` programmatically (grep confirms the
only references are the watcher itself, its plist, and the scheduler policy doc),
and the docstring records the keep-the-names decision explicitly
(pulse_warning_watch.py:107-109). The fingerprint flips once on first post-update
run, which is the expected transition, not a silent split. The badge parser is
correct: the badge span is a text-only leaf, and the copy button/svg live outside
it, so `_badge_depth` collects exactly the verdict string.

**4. Layout: sound.** The clipping Agy flagged is real-but-mitigated: the
`@media (max-width: 1100px)` block exists at pulse_web.py:2364 and sets
`.health-banner { grid-template-columns: 1fr }` + `.health-banner-lead {
flex-wrap: wrap; white-space: normal }` (lines 2377-2378). Above the breakpoint,
the lead is the protected `auto` column while the `1fr` items column absorbs the
shortfall, and `.health-banner-items` carries `min-width: 0` (line 1914) so it
shrinks rather than overflows against `.health-banner`'s `overflow: hidden`. A
long hint wraps (`white-space: normal` + `overflow-wrap: anywhere` on
`.health-banner-item`, lines 1925-1926), so "→ inspect tem…" is gone; the
unbounded hint can only grow the bar vertically. One cosmetic nit, non-blocking:
`.health-banner-item` keeps `border-radius: 999px` (line 1922), so a hint long
enough to wrap into several lines renders as an elongated rounded shape. Ugly, not
clipped or broken.

**5. Minor dead code (advisory, no change required to ship).**
- `.ok-dot` CSS (pulse_web.py:1763) is orphaned: `render_sync_chip` — the only
  emitter of `<span class="ok-dot">` — is deleted, and a repo-wide grep finds no
  remaining producer. (`@keyframes glow-ok` is *not* dead; `.health-dot` at line
  1764 still consumes it.)
- `HealthStatus.status_text` (health.py:174-183) now has no production caller.
  The header uses `problem_text`; the copy button and CLI JSON use `bucket_text`.
  `status_text` survives only in tests (test_health.py, test_health_buckets.py).

Neither finding is a correctness or behavior defect; they are removable at the
producer's leisure.

**Verdict: Approved.** The unification is correct, the verdict/bucket split is
structurally equivalent to what it replaced, and the high-risk scraper repoint is
the one change whose tests now read the real render instead of a stale fixture —
which is the right kind of regression guard for exactly the failure mode that
prompted this review.

## Turn 3 — Claude (adjudication)

**Both findings verified true and both are fixed.** The reasoning on the four clean
probes was also checked and holds.

**`.ok-dot` orphaned → CONFIRMED, removed.** The only emitter was `render_sync_chip`.
The rule at pulse_web.py:1763 survived because the earlier deletion took the
`.synced .ok-dot` descendant rules and left the standalone animation rule behind. The
accompanying observation that `@keyframes glow-ok` is NOT dead — `.health-dot` still
consumes it — was correct and stopped a wrong deletion. Remaining `web/pulse.html`
hits are the gitignored generated artifact and clear on the next render.

**`status_text` has no production caller → CONFIRMED, removed.** The only non-test
references were its own definition and a docstring. `pulse_web.py:344/355` is a
*parameter* of that name in `_health_banner_copy_text`, which line 473 feeds from
`bucket_text` — so the property itself was dead. Deleted rather than kept: three
near-identical summary properties (`status_text`, `bucket_text`, `problem_text`) is a
coin-flip at every call site, and the hybrid existed only because one property was
being asked to serve two callers with opposite requirements.

Its tests were RETARGETED, not deleted — the bucket-summarisation behaviour is still
worth pinning, it just belongs to `bucket_text` now, with new cases for the
headline/summary split.

Removing it surfaced one thing neither review caught: `status_text` returned only the
DOMINANT bucket when no notices were present, so a system with one error and one
warning displayed "1 error" and the warning vanished from the headline entirely.
`problem_text` lists every non-empty problem bucket. `test_fail_dominates` was pinning
the hiding behaviour and now pins the disclosure.

**Layout nit (`border-radius: 999px` on a multi-line item) — accepted, not fixed.**
Correct, cosmetic, and only reachable with an unusually long hint. Recorded rather than
churned.

**On the verification quality.** This turn cited file:line for every claim and its
reasoning was independently checkable — including the `glow-ok` caveat, which prevented
a wrong deletion. That is a materially different standard from the first GH-100 review,
whose four findings all failed verification and two of which would have caused
regressions. Noting it because it bears on whether these reviews are worth their cost:
this one was.

Status: Approved — both findings fixed, one nit accepted, 1991 tests passing.
