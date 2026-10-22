# GH-348 / GH-329 recon — retire ROADMAP.md, RELEASES SQLite ledger only

Read-only recon, 2026-10-21. Nothing in either repo was modified. All write-capable commands ran
only against `git archive` / `cp` copies under `$TMPDIR/gh348/` (temp git repo `tree/`).

- Task clone: `<GH Repos>/rebalanceOS-gh329-retire-roadmap-md-2026-10-21`
  — **HEAD is now `7cfb820`** ("chore(GH-348): capture and park #348 with #329 as phase 1"), one commit past the
  `44c318d` the brief named. Row counts below are from `7cfb820`.
- Forge: `origin/development` = `1573dd4b7` (2026-10-20). Read only via `git show` / `ls-tree`.
- Primary rebalanceOS checkout (`<GH Repos>/rebalanceOS`) read for its `.xyz/` only.

Legend: **[V]** verified by reading or running on a copy. **[I]** inferred.

---

## 0. Premise corrections (read these first)

1. **`.xyz/` is not in the task clone and never will be.** `.gitignore:75` has `.xyz/`, so `.xyz/` is machine-local.
   It exists only in the primary checkout (`rebalanceOS/.xyz/VERSION`: `source_commit=34a3056…`,
   `vendored_utc=2026-09-15T23:26:51Z`, `tier=2`). Task clones, landing clones and CI do not have it. [V]
2. **The root `utils/py/releases_app.py` is what governed workflows run, not `.xyz/`.** The global skills resolve the
   tool clone-first: `<claude skills>/merge-cleanup/scripts/ledger_merge.py:262-272` `tool_path()` tries
   `<root>/utils/py/releases_app.py`, then `<root>/.xyz/utils/py/…`, then the same two under the primary checkout.
   `start-task/SKILL.md:220,369` hard-codes `python3 utils/py/releases_app.py roadmap update|rate …`. The root copy
   lacks `update`/`rate`/`move`/`add`/`reconcile-state` and is at schema v5. That gap explains #329's "ledger gate
   fails here". [V for resolution order; I for the #329 causal link]
3. **`xyz-vendor.sh --with-releases` never touches `utils/py/` at the repo root.** It only rewrites `.xyz/` (§4). So
   "installing the overlay" through the supported vendor path **cannot** fix the root fork. #329 needs an explicit
   re-vendor of the root file (copy from Forge `origin/development`) in a tracked commit. [V]
4. `utils/pdda/pdda-check-roadmap*.sh` **does not exist** in rebalanceOS (or Forge). The roadmap checks are the
   `roadmap` and `roadmap-coverage` subcommands inside `pdda.sh`. [V]

---

## 1. The two `releases_app.py` copies and their callers

| Copy | Size | Schema registry | `roadmap` verbs |
|---|---|---|---|
| root `utils/py/releases_app.py` (tracked) | 188K | v1–5 (`:853-859`) | `sync, list` |
| primary `.xyz/utils/py/releases_app.py` (Forge 34a3056, gitignored) | 342K | v1–8 (`:1016`) | Forge set as of 09-15 |
| Forge `origin/development` | 364K | v1–9 (`:1026-1036`) | `sections, sync, reconcile-state, list, render, add, rate, repoint, update, move` |

### Who calls which [V]

**Tracked callers that name the root copy (6):**
1. `pyproject.toml:102-107`: ruff exclude. The comment says it is "Vendored verbatim from XYZ-forge … the next `xyz-sync` would silently revert the fix". That is **false today**: xyz-sync/xyz-vendor never write it.
2. `utils/pdda/script_inventory_baseline.json:87`: inventory ratchet entry, needed if the file is deleted or renamed.
3. `tests/test_releases_app_dump_parse.py:17`: imports root copy; tests `parse_dump` / `_sql_str` (#322 fix).
4. `ARCHITECTURE.md:290`: subsystem table row.
5. `utils/py/releases_cycle.py:46`: **does NOT use the root copy**. It loads `<harness_root>/utils/py/releases_app.py`
   (`load_work_evidence`, a Forge-only function; root copy has 0 occurrences). harness_root comes from
   `utils/daily_work_synthesis.py:211-234` config `xyz_harness_root`. This caller is the XYZ harness (Forge/.xyz).
6. `tests/test_daily_issue_status.py:61`: fixture fakes a *harness* `releases_app.py` (pairs with #5).

**Untracked/global callers (resolve to the ROOT copy first):** merge-cleanup (`merge_cleanup.py:426,498,655,786`,
`ledger_merge.py:276,314`), start-task (`SKILL.md:220,369`). [V]

**Not callers:** `.github/workflows/ci.yml` (no releases/pdda.sh step), `.githooks/{pre-push,post-merge}` (0 refs),
`src/rebalance/**` (reads `releases.db` directly via sqlite, see §3), AGENTS/ROUTER/SOP/RELEASES.md (no CLI commands),
`.claude/skills/{rebalance,unlock-suite}` (prose only). [V]

**Count: 6 tracked references + 2 global skills. Only 2 tracked consumers execute the root copy:
`test_releases_app_dump_parse.py` and the ruff/inventory config.**

### Fork or rebalanceOS-specific? [V]
It is a **stale fork of Forge** (same GH-32/GH-69 docstring lineage), with 4 commits of local history:
`4cb7c53` adopt (08-24), `217f29b` org-rename fix, `dd77b6a` GATEWAY-OK exemptions, `9296b0a` #322 multi-line
INSERT parse fix (10-04). Function-level diff against Forge dev shows 4 root-only defs: `_is_single_values_tuple`
(#322), and `gen_marker`/`render_ledger`/`write_drift_report` (the `gen` verb, which Forge retired in GH-568). Forge has
178 defs vs root 105.
- #322 fix: Forge already has `INSERT_RE … re.S` (`forge releases_app.py:5951`) plus a buffered statement parser, and a
  comment at `:144-150` describes a downstream fork that "re-derived an INSERT_RE fix that already existed here". The
  root-only `_is_single_values_tuple` guard is the one thing Forge lacks. **Re-run `tests/test_releases_app_dump_parse.py`
  against the Forge copy before deleting the guard** [I: likely passes, not run].
- `gen` / `RELEASES.generated.md`: no tracked caller found in rebalanceOS (`.gitignore:119` ignores the output). [V]

### Roadmap/sync behaviour difference [V]
- Root `cmd_roadmap_sync` (`:2779`) mirrors ROADMAP.md one way, with no releases-mode guard and no empty-parse refusal.
- Forge `cmd_roadmap_sync` (`:4167-4185`) **no-ops when `.pdda-mode` contains `ROADMAP_SOURCE=releases`**, refuses
  `rule=roadmap-missing` when ROADMAP.md is absent in legacy mode, and refuses a 0-entry parse (`roadmap-empty-parse`,
  `--allow-empty`). The Forge parser (`:3480`) handles link-style bullets and any-org URLs (GH-349).
- Forge's `releases_app` lazily imports `work_connectors` (`:1622-1640`, swallowed, prints "work connectors skipped")
  and `harness_paths` (only for `jog`, `:4494`). Neither ships in rebalanceOS `utils/py/`. That leaves stderr noise
  only. Set `XYZ_WORK_CONNECTORS=0` or accept the noise. [V ran it]

---

## 2. Schema

- rebalanceOS `releases.db` (copy, HEAD 7cfb820): `schema_migrations` = **1,2,3,4,5**; `settings.generation=82`,
  `enforcement=lenient`, `repo_slug=rebalanceOS`; journal_mode=delete. [V]
- Forge dev expects **1–9** (6 jog_queue/GH-259, 7 updated_at on all tables/GH-355, 8 work_events + connector_cursors/GH-549,
  9 GH-646 accepted-start). The vendored `.xyz` is v8. [V]
- **Forge `migrate` closes the gap cleanly** on a copy: `check` before = clean (0 failures, 9 warnings: 2 stale MIG
  refs, 2 past-target drafts, 10 grandfather entries pending); `migrate` printed "migrated releases.db to schema version
  9 (applied 6, 7, 8, 9; generation 84)"; `check` after = same 9 warnings. Diff: releases.db 385K→438K,
  `releases.sql` +256/-251 lines. [V]
- The root v5 app on a v9 DB: **[I] it will likely refuse or misbehave**, because its registry never claims more than
  it defines. In any case the migration is one-way for the old app (schema_migrations rows 6-9 + new tables). That
  makes the "flip the app" and "migrate the DB" a single commit.

### `roadmap_items` now (HEAD 7cfb820) [V]
| section | rows |
|---|---|
| Completed | 42 |
| In progress | 47 |
| Queue / parked intake | 49 |
| Superseded | 4 |
| Deferred · vision | 1 |
| **total** | **143** |

- `gh_number` populated on **6/143**, `issue_url` on 6, `doc_path` on ~136. The 6 keyed: #5 (HiQS-Suite), **#93, #94,
  #96, #144 (old org Hypercart-Dev-Tools/rebalance-OS)**, #330 (HiQS-Labs). After a Forge `roadmap sync` on the
  migrated copy: "143 in ROADMAP.md → +0 added, ~7 updated, -0 removed, 136 unchanged" and **still 6 keyed**. Most
  entries are `**Title** ([#N](url))`, and Forge keys from the *title* (`GH-N`/`#N` prefix), not from a trailing link. [V]
- **ROADMAP.md content the parser drops** [V]: lines 35-38 (#300 Luna trial, #232 CLIO follow-up, #230 CLIO replay) sit
  under `## Ledger` before the first `###`, and line 230 (GH-23 publication durability) sits in `## Entry format`. Forge
  pdda coverage against the DB flags exactly these 4 extra docs (13 errors vs 9 with ROADMAP.md present). ROADMAP.md
  also has **two `### In progress` headings** (lines 40 and 116; the second holds old-org #217/#218/#219/#193).

---

## 3. Live ROADMAP.md readers and writers (excluding PROJECT/TESTS-RESULTS/relay-system/marathon-system/CHANGELOG)

| File:line | What it does | If ROADMAP.md is absent | Forge dev equivalent with DB branch? |
|---|---|---|---|
| `utils/pdda/pdda.sh:264-321` `check_roadmap` | pointer-only lint (checkboxes, Checklist headings, ≤200 lines, ≤25 headings) | info "not found; nothing to check", exit 0 [V] | same code; DB not needed |
| `utils/pdda/pdda.sh:324-376` `check_roadmap_coverage` | every 2-WORKING doc and 1-INBOX GH doc must be `grep -F`'d in ROADMAP.md | **ERROR "ROADMAP.md not found"** [V ran on copy] | **Yes**, `forge pdda.sh:326-372`: releases-mode or absent file → reads `roadmap_items.doc_path`+`raw_text`. Adoptable verbatim [V ran it: works, 13 errors] |
| Forge-only `pdda.sh:676-700` issue-doc-sync §3 | warns when a CLOSED issue's row is not Completed (exactly the #345 drift) | n/a in reb | **Yes**, gated on `ROADMAP_SOURCE=releases` and uses `gh_number` only |
| Forge-only `pdda.sh:1293` | adds ROADMAP.md/RELEASES.md to shipped-doc ref exemptions in releases mode | n/a | yes |
| `utils/pdda/pdda-doc-ready.sh:152-154` | LLM rubric review of ROADMAP.md | skipped (`[ -f ] &&`) [V] | identical (0-line diff) |
| `utils/pdda/pdda-edit-doc-hook.sh:38-47` | on Edit of ROADMAP.md, runs `pdda.sh roadmap` | never fires [V] | identical |
| `utils/pdda/pdda-lib.sh:11,449` | comments only | — | Forge differs by 15 lines (RELEASES.md optional, GH-568) |
| `utils/pdda/prior-art-check.sh:57-68` (**reb-only**) | greps `### In progress` section for concept terms | **silently skips**, so prior-art check #2 is lost [V] | **No Forge equivalent.** Needs a local `sqlite3 -readonly … WHERE section='In progress'` branch |
| `utils/frontdoor-check.sh:22,32,253,261` | `:(exclude)ROADMAP.md` pathspec in secret/path scans | harmless [I] | — |
| `scripts/check_doc_links.py` (CI `ci.yml:56-70`) | link checker, no allowlist | **8 broken links → CI red** [V ran on copy]: `ARCHITECTURE.md:140`, `README.md:282`, `PROJECT/2-WORKING/MARATHON-PLAN-2026-09-06.md:22,168`, `PROJECT/4-MISC/ARCHIVED-PREDECESSOR/2-WORKING/GH-102-…md:373,654`, `…/MARATHON-PLAN-2026-07-25.md:29,121` | — |
| `tests/test_doc_links.py:7,38` | unit test of the code-span skip using a ROADMAP row template string | unaffected (string fixture) [V] | — |
| `src/rebalance/ingest/releases_scan.py:131-143` | reads `roadmap_items` from **releases.db** (not ROADMAP.md); optional columns via PRAGMA; refuses WAL | unaffected; schema-tolerant [V code read; I runtime] | — |
| `.claude/skills/rebalance/SKILL.md:164`, `unlock-suite/SKILL.md:137` | prose ("ROADMAP prose may be stale") | wording only | — |
| `.xyz/utils/marathon-plan.sh` → `_marathon_plan.py:773-798` (vendored, primary only) | planner: ROADMAP.md, else `releases.db roadmap_items` | already DB-capable in the 34a3056 vendor [V] | yes |
| `.xyz/utils/py/wave_reconcile.py` | post-merge `roadmap sync` | vendored copy has `ROADMAP_SOURCE` support [V] | yes |
| Governance prose: `ROUTER.md:14,37,48,57-59,127`; `AGENTS.md:3`; `ARCHITECTURE.md:3,140`; `GUIDING-PRINCIPLES.md:69,88`; `README.md:14,282`; `SOP.md:15`; `utils/pdda/PDDA-INSTALL.md` (7 refs) | startup step 4 "Read ROADMAP.md", coverage rule, prior-art #2 | doc rewrite | Forge 9e5c79979 rewrote AGENTS/ROUTER/SOP/PROJECT/PDDA.md |
| `ROADMAP.md:222-226` "Entry format" | documents the planner's parse contract | goes away with the file | — |
| `utils/3-eyes/registry/catalog-notes.toml:146` `com.neochro.hq-rollup` "HQ ROADMAP rollup → Obsidian" | machine-local launchd job, status `to-adopt` | **[I] may read ROADMAP.md across repos.** Out of tree, check before deleting | — |

### Is rebalanceOS `utils/pdda` vendored Forge PDDA or a fork? [V]
It is an **installed copy of the PDDA runtime, now stale, with local extensions**. Forge dev `utils/pdda/PDDA-SOURCE.md`
now says PDDA is a subsystem of XYZ Forge (canonical: Forge `utils/pdda/`; migration decision Forge #649). Compared with
Forge dev:
- identical (0-line diff): `pdda-catchup.sh`, `pdda-doc-ready.sh`, `pdda-edit-doc-hook.sh`, `pdda-gh-refresh.sh`, `pdda-stop-doc-health.sh`
- drifted: `pdda.sh` (632 diff lines; reb lacks the GH-243/269 DB branch, GH-492 roadmap drift, comment-ref checks and `check_marathon_qa`; reb-only `check_banned_imports`), `pdda-lib.sh` (15), `PDDA-INSTALL.md`, `PDDA-SOURCE.md`
- **rebalanceOS-only** (keep): `prior-art-check.sh`, `check_banned_imports.py`, `check_machine_paths.py`, `check_near_duplicates.py`, `check_read_layer.py`, `check_script_inventory.py`, `pdda-leaf-ingest-guard.py`, the `*_baseline.json` files (all CI-gated in `ci.yml:41-54`).

A wholesale pdda.sh refresh from Forge is bigger than this task and drags in `check_marathon_qa` and other changes. The
smallest move is to **port the `check_roadmap_coverage` hunk** (Forge `pdda.sh:326-372`) and optionally the GH-492
drift block (`:676-700`).

---

## 4. `.xyz/` contents and what `xyz-vendor.sh --with-releases` writes

- Primary `.xyz/` already holds `utils/pdda/` (pdda.sh 86K) and `utils/py/{releases_app.py, releases_cycle.py,
  wave_reconcile.py, _marathon_plan.py}`, plus `RELEASES-DB-FAQS.md` (tier 2). The vendor is **1,416 Forge commits
  behind** dev (34a3056 → 1573dd4b7) and contains GH-269 (ancestor check passed). [V]
- `xyz-vendor.sh` (Forge dev) [V]:
  - `:66-71`: **auto-enables Tier 2 when `releases.db` exists at the target root** (sticky). `--with-releases` is
    therefore implicit for rebalanceOS.
  - `:433` `RELEASES_OVERLAY="utils/py/releases_app.py utils/py/releases_cycle.py utils/releases-merge-resolve.sh utils/release-lanes.sh utils/timeline relay-automation/xyz-releases-onboard.sh"`.
    Tier 1 deletes these from the stage; Tier 2 keeps them and copies `RELEASES-DB-FAQS.md`.
  - `:437-503` `materialize_vendor`: stages `relay-automation bin src utils test skills` into `.xyz.tmp.$$`, writes
    `.xyz/package.json` and `.xyz/VERSION`, preserves `XYZ_RUNTIME_PATHS` (`:236`: relay-system .tick
    .relay-driver.lock XYZ.json XYZ.json.lock XYZ.heartbeat.json), then `rm -rf .xyz && mv`.
  - **Repo-root writes: none** except ignore rules. `reconcile_ignore_state` appends `.xyz/` and `/.tick/` (or runtime
    subpaths if `.xyz` is tracked) to **`$GIT_DIR/info/exclude`** (`:334,:391`). It falls back to `.gitignore` only for
    a non-git target. It warns, and never edits, if `phases/` or `relay-system/` are ignored.
  - **Machine-local registration:** `register_vendor` (`:400-413`) writes a row to
    `${XDG_CONFIG_HOME:-~/.config}/xyz/registry.tsv` under an advisory lock, unless `--no-register`.
  - It never touches `releases.db`, `releases.sql`, `.pdda-mode`, `ROADMAP.md`, root `utils/py`, or `.xyz-pin`.
    `xyz-sync.sh` does not read `.xyz-pin` either (only the registry). `.xyz-pin` (`commit=c829000…`, 2026-07-03) is
    advisory and stale.
- GH-353's `relay-automation/xyz-router-audit.sh` is **absent from Forge origin/development** (only the test and doc
  exist). Do not count on it. [V ls-tree]

---

## 5. Forge invariants worth mirroring

**`test/gh269-roadmap-retired.sh`** (current dev version; it now `require_forge_root` and skips inside a vendored `.xyz/`):
1. ROADMAP.md absent at the repo root.
2. `marathon_plan.py --dry-run` does not exit 3 without ROADMAP.md. (rebalanceOS equivalent: `.xyz/utils/marathon-plan.sh`, primary-only.)
3. `releases_app.py roadmap list` succeeds from the DB.
4. `pdda.sh roadmap-coverage` **and** `pdda.sh roadmap` exit 0 without ROADMAP.md. Note that in observe mode both exit
   0 anyway, so assert on `errors=` in SUMMARY or run with `PDDA_MODE=full`, or the test proves nothing.
5. Fixture: `.pdda-mode` has `ROADMAP_SOURCE=releases`; `roadmap add` lands in "Queue / parked intake"; `roadmap move
   --section Completed` works; `roadmap sync` prints "skipped — releases-mode repo".

**`test/gh349-releases-roadmap-vendored.sh`** (relevant for the last legacy import):
- link-style bullets and any-org issue/PR URLs parse; a re-sync is a no-op ("already in sync");
- a 0-entry parse of a non-empty ledger refuses `rule=roadmap-empty-parse` and deletes nothing; `--allow-empty` only clears a genuinely empty ledger;
- titles that only *mention* issues, umbrella `#601/#602`, and `GH-701..706` / en-dash ranges get **no key**; `#503 —` and `GH-707 —` titles **are keyed**;
- the parser on the repo's own ROADMAP.md yields **no duplicate GH keys** (otherwise sync refuses);
- `RELEASES-DB-FAQS.md` documents the `rated <pri>/<sev>/<appeal>/<effort>` grammar.

Suggested rebalanceOS mirror: one pytest that (a) asserts ROADMAP.md is absent, (b) asserts `.pdda-mode` carries the
marker, (c) runs root `releases_app.py roadmap sync` and expects the skip line, (d) runs `pdda.sh roadmap-coverage` and
asserts `errors=0` or a pinned count, and (e) keeps `test_releases_app_dump_parse.py` green against the new root copy.

---

## 6. Risks and one-way doors

1. **Schema v5→v9 is one-way for the old app** [V migrate; I old-app behaviour]. The new app and the migrated
   `releases.db`/`releases.sql` must land in **one commit**. Any open branch or clone still carrying the v5 root app
   breaks on its next ledger write, and merge conflicts on `releases.sql` follow the "take development's db" rule. Run
   `check` before and after, and keep the pre-migrate db/sql in TESTS-RESULTS.
2. **The flip changes the DB from mirror to source of truth.** After `ROADMAP_SOURCE=releases`, `roadmap sync`
   no-ops, so any markdown edit is silently lost. Without the marker and with ROADMAP.md deleted, sync **refuses**
   (`roadmap-missing`) and breaks the merge-cleanup / "re-run roadmap sync" rule. The file deletion and the marker must
   land together. `.pdda-mode` parsing tolerates the extra line (`pdda-lib.sh:37-38` reads only the first non-comment
   line). [V]
3. **Roadmap history and keys degrade at the final import** [V]:
   - 4 entries outside `###` sections (#300, #232, #230, GH-23) are not in the DB. Move them under a section before the last sync.
   - Only 6/143 rows carry `gh_number`. `reconcile-state` (`forge :4057`, `WHERE gh_number IS NOT NULL`), the GH-492
     drift warning, `roadmap update/move/rate --issue-num`, and `releases_scan.py` all key on it. **No verb can add a
     gh_number to an existing row afterwards** (`update` only takes `--issue-url` matching the existing gh_number).
     Without re-keying titles (`#N — Title` / `GH-N · Title`) *before* the final legacy sync, #348's goal (no drift
     against GitHub) is not met: the #345-style drift stays invisible, and every later edit needs `--gid`.
   - Old-org numbers (#93/94/96/144, the 2nd "In progress" block #217/#218/#219/#193) are not HiQS-Labs issues. Leave
     them unkeyed and do not rewrite their URLs (memory rule). `reconcile-state` should mark them unresolvable rather
     than closing them [I from `:4079-4087` identity check].
   - `raw_text` is verbatim, so prose is preserved in the DB. The markdown file itself remains in git history.
4. **CI lane breaks**: `check_doc_links.py` → 8 broken links (2 live docs plus 6 PROJECT docs, 4 of them archived
   history). Unwrapping links in archived docs touches "history" files, so decide whether to edit them or add a
   skip/allowlist. [V]
5. **The root fork carries the #322 guard that Forge lacks** (`_is_single_values_tuple`). Run
   `tests/test_releases_app_dump_parse.py` against the Forge copy. If it fails, upstream the guard to Forge rather than
   re-forking. `gen`/`RELEASES.generated.md` is gone in Forge, with no tracked caller here. [V/I]
6. **Silent capability loss**: `prior-art-check.sh` ROADMAP section skips without warning (rebalanceOS-only, needs a DB
   branch). `com.neochro.hq-rollup` (3-Eyes catalog, machine-local) may read ROADMAP.md [I]. The pyproject comment
   claiming xyz-sync refreshes the root copy is wrong and will mislead the next updater.
7. **pdda coverage is already red in observe mode** (9 errors with ROADMAP.md) and rises to 13 with the DB unless the 4
   dropped rows are fixed. In observe mode that does not block, which is why a test must assert counts.

---

## Recommended smallest approach

**Phase 1 (#329), one PR:**
1. Replace root `utils/py/releases_app.py` with Forge `origin/development` verbatim, pinning the Forge SHA in the
   commit and fixing the pyproject comment. Keep the #322 test green.
2. Run `releases_app.py migrate` → v9 and `check`. Commit `releases.db` + `releases.sql`.
3. Optionally refresh the primary `.xyz/` with `xyz-sync update` (machine-local, tier 2 auto) and bump `.xyz-pin`.

**Phase 2 (#348), one PR:**
1. Normalise ROADMAP.md: fold lines 35-38 and 230 into sections, merge the duplicate "In progress", and re-title
   HiQS-Labs entries to `#N — …` so they key. Run the final `roadmap sync` and assert there are no duplicate keys.
2. Add `ROADMAP_SOURCE=releases` to `.pdda-mode` and delete ROADMAP.md **in the same commit**.
3. Port Forge `pdda.sh` `check_roadmap_coverage` (`:326-372`), plus the GH-492 drift block if wanted. Add a DB branch to
   `prior-art-check.sh`.
4. Fix the 8 doc links. Rewrite ROUTER/AGENTS/ARCHITECTURE/GUIDING-PRINCIPLES/README/SOP/PDDA-INSTALL prose using Forge
   9e5c79979 as the template.
5. Add the GH-269-style pytest from §5.

Do not refresh the whole of `utils/pdda` from Forge here.
