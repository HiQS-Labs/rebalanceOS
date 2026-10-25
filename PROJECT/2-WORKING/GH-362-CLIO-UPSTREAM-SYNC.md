---
gh_issue: 362
source: https://github.com/HiQS-Labs/rebalanceOS/issues/362
title: "GH-362 sync utils/CLIO up to XYZ-CLIO and make Rebalance CLIO's upstream"
status: "Working — PR ready, awaiting merge"
created: 2026-10-25
updated: 2026-10-25
owner: noel
doc_type: chore
related: "HiQS-Labs/XYZ-CLIO#13, HiQS-Labs/XYZ-CLIO#15, HiQS-Labs/XYZ-CLIO#14, noelsaw1/noels-cross-project-tasks#52"
goal: >
  Make rebalanceOS utils/CLIO byte-identical to XYZ-CLIO main (bacd26f) and declare it CLIO's
  upstream, so every later CLIO change starts here and is published to XYZ-CLIO.
roadmap_exempt: false
---

# GH-362 — CLIO upstream sync

## Status

| What was just completed | What's next |
|---|---|
| Implemented and verified (receipt `TESTS-RESULTS/2026-10-25+GH-362/`); final Codex QA Approved R1, change 9 (SQLite gateway) Approved R2. | PR ready; awaiting merge. After merge: XYZ-CLIO publisher (0c), then the CLIO installer. |

Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/362 · Base `origin/development` 6672892 · Clone/branch `rebalanceOS-gh362-clio-upstream-sync-2026-10-25` / `chore/<same>`.
Rating `rated 75/55/50/80` (calc 260), 2026-10-25.
- Priority: it blocks the publisher (0c), the CLIO installer and the Codex capture fix (XYZ-CLIO#14).
- Severity: no runtime effect by itself (nothing is installed by merging), but until it lands, any device installed from this copy runs the pre-SQLite capture, which lacks the stale-lock reaper.
- Appeal: neutral.
- Effort: a byte copy plus doc lines.
- Recurrence: n/a (a one-time direction flip).

## Context
Operator decision D (noelsaw1/noels-cross-project-tasks#52, 2026-10-24) sets the order:
1. Finish the standalone XYZ-CLIO work. Done: XYZ-CLIO#12 (fleet discovery) and #15 (reconciled every Rebalance-only fix) are merged; `main` is at `bacd26f`.
2. Bring this copy up to it (**this task**).
3. From then on, **Rebalance's `utils/CLIO` is upstream**, and XYZ-CLIO is a published downstream (the publisher is step 0c, in XYZ-CLIO).

## Recon (this clone vs XYZ-CLIO `bacd26f`)
| Path | State | Action |
|---|---|---|
| `utils/CLIO/INSTALL.md` | differs (452 changed lines; this is the pre-SQLite doc and says "This mirrored folder is not the canonical SQLite helper release", L494) | replace with upstream bytes |
| `utils/CLIO/clio-agy-tail.sh`, `clio-codex-tail.sh` | differ (38 / 60 lines; missing `source_event_id`, the RO Agy DB, the serialized reaper, the narrowed IDE strip) | replace |
| `utils/CLIO/prompt-log-to-md.sh` | differs (18 lines; missing the `--sqlite` and `scheduled-export` branches) | replace |
| `utils/CLIO/clio-store.py` | absent | add |
| `test/clio-store.py` | absent | add (unittest for `clio-store.py`; uses the existing `test/fixtures/clio/`) |
| `test/clio-{capture,exporter,codex-tail,agy-tail}.sh`, `test/fixtures/clio/*` | identical | none |
| `utils/CLIO/README.md`, `utils/CLIO/LICENSE` | Rebalance-only | keep. The README gains the upstream section; the 0c publisher will exclude both (XYZ-CLIO keeps one root README/LICENSE). |

Consumers checked:
- `.agents/skills/clio` and `.claude/skills/clio` read the *installed* `~/.claude/hooks/clio-store.py` and link XYZ-CLIO's INSTALL anchor `#read-only-agent-lookup`, which still exists. Unaffected.
- Focus5 `PromptLogReader.swift` parses the exporter's Markdown note, whose format the SQLite projection keeps (same note/header, XYZ-CLIO #5). Unaffected by a repo sync; nothing is installed.
- `src/rebalance/ingest/clio.py` reads the configured runtime JSONL. Unaffected.
- No repo link targets the removed `Canonical SQLite fleet integration` heading (grep).
- CI (`.github/workflows/ci.yml`) does not run the `test/clio-*` suites; they are operator-run.
- **Script-inventory ratchet (GH-241):** `utils/pdda/check_script_inventory.py` freezes `.py/.sh/.swift` under `utils/`. Its baseline already lists the three CLIO siblings (`script_inventory_baseline.json` L58-60). Adding `clio-store.py` is an addition the ratchet rejects. Precedent #244/#249 *moved* `utils/CLIO/journey_replay.py` into the package, because it was Rebalance-side analytics. `clio-store.py` cannot move: the installed writer runs `$(dirname "$0")/clio-store.py`, and the folder is the deployable/published unit. **Decision:** grow the baseline with `--update-baseline`, recorded in this PR as a deliberate addition beside its siblings, with nothing else changing in the baseline (verified by diff). Rejected alternative: a `SCRIPT-INVENTORY-OK` pragma, which would edit the synced bytes and still need an exemptions entry.

## Changes
1. Copy the five `utils/CLIO` files and `test/clio-store.py` byte-for-byte from XYZ-CLIO `bacd26f`, keeping file modes.
2. `utils/CLIO/README.md`: add an **Upstream** section near the top. It says:
   - this folder is CLIO's canonical source;
   - HiQS-Labs/XYZ-CLIO publishes it unchanged (except this README and LICENSE);
   - every change is made here first, through a reviewed rebalanceOS PR, then published;
   - devices get it only through Skills Army HQ, never by hand copy.
   It also records the sync revision (`bacd26f`).
3. `.agents/skills/clio/SKILL.md` and its identical `.claude/skills/clio/SKILL.md` (plan QA R1): under "Locate the existing store", after the installed reader, prefer this repository's upstream `utils/CLIO/clio-store.py` and keep an XYZ-CLIO checkout as the published downstream. Drop "This repository's older `utils/CLIO/` copy may not contain the SQLite helper". The "Canonical interface and setup reference" becomes this repo's `utils/CLIO/INSTALL.md#read-only-agent-lookup` (that anchor exists in the synced bytes), with XYZ-CLIO named as its published copy. Retrieval behaviour is otherwise unchanged. The deployed skill updates later through Skills Army HQ, not in this PR.
4. `AGENTS.md`: one line under the existing CLIO pointer saying `utils/CLIO/` is CLIO upstream and edited here first (see `utils/CLIO/README.md`).
5. `utils/pdda/script_inventory_baseline.json`: `--update-baseline`. The only diff is the added `utils/CLIO/clio-store.py`.
6. `pyproject.toml` `[tool.ruff] extend-exclude`: add `"utils/CLIO"` and `"test/clio-store.py"`, with a comment that the folder is published byte-for-byte to XYZ-CLIO and verified by its own suites. Recon: the repo's ruff (`ruff check .` and `ruff format --check .`, run by both the pre-push gate and `ci.yml`) rejects the upstream files:
   - `clio-store.py`: E731 at L754 and F841 (`since` unused) at L779;
   - `test/clio-store.py`: F401 and B023 ×2;
   - format would rewrite ~1,400 / ~1,200 lines.

   That would fork the bytes on day one and make 0c's "first publish is an empty diff" proof impossible. The file already excludes vendored `releases_app.py` for the same reason. F841 is a dead leftover (the render path uses `cutoff_dt`), not a defect; it is logged as a follow-up for the first upstream change, not edited here.
7. `CHANGELOG.md`: entry per repo convention.
8. `src/rebalance/ingest/clio_journey.py` `markdown_rows` docstring (plan QA R2): replace the line-number contract `utils/CLIO/prompt-log-to-md.sh:500` with a stable descriptive reference: the legacy exporter's jq render of `<!-- clio:id:SESSION:UTC -->` blocks in `utils/CLIO/prompt-log-to-md.sh`. The sync shifts that renderer by about 24 lines. This is a comment-only change; the parser is untouched. Check: `rg -n -F 'prompt-log-to-md.sh:500' src/` returns nothing after the change.

9. *(Added after final QA R1, found by the pre-push gate.)* SQLite gateway ratchet (GH-136, `utils/pdda/check_banned_imports.py`): the push was blocked with `utils/CLIO/clio-store.py:1: NEW sqlite3.connect bypass (3 site(s))`. Its baseline `sqlite_connect_baseline.json` is `{}`: the repo has zero direct-connect debt. The checker's own model is a list of **gateway directories that are separate stores by design** (`src/rebalance/ingest/db`, `HiQS/hiqs`). CLIO's store is exactly that: a private prompt-history DB whose stdlib helper runs installed beside the capture hooks and cannot import the rebalance gateway. So `utils/CLIO` is added to `SQLITE_GATEWAY_DIRS`, with the docstring updated ("three gateways"). Rejected:
   - Baseline debt: it would re-open a zero baseline for code that is not a bypass.
   - A `# GATEWAY-OK` pragma: it would edit the synced bytes.
   Checks: `check_banned_imports.py --check` clean; `tests/test_sqlite_gateway_ratchet.py` 9 passed. Red control: the blocked push.

## Non-goals
- No edits to synced bytes. INSTALL.md keeps upstream wording; the banner that names the upstream inside INSTALL.md is a first change made *here* after the flip and published in 0c.
- No publisher.
- No installer.
- No Codex format fix (#14).
- No skill edits beyond the stale locate/reference lines in change 3.
- No device installs.

## Risks / rollback
- Purely repo files; nothing runs on merge. Rollback is a PR revert.
- Ratchet: the baseline grows by exactly one entry. A reviewer can see it in the diff.

## Verification (disposable full clone; tests with throwaway HOME and synthetic data)
- `diff -r` of the six synced paths vs XYZ-CLIO `bacd26f`: empty, with modes equal (red control: run against the base → non-empty).
- `bash test/clio-{capture,exporter,codex-tail,agy-tail}.sh` and `python3 test/clio-store.py`: pass, apart from the known date-dependent `test_activation_import_gate_and_source_preservation`, which also fails in XYZ-CLIO at `bacd26f`.
- `python3 utils/pdda/check_script_inventory.py --check`: green after change 4 (red control: before change 5 it fails, naming `clio-store.py`).
- `ruff check .` and `ruff format --check .` green with the exclude (red control: without it, the five findings above). `utils/pdda/pdda.sh run` (docs and roadmap-coverage gate) green, plus the repo's pre-push static gate (ruff, repo guards, governance ratchets) on push.
- Smoke: run `python3 utils/CLIO/clio-store.py --help` and one `query` against a throwaway DB, from the repo copy (main path), plus `prompt-log-to-md.sh --help` (adjacent path).
