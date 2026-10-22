---
gh_issue: 348
source: https://github.com/HiQS-Labs/rebalanceOS/issues/348
title: "Retire ROADMAP.md: make the RELEASES SQLite ledger the only work ledger (with #329 as phase 1)"
status: "Active — plan QA Approved (codex r2); Phase 1 (#329) committed; Phase 2 next"
created: 2026-10-21
updated: 2026-10-21
owner: noel
doc_type: refactor
goal: >
  Stop hand-editing ROADMAP.md. Install the current XYZ Forge RELEASES overlay (#329), migrate
  releases.db, import the final ROADMAP.md rows, and switch every reader/writer to the DB the way
  XYZ Forge already did for itself (GH-269), so the ledger can no longer drift from GitHub state.
---

# GH-348 — Retire ROADMAP.md for the RELEASES SQLite ledger

## Status

| What was just completed | What's next |
|---|---|
| Plan QA Approved (codex r2, attested). Phase 1: Forge 1573dd4b7 app + #322 delta, schema v5→v9, check warning set unchanged, reconcile-state dry-run exit 0. | Phase 2 (#348): de-key/key, final import, flip. |

## Tracked issues

| Issue | Scope | Depends on | Rating (P/S/A/E) | State | PR |
|---|---|---|---|---|---|
| [#329](https://github.com/HiQS-Labs/rebalanceOS/issues/329) | Phase 1 — current Forge RELEASES overlay via the supported vendor path; `releases.db` migrate; `.xyz-pin` bump | — | 75/60/50/45 (provisional, from the issue, 2026-10-13) | recon | — |
| [#348](https://github.com/HiQS-Labs/rebalanceOS/issues/348) | Phase 2 — final import, flip readers/writers to the DB, rewrite governance docs, retire the file | #329 | 70/55/50/25 | recon | — |

## Why

`ROADMAP.md` is the source of truth; `releases.db` mirrors it one way (`releases roadmap sync`). Nothing
reconciles the markdown against GitHub, so it drifts (#345: #325/#334/#336/#338 listed "In progress"
after merge), and this repo's old `releases_app.py` lacks the verbs the governed workflows need (#329).

## Rating rationale (2026-10-21)

- **#348 — 70/55/50/25.** Severity 55: ledger drift misleads planning and agents (ROUTER step 4 sends
  every session to "In progress"), no data loss. Priority 70: user-requested now; every merge adds drift.
  Appeal 50 (neutral; no user score). Effort 25: ~10 tools/tests/CI plus ~8 governance docs plus a migration.
- **#329 — 75/60/50/45** kept as filed (provisional): blocks `/merge-cleanup` and `/start-task` ledger steps.
- **Recurrence (last 14 days vs prior 14):** 2026-10-07..21 — #345 roadmap drift (1 incident, 4 rows),
  #327 batch ledger-gate failure (1); 2026-09-23..10-06 — none found in issues. Trend: low count, unknown
  beyond issue search.

## Key concepts

- Forge prior art: `XYZ-forge` 9e5c79979 (GH-269) deleted its `ROADMAP.md` and made `pdda.sh`,
  `releases_app.py`, `wave_reconcile.py` and the marathon planner read `releases.db` when the file is absent.
- Writers after the flip: `releases roadmap add / update / move / rate / repoint` only.

## Recon summary (full map: [TESTS-RESULTS/2026-10-21+GH-329/RECON.md](../../TESTS-RESULTS/2026-10-21+GH-329/RECON.md))

- Root `utils/py/releases_app.py` is a stale fork of Forge (schema v1–5, `roadmap {sync,list}`). It is what the
  governed skills run: merge-cleanup's `tool_path()` and start-task resolve the root copy before `.xyz/`. `.xyz/` is
  gitignored (`.gitignore:75`), so task clones and CI never have it. `xyz-vendor.sh` writes only `.xyz/`, so the
  supported vendor path **cannot** fix the root copy; #329 needs the root file re-vendored in a tracked commit.
- Forge `origin/development` @ `1573dd4b7` is schema v1–9. Its `migrate` takes this repo's `releases.db` from v5 to v9
  cleanly on a copy, and `check` stays at the same 9 warnings before and after.
- Forge lacks one local fix: the #322 `_is_single_values_tuple` guard in `parse_dump`. Measured: Forge's copy fails 2 of
  6 tests in `tests/test_releases_app_dump_parse.py`.
- `roadmap_items` has 143 rows but only **6 carry `gh_number`**: Forge keys a row only from a `#N`/`GH-N` prefix at
  the head of the title, and this ledger's titles are `**Title** ([#N](url))`. `reconcile-state`, the closed-issue
  drift warning and every `--issue-num` edit depend on that key, and no verb can add a key to an existing row later.
- Four entries sit outside any `###` section and never reach the DB (lines 35-38: #300, #232, #230; line 230: GH-23).
  There are two `### In progress` headings.
- Readers that break when the file disappears: `pdda.sh roadmap-coverage` (hard ERROR), `prior-art-check.sh` (silent
  skip), `scripts/check_doc_links.py` (8 broken links, CI red). Forge `pdda.sh:326-409` already has the DB branch for
  coverage. `src/rebalance/ingest/releases_scan.py` reads `releases.db` directly and is unaffected.
- `wave_reconcile.py` is a 2.5K-line harness tool that imports `harness_paths` and calls `ci-route.sh`, the marathon
  planner, timeline and leaderboard through `harness_tool()`. It belongs in the machine-local `.xyz/` harness, not in
  this repo's tracked `utils/py`.

## Preflight bet check

- **Outcome sought:** the work ledger cannot silently disagree with GitHub, and the governed landing tools run here.
- **Smallest bet:** re-vendor one file, migrate the DB, re-key the existing rows, flip one marker, port one coverage
  hunk, and add one DB branch. **Not built:** no new ledger, no new CLI verb, no wholesale `utils/pdda` refresh from
  Forge, no root copy of `wave_reconcile.py`, no hosted `wave-reconcile.yml` workflow, and no rewrite of old-org URLs.
- **Alternatives rejected:**
  - Keep ROADMAP.md and add a drift linter. That keeps two sources of truth, and #345 shows the file drifts anyway.
  - Run `xyz-sync update` only. It touches `.xyz/` and leaves the tracked root fork stale (recon §0.3).
  - Refresh all of `utils/pdda` from Forge. That is a 632-line `pdda.sh` diff, and it would drop rebalanceOS-only checks.
- **Rollback:** revert the PR. Each phase is one commit that carries its app, `releases.db` and `releases.sql`
  together, so reverting restores a matching v5 app + v5 DB + ROADMAP.md. No external state is written.

## Plan

### Phase 1 — #329: current Forge RELEASES app + schema v9 (one commit)

1. Replace `utils/py/releases_app.py` with Forge `origin/development` @ `1573dd4b7` verbatim. Then re-apply the #322
   guard as the **single marked local delta**: the `_is_single_values_tuple()` helper plus the check in
   `parse_dump.try_stmt`, bracketed by a `# rebalanceOS local delta (#322)` comment. Correct the `pyproject.toml`
   ruff-exclude comment: the file is re-vendored by hand from a named Forge SHA, and xyz-sync never writes it.
   *Verify:* `pytest tests/test_releases_app_dump_parse.py` 6/6 (red control: Forge verbatim fails 2/6, measured);
   `python3 utils/py/releases_app.py roadmap --help` lists `reconcile-state`, `rate`, `add`, `update`, `move`.
2. `python3 utils/py/releases_app.py migrate`, then `check`.
   *Verify:* `schema_migrations` = 1–9; `check` = 0 failures, with the same warning set as before migration (record both);
   `roadmap reconcile-state --dry-run` exits 0.
3. Bump `.xyz-pin` to `1573dd4b7` and note that it now also records the root `releases_app.py` vendor SHA.
4. Commit the app, `releases.db`, `releases.sql`, `pyproject.toml` and `.xyz-pin` together.

### Phase 2 — #348: re-key, final import, flip (one commit for the flip)

5. Normalise ROADMAP.md before the last import:
   - Fold the three entries at lines 35-38 and the GH-23 entry at line 230 into their sections.
   - Merge the second `### In progress` block into the first.
   - Re-key titles with a one-off transform run from the session scratchpad. Nothing new is committed under `scripts/`
     or `utils/` (GH-241); the receipt keeps the exact transform source and command so it can be reproduced.
   - **De-key first (plan QA S2):** every existing title that starts `GH-N`/`#N` while the entry's own link belongs to
     a predecessor org loses its key, and the number moves into the title's tail (`One-shot sentinel prompt
     (predecessor GH-144)`). Known inputs: Hypercart #144/#96/#94/#93 (`ROADMAP.md:105,183-185`) and HiQS-Suite #5.
   - **Then key:** prefix `#N — ` to the bold title only when the entry's own first link is a
     `HiQS-Labs/rebalanceOS` issue URL for N.
   - **Never key** (plan QA S1): `HiQS-Suite` rows. Forge's identity check compares the URL owner exactly
     (`releases_app.py:5440-5455`, and `:5480-5484` also requires the API `html_url` to match), so a Suite-URL row would
     be keyed but could never be reconciled. Also never key Hypercart rows, umbrella or multi-issue entries, or any
     number more than one eligible entry would claim (e.g. #5's two PR entries).
   - These rows stay unkeyed with their URL and prose intact. The reasoned exception: reconcile-state and the drift
     warning do not cover them (old, mostly closed history).
   - URLs are never rewritten.
   *Verify:*
   - Per-entry assertions in the receipt: each keyed row's `gh_number` equals the number in its own HiQS-Labs URL.
   - The four Hypercart rows and the Suite #5 row have NULL `gh_number` and the original URL/prose.
   - Current #144 is keyed 144.
   - `roadmap sync` succeeds with no duplicate-key refusal, and the 4 previously dropped entries are present
     (total rows = 143 + 4).
   - `roadmap reconcile-state --dry-run` reports every keyed row as a valid identity.
6. In **one commit**: add `ROADMAP_SOURCE=releases` to `.pdda-mode`, delete `ROADMAP.md`, and commit the post-sync
   `releases.db`/`releases.sql`.
   *Verify:* `roadmap sync` prints the releases-mode skip line; `roadmap list` shows every row.
7. Port Forge `pdda.sh`'s **whole** `check_roadmap_coverage` function (`:326-409`, plan QA S3). Both loop call
   sites (Forge `:378-379`, `:396-397`) replace this repo's file-only `grep -Fq "$rel" "$PDDA_ROADMAP"`
   (`utils/pdda/pdda.sh:347,365`). Also port the GH-492 closed-issue drift block (`:676-700`). Unrelated
   rebalanceOS-only functions stay as they are.
   Give `utils/pdda/prior-art-check.sh` a read-only `sqlite3 -readonly releases.db` branch that selects
   `section='In progress'` titles when ROADMAP.md is absent.
   *Verify:* `pdda.sh roadmap-coverage` error count is ≤ today's 9, with the 4 folded docs now covered. The drift block
   flags a seeded CLOSED issue whose row is not Completed (red control on a disposable copy). `prior-art-check.sh`
   finds a known in-progress term. Coverage controls run in a disposable clone: a non-empty DB-only pointer passes each
   loop (working and inbox), and removing that pointer adds exactly one uncovered-doc finding.
8. Fix the 8 links `check_doc_links.py` would break:
   - Live docs (`ARCHITECTURE.md:140`, `README.md:282`): point at the ledger docs.
   - Historical PROJECT docs: repoint the link target to the GitHub permalink of `ROADMAP.md` at the last commit that
     had it. The meaning is preserved, the text is unchanged, and no allowlist is added.
   *Verify:* `python3 scripts/check_doc_links.py` clean.
9. Rewrite the governance prose to name the DB and the CLI verbs, using Forge 9e5c79979 as the template:
   - `ROUTER.md`: startup step 4, prior-art check #2, the canonical rules.
   - `AGENTS.md`, `SOP.md`, `RELEASES.md`, `ARCHITECTURE.md`, `GUIDING-PRINCIPLES.md`, `README.md`.
   - `PROJECT/PDDA.md`, `utils/pdda/PDDA-INSTALL.md`.
   - Wording in `.claude/skills/rebalance` and `unlock-suite`.
   *Verify:* live governance prose (ROUTER/AGENTS/SOP/RELEASES/ARCHITECTURE/GUIDING-PRINCIPLES/README/PDDA docs and skills)
   names ROADMAP.md only in retirement notes. Intentional code references, such as legacy-mode branches and parser
   constants (`utils/pdda/pdda.sh`, `releases_app.py`), are listed and inspected separately.
10. Add one pytest, `tests/test_roadmap_retired.py`, mirroring Forge GH-269's invariants:
   - ROADMAP.md is absent and `.pdda-mode` carries the marker.
   - `roadmap sync` prints the skip line.
   - `roadmap list` succeeds.
   - `pdda.sh roadmap-coverage` runs with `PDDA_MODE=full` and the SUMMARY `errors=` count is pinned. Observe mode
     always exits 0, so it would prove nothing.
11. CHANGELOG entry, version bump per repo convention, and a ROUTER-visible note on how to park work now
    (`releases_app.py roadmap add --issue-url … --section 'Queue / parked intake'`).

### Verification (final)

- `pytest tests/ HiQS/tests` (full suite), `utils/pdda/pdda.sh run`, `python3 scripts/check_doc_links.py`,
  `python3 utils/pdda/check_script_inventory.py --check`, `releases_app.py check`, `rebalance doctor` (record; note
  pre-existing FAILs).
- **Smoke (disposable full clone):**
  - Main path: `roadmap add` a real open issue into the queue, `roadmap move` it to In progress, then `roadmap list`.
  - Adjacent path: re-run `roadmap sync` (skip, no change), and run `reconcile-state --dry-run` with a seeded
    closed-but-in-progress row.
  - Receipt goes to `TESTS-RESULTS/2026-10-21+GH-329/`.

## Non-goals and operator steps outside this PR

- `wave_reconcile.py` and the hosted `wave-reconcile.yml` from #329's acceptance list are **not** vendored into the
  tracked tree. They are harness tools with harness dependencies (recon §4). Refreshing the primary checkout's `.xyz/`
  with `xyz-sync update` is a machine-local operator step on each Mac, recorded in the PR body. Proposed change to
  #329's acceptance: `reconcile-state --dry-run` exits 0 from the root app; `wave_reconcile` runs from a refreshed
  `.xyz/`.
- 3-Eyes `com.neochro.hq-rollup` may read ROADMAP.md, but 3-Eyes is stood down (AGENTS.md). Check it, do not change it.
- Not done: refreshing `utils/pdda` wholesale, reformatting old-org rows, and fixing the 9 pre-existing coverage errors.

## Risks

- **One-way schema step:** an open branch still on the v5 app breaks on its next ledger write. Mitigation: there are no
  open PRs today (2026-10-21), and the releases-ledger merge rule (take development's db, re-run) still applies.
- **Silent loss after the flip:** with the marker set, any later markdown edit to a recreated ROADMAP.md is ignored.
  Mitigation: the file is deleted, and the pytest asserts it stays absent.
- **Re-key misattribution:** the transform keys only from the entry's own first link and skips duplicates. The
  receipt lists every keyed and skipped entry for review.
