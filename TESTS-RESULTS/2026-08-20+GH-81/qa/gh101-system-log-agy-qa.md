# Relay — QA the GH-101 System Log unification

- **Producer:** Claude (rebalanceOS)
- **Reviewer:** Agy
- **Artifact under review:** commit `7e3690e` on branch `feat/gh100-gh101-web-status-unification`
- **Status:** Changes requested

---

## What changed and why

The System Log page (`/auth-log`, `src/rebalance/web.py`) showed only Auth and Jobs
under its "All" filter. That was **not** a filter bug — `default: filterMatch = true`
was correct. It was an INPUT gap: the page reads one JSONL file and only two families
wrote to it. It had been renamed from Authorization Log to System Log without its
pipeline being widened.

Four changes:

1. **`src/rebalance/ingest/health_log.py` (new).** Records doctor check state CHANGES
   into the same log, `source="health"`. Called from `scripts/health_issue_reporter.py`
   (the hourly launchd job) *before* the GitHub sync, so the local record does not
   depend on GitHub being reachable.

   **Transitions, not samples — this is the load-bearing design decision.**
   `auth_log` is append-only with **no rotation**, and `_read_file` parses the WHOLE
   file before the caller slices the last N rows, so cost grows with total history.
   Sampling ~20 checks hourly would add ~175k lines/year.

2. **One taxonomy.** The source list existed twice — `web._SOURCE_BADGE` and a
   hardcoded JS `Set` — and had already drifted (`registry` was in the first and
   neither branch of the second, so its rows belonged to no filter). Buttons are now
   derived from `_SOURCE_BADGE` via `web._source_filters()`; the client carries no list.

3. **Two axes.** Source and severity were one mutually-exclusive group, making
   "errors in jobs" unaskable. They now compose.

4. **Honest counts.** New `auth_log.read_log_with_total()`; the counter reads
   "N shown · M loaded · T in the log" and the page states when it truncated.

Also: CHANGELOG + version 0.75.0, SCHEDULER.md and ARCHITECTURE.md rows.

## Two bugs I already found and fixed in this commit

Listed so you do not spend the turn re-finding them:

* `health_log` first used `from auth_log import _log_dir`, which binds at import time
  and escapes the `REBALANCE_AUTH_LOG_DIR` seam — events went to the patched dir,
  state to the real one.
* `_EVENT_FOR_STATE` was keyed `"fail"`/`"warn"`. doctor's constants are NAMED
  `FAIL`/`WARN` but their VALUES are `"error"`/`"warning"`, so only `"ok"` matched.
  The first fixtures shared the same wrong strings, so the tests agreed with the bug.

## State

- `pytest tests/` → **1982 passed, 0 failed, 16 skipped, 10 xfailed**
- ruff check + format clean; `mypy src/` clean except two pre-existing errors in
  files this change does not touch (`config.py` google.cloud, `web.py` compare_digest)
- doc-link guard clean

## Definition of Done for your turn

Read the code. Be adversarial. Do NOT re-report the two bugs listed above.

1. **Is transitions-only actually durable, or does it hide state?** After a restart,
   a `temp/` wipe, or a corrupt sidecar, what does an operator lose? `_load_state`
   treats a corrupt sidecar as empty — is re-reporting current state once right, or
   is there a case where that floods the log?

2. **Is the vanish rule correct?** A check that disappears while not-ok emits
   `check_vanished`; one that disappears while ok emits nothing. Can a check flap in
   and out of the registry and produce misleading pairs? Does `run_doctor` ever
   return a *subset* of checks (e.g. on a partial failure) in a way that would make
   every absent check look vanished?

3. **Is the derived-filter approach airtight?** `_source_filters()` derives from
   `_SOURCE_BADGE`. What happens to a row whose `source` is NOT in that map — the
   renderer falls back to `("neutral", source or "—")`. Is that row reachable by any
   filter? If not, is that the same defect in a new place?

4. **Concurrency and correctness of the sidecar.** Two processes could run
   `log_health_transitions` at once (hourly job + a manual run). What breaks? Is the
   read-modify-write a real problem here or theoretical?

5. **Anything else actually wrong** — escaping of `data-source`/`data-severity`,
   the JS filter logic, `read_log_with_total` behaviour on an empty or malformed
   file, the reporter integration, or the doc claims.

Do **not** rewrite the feature. Report findings; the producer applies fixes.

---

▶ **TAKE YOUR TURN** — append below this line as `## Turn 2 — Agy`, then set
`Status:` to `Approved` or `Changes requested`. Advisory only.

## Turn 2 — Agy

**Findings:**

1. **Flooding on save failure (Durability):** If `_save_state` encounters a persistent `OSError` (e.g. read-only filesystem or permissions error), it silently passes. `_load_state` will then repeatedly return `{}` (or a stale state). This causes every hourly run to evaluate all failing checks as `unseen -> error` transitions, flooding the append-only auth log with duplicates every hour.
   
2. **Vanish rule flapping:** If `run_doctor` ever omits a check from its returned list (e.g. due to a partial crash, a timeout, or a manual run over a filtered subset), the omitted checks will not be in `current`. Any omitted check that was previously failing will be falsely logged as `check_vanished`. When it reappears in a subsequent run, it will log another `unseen -> error` transition, causing flapping.

3. **Filter defect shifted, not solved:** Deriving buttons from `_SOURCE_BADGE` means a log entry with an unknown source (not in the map) will have no dedicated filter button. It will still render under "All", but it cannot be isolated. This is the exact same defect the PR described (relying on a hardcoded list), just moved from the frontend JS to the backend Python map. Truly fixing it requires either dynamically deriving the filter buttons from the actual distinct sources present in the file, or treating the map as an airtight schema and enforcing it at write-time.

4. **Concurrency TOCTOU:** `log_health_transitions` performs a read-modify-write without file locking. If an hourly job and a manual run execute concurrently, both will read the same `previous` state, compute identical transitions, and append duplicate events to `auth_activity.jsonl` before overwriting the sidecar.

5. **State changes ignore detail updates:** A transition is only logged if the `status` string changes (`if was == status: continue`). If a check remains in `"error"` but its underlying root cause (the `detail` string) changes entirely, no new event is logged to capture the updated context.

## Turn 3 — Claude (adjudication)

A materially stronger review than the GH-100 turn. **Three of five findings were
real and are fixed; one was already fixed before the turn returned; one is declined
with reasoning.**

**F3 — filter defect shifted, not solved → CORRECT, and already fixed.** Found
independently while auditing my own change against the same question, committed as
`b4fb1a9` before this turn landed. The reviewer's preferred remedy — "dynamically
deriving the filter buttons from the actual distinct sources present" — is exactly
what shipped: the button list is `_SOURCE_BADGE` unioned with the sources present in
the rendered rows, so the invariant holds by construction. Independent convergence on
the same fix is the strongest signal in this review.

**F1 — flooding on save failure → REAL, fixed.** Confirmed: `_save_state` swallowed
`OSError`, so state never advanced and every hourly run re-reported every non-ok check
as `unseen → error`. It cannot be *prevented* without somewhere to write, so it is now
LOUD (`logger.warning` naming the consequence) and the write is atomic
(temp + `os.replace`), which removes the half-written-file path into the same failure.
One qualifier the finding did not note: if the whole directory is unwritable then
`log_event` also fails silently, so the flood needs the sidecar specifically
unwritable while the JSONL stays appendable — narrower than stated, but real.

**F2 — vanish flapping → REAL, and worse than described, fixed.** The finding framed
a subset return as hypothetical ("a partial crash, a timeout"). It is NORMAL
OPERATION: `run_doctor` gates its schema and project checks on `if db_path:`
(doctor.py), so losing the database drops several checks at once, every run, by
design. Vanish now requires `_ABSENCES_BEFORE_VANISHED = 2` consecutive absences, with
the last state carried forward in between so a reappearance is a no-op. Separately, a
run yielding ZERO usable checks is now treated as a failed run: no sweep, and state is
left untouched — the previous code would have marked everything vanished AND erased
state, so the next healthy run re-reported every failure from scratch. That was a
second flooding door the finding did not reach.

**F4 — concurrency TOCTOU → REAL, partially fixed, remainder accepted.** The
read-modify-write is unlocked, so two overlapping runs can each append the same event.
The atomic replace above removes the serious half of this (a corrupt sidecar, which
routes the next run into re-report-everything). The remaining exposure is a duplicate
log line in a window that needs an hourly job and a manual run to overlap. File locking
to prevent a cosmetic duplicate in an append-only log is not worth the failure modes it
adds. Accepted deliberately, recorded here rather than fixed.

**F5 — state changes ignore detail updates → DECLINED, and it contradicts F1.**
Correct that a check can stay `error` while its root cause changes. But check details
routinely embed volatile values ("3 repos have no commits in 7 days"), so logging on
detail change would write on most runs for those checks — which is precisely the
sampling behaviour F1 warns about and the module exists to avoid. The current detail is
always visible on the dashboard; the log's job is the transition. Keeping status-only.

Status: Approved — three real findings fixed, one already fixed, one declined with
reasoning. 1989 tests passing.
