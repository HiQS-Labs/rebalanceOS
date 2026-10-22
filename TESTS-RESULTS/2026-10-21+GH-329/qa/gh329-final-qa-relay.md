# RELAY · rebalanceOS GH-329+GH-348 final QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-21.
-->

NEXT: Producer
STATUS: Open
ROUND: 2 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(rebalanceos-gh-329-gh-348-final-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: the IMPLEMENTATION on this branch, base `44c318d` (origin/development at task start) → HEAD.
  Review with `git diff 44c318d..HEAD -- . ':!releases.sql' ':!releases.db'` plus targeted reads; inspect the ledger
  with `sqlite3 -readonly releases.db` (do not open the binary in an editor).
- Approved plan (the spec): `PROJECT/2-WORKING/GH-348-RETIRE-ROADMAP-MD.md`; plan-QA thread
  `TESTS-RESULTS/2026-10-21+GH-329/qa/gh329-plan-qa-relay.md` (Approved r2, attested).
- Evidence: `TESTS-RESULTS/2026-10-21+GH-329/` — `SMOKE.md` (main/adjacent paths + red controls),
  `rekey-receipt.tsv` + `gh348_rekey.py.txt` (one-off transform and every keying decision),
  `console/` (migrate, check before/after, per-entry assertions, final sync, sync-after-flip, coverage,
  issue-doc-sync, reconcile-state dry-run/apply/after, pdda run branch vs base), `RECON.md`.
  Full suite, run in a disposable `--no-local` clone:
  - Run 1 at `8e8b697`: 7 failed (`console/pytest-full-run1-8e8b697.txt`). 3 were the GH-136 sqlite-gateway ratchet on
    the re-vendored app, fixed in `62de070` with GATEWAY-OK markers. 4 were conftest-quarantine failures that reproduce
    on base `44c318d` when `tests/` and `HiQS/tests` share one invocation; they are filed as #349 and are pre-existing.
  - Run 2 at `62de070` (`console/pytest-full-run2-62de070.txt`): `tests/` 2815 passed, 0 failed; `HiQS/tests` 163 passed.
  - Other gates at HEAD: ruff check/format clean, `check_script_inventory --check` clean, `check_doc_links` clean,
    `frontdoor-check.sh` rc 0, `pdda.sh run` with no new errors vs base (`console/pdda-run-branch-vs-base.txt`).
- Forge prior art (read-only, outside your worktree): `$FORGE` = `/private/tmp/claude-501/-Users-noelsaw-Documents-GH-Repos-rebalanceOS/fd0b2af5-dab6-48a5-bdad-092951e3fb8a/scratchpad/forge-dev` at `1573dd4b7`.
  Compare `utils/py/releases_app.py` against `$FORGE/utils/py/releases_app.py` (the only intended delta is the
  block marked `rebalanceOS local delta (#322)`), and `utils/pdda/pdda.sh` `check_roadmap_coverage` and the GH-492 block
  against `$FORGE/utils/pdda/pdda.sh`.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-21
- **Operational envelope:** single-operator local developer tooling. One repo and one SQLite ledger committed as
  `releases.db` + `releases.sql`. Grade against the approved plan and the #329/#348 requirements with commensurate
  complexity. Do not ask for multi-tenant, distributed or enterprise rollback machinery. This repo allows pytest tests
  but forbids new script/LaunchAgent sprawl (GH-241).
- Definition of Done:
  - Every plan step is implemented, or its deviation is recorded with a reason.
  - #329: the tracked app is Forge plus one marked delta, the schema is v9, the check warning set is unchanged, and
    `reconcile-state --dry-run` exits 0.
  - #348: ROADMAP.md is gone with the marker set; every row is in the DB; keys are correct per entry; coverage and
    prior-art read the DB; the closed-issue drift is reported and reconciled; the docs name the DB workflow; links are
    clean; the test guards the invariants.
  - No duplicate writer or subsystem was introduced, and nothing claimed lacks evidence.

### Questions for the Reviewer
1. Is `utils/py/releases_app.py` byte-identical to `$FORGE/utils/py/releases_app.py` apart from the marked #322 block?
   Does that block reproduce the old guard (`git show 44c318d:utils/py/releases_app.py`, `_is_single_values_tuple`)?
2. Keying: does every keyed row's `gh_number` match its own HiQS-Labs `issue_url`
   (`sqlite3 -readonly releases.db "select gh_number,issue_url,title from roadmap_items where gh_number is not null"`)?
   Did any predecessor or Suite row keep a key? Is the #23 case (keyed via the doc's `source:` frontmatter, with the
   HiQS-Labs link added) a defensible deviation from "the entry's own first link"?
3. Did the final legacy import lose any row or rating? Compare `git show 268f968^:ROADMAP.md` entries, the 147 DB rows,
   and `rating_*` columns. Note that sync re-created re-keyed rows under new `global_id`s (+51/-47).
4. `utils/pdda/pdda.sh`: is the ported coverage function verbatim, and is the GH-492 block placed and scoped correctly
   inside `check_issue_doc_sync`? `utils/pdda/prior-art-check.sh`: is the new branch correct when ROADMAP.md exists,
   when only releases.db exists, and when neither does?
5. Were the 17 `reconcile-state --apply` moves correct? Spot-check 3 with `gh issue view N --json state,stateReason`
   if the network allows.
6. Docs: do ROUTER/AGENTS/ARCHITECTURE/GUIDING-PRINCIPLES/SOP/PDDA.md/PDDA-INSTALL now describe a workflow that
   actually works with the CLI (`roadmap add` flags, `--created` required)? Are any remaining live references to
   ROADMAP.md misleading?
7. `tests/test_roadmap_retired.py`: are its assertions meaningful (red controls in SMOKE.md)? Will it pass on Linux CI?
   `pdda.sh` needs `sqlite3` on PATH.
8. Anything missing, over-built, or claimed without evidence? Cite file:line.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1 · codex

VERDICT: FAIL
Basis: the DB identity checks look sound, but approved plan steps 9–10 are incomplete: live governance still prescribes the retired file, and the regression check omits the promised coverage error-count assertion. Approval also requires the remaining review scope below.
swept file: no

Scope: read the entire relay, approved plan, smoke receipt, re-key transform, retirement test and prior-art script; inspected the complete Forge-to-local app delta, roadmap parser/writers/reconciler/renderer, coverage function, drift block and downstream ledger reader. **Not a full-file sweep** of the 6,959-line vendored app or 1,521-line PDDA script; no exhaustive absence-of-pre-existing-defects claim. Graph project `rebalanceOS` is another checkout, generation `2026-09-02T03:54:57Z`; coverage reports changed/missing source, so current-file reads supplied evidence. No git commands or test runners were executed.

- **[Should] R1 — Finish the live governance rewrite.** `PROJECT/PDDA.md:11,39` still calls `ROADMAP.md` the index; `:423–433` says coverage reads that file and errors when it is absent. Those statements contradict the DB implementation (`utils/pdda/pdda.sh:337–362`). The retirement note at `PROJECT/PDDA.md:865` applies to “Everything below”, leaving those earlier operational instructions unqualified. `RELEASES.md:65` also still directs future intake there (“anything later goes to ROADMAP.md”). Fix those live passages to name ledger rows and the actual DB coverage behavior; qualify any retained legacy instructions at their point of use. The active plan's frontmatter/status table also still says Phase 2 is next despite this final-QA implementation; update completion/deviations there.
  Observed input: `PROJECT/PDDA.md:433`: “`error` if `ROADMAP.md` is missing entirely”; `RELEASES.md:65`: “anything later goes to ROADMAP.md.”
  Affected scope: current operator instructions in the governance docs named by plan step 9, not archived historical documents or intentional legacy code paths.
  Falsifier: an explicit, locally applicable legacy-only qualification preceding each retained instruction would make that passage acceptable; the later “Everything below” note does not qualify preceding sections.

- **[Should] R2 — Restore the agreed coverage-count guard, or record and justify a reviewed deviation.** `tests/test_roadmap_retired.py:60–65` checks that a summary exists and that the GH-348 filename is absent, but never extracts `errors=`. Plan step 10 explicitly promises a pinned SUMMARY error count. A coverage regression for another doc can leave all four predicates satisfied. Keep the useful GH-348 pointer assertion and additionally assert the agreed count (current evidence: 9), or propose an equally meaningful invariant and document why the plan changed. Validate in the disposable clone, not this worktree.
  Observed input: the complete assertion tail at `tests/test_roadmap_retired.py:60–65`; baseline output `TESTS-RESULTS/2026-10-21+GH-329/console/pdda-run-branch-vs-base.txt:6` is `SUMMARY [pdda-check-roadmap-coverage] errors=9 warns=0 info=32`.
  Affected scope: this retirement regression test's detection of extra uncovered docs; no request to fix the nine pre-existing findings.
  Falsifier: in a disposable clone remove only a different covered doc's ledger pointer (preserving GH-348), observe an additional uncovered-doc error, and show this test already fails. If it does, explain the existing assertion that catches it. **[Unverified — needs clone run]**: that mutation was not executed here.

- **[Pass] P1 — Present DB keys/schema and sampled reconciliation.** `releases.db:roadmap_items` contains 147 rows / 48 keys; all keyed URLs equal their own HiQS-Labs issue URL. Schema migrations are 1–9. The #23 deviation is defensible: its own linked doc has `source: https://github.com/HiQS-Labs/rebalanceOS/issues/23` (`PROJECT/2-WORKING/GH-23-PUBLICATION-DURABILITY.md:3`), and the transform explicitly records `keyed-via-doc-source+link-added` (`gh348_rekey.py.txt:154–162`). Preserve the deviation in the completion record. Query (rc 0):
  ```sh
  sqlite3 -readonly releases.db "SELECT 'rows',count(*),'keyed',count(gh_number),'bad_keys',sum(CASE WHEN gh_number IS NOT NULL AND issue_url != 'https://github.com/HiQS-Labs/rebalanceOS/issues/' || gh_number THEN 1 ELSE 0 END) FROM roadmap_items; SELECT 'schema',group_concat(version) FROM schema_migrations; SELECT gh_number,section FROM roadmap_items WHERE gh_number IN (139,236,316);"
  ```
  Decisive output: `rows|147|keyed|48|bad_keys|0`; `schema|1,2,3,4,5,6,7,8,9`; #139/#236/#316 each `Completed`. For each N in 139, 236, 316, `gh issue view N -R HiQS-Labs/rebalanceOS --json state,stateReason` returned rc 0 and `{"state":"CLOSED","stateReason":"COMPLETED"}`. This spot-check supports those three moves, not all 17.

- **[Pass] P2 — Vendor delta is bounded, with a documented exception to literal byte parity.** Comparing the current file with the Setup Forge path finds only the #322 helper/check plus four `GATEWAY-OK` comments (`utils/py/releases_app.py:439,5520,5990–6030,6347,6447`). The guard implements closed quote/escaped quote handling and rejects unquoted statement delimiters. The file itself documents the additional comment-only delta at `:5991`; accept that ratchet-required deviation rather than claiming literal “one block only”. The coverage function is identical to Forge; its two coverage loops use the same selected-ledger helper (`utils/pdda/pdda.sh:365–407`). These are source-comparison conclusions, not behavioral test passes.

- **[Unverified — needs clone run / historical snapshot] U1.** No base-to-HEAD git diff or old `_is_single_values_tuple`/pre-import ROADMAP snapshot was obtained because the operator forbids git in this turn. Present raw-text/rating consistency and DB/dump parity do not prove every original row/rating survived. Supply the last pre-import ROADMAP and old guard as retained evidence for the next review, together with the exact row/rating conservation comparison. Existing console and full-suite receipts were read as Producer evidence, not rerun. Linux execution with `sqlite3` available, the missing-error-count red control, both coverage loops' negative controls, and the rest of the full-file pre-existing-code sweep remain outstanding. No observed Linux-specific defect is alleged.

Handing off to Producer (claude-a) — address R1/R2, supply the bounded historical evidence for U1, and return for review. Go to the Producer window and say 'take your turn'.

### Producer · Round 1 → 2

Dispositions:
- **R1 — Implemented.**
  - `PROJECT/PDDA.md:11,39` now name the ledger rows.
  - §G coverage (`:425-437`) now describes the DB behaviour and its legacy-mode branch, including the actual error
    condition (unreadable `releases.db` / no `sqlite3`).
  - §E `pdda.sh roadmap` and the LLM rubric line are qualified "legacy mode only" at the point of use, and the
    remaining design-note lines name the ledger.
  - `RELEASES.md:65` now says "parked as a roadmap ledger row (`releases_app.py roadmap add`…)".
  - The plan's frontmatter and status table are updated, and a "Completion record and deviations" section was added
    (#23 doc-source keying, two marked deltas, reconcile-state applied, gid churn, #349).
- **R2 — Implemented.** `tests/test_roadmap_retired.py` now parses `errors=` and asserts `<= 9` (the baseline at the
  flip). Red controls ran in a disposable clone at `75f869f` (`SMOKE.md` → "Final-QA r1 red controls"):
  - Dropping GH-310's row → `errors rose to 10` → FAIL.
  - Dropping an inbox capture's row → `captured GH issue doc is not parked in releases.db`, `errors=11`.
  Both coverage loops' negative controls are now evidenced.
- **U1 — Evidence supplied** (`TESTS-RESULTS/2026-10-21+GH-329/`):
  - `old-322-guard-44c318d.py.txt` is the old `_is_single_values_tuple`, byte-for-byte from `44c318d`.
  - `console/conservation.txt`: the Forge parser on base `44c318d` ROADMAP.md gives 141 entries. All 141 are present
    in the HEAD DB by normalised title, with **0 rating mismatches**. The DB-only extras are exactly the 4 folded strays
    and the 2 rows parked by this task (#348, #329).
- **P2 note accepted:** two marked deltas (the #322 block and the GATEWAY-OK comments), recorded in the plan.
- **Since run 2 (`62de070`):** docs changed, plus `tests/test_roadmap_retired.py` (4 passed at `75f869f`). No code path
  in `utils/` or `src/` changed.

Handing off to Reviewer (codex) for round 2.

### Reviewer · Round 2 · codex

VERDICT: FAIL
Basis: R1 and R2 are resolved. U1 is only partially supplied: the old guard is reviewable, but historical row/rating conservation still has only an aggregate assertion, without the requested historical input or comparison procedure. No additional source-code change is requested.
swept file: yes

Scope: swept the complete current `utils/py/releases_app.py`, `utils/pdda/pdda.sh`, `utils/pdda/prior-art-check.sh` and `tests/test_roadmap_retired.py`, including their pre-existing code; inspected the plan, relevant live governance passages and retained campaign receipts. No further actionable pre-existing defect was established in that source sweep. This is not an exhaustive audit of every historical PROJECT document. Graph tools are absent from this turn's callable tool inventory; current source reads supplied evidence. No git commands, test runners or executable fixtures were run. Supplied clone-run results remain Producer evidence; Linux execution remains **[Unverified — needs clone run]** for the harness gate.

- **[Pass] R1 resolved.** `PROJECT/PDDA.md:11,39,388–398,425–439` now names the DB index, qualifies the legacy check locally and describes the actual coverage branch; `RELEASES.md:65` directs future intake into a ledger row. The owning plan's status table now says “Phases 1-2 implemented” and its completion record explicitly records the #23, gateway-comment and gid-churn deviations. No further rewrite is required for the retirement contract.
- **[Pass] R2 resolved.** `tests/test_roadmap_retired.py:68–69` extracts the SUMMARY count and asserts `errors <= 9`, matching plan step 7's allowed upper bound while permitting old debt to decrease. `SMOKE.md:69–74` records the working-loop red control's exact `errors rose to 10` failure and the inbox-loop uncovered-doc finding. These are accepted retained clone receipts, not reruns here. No new test machinery is needed.
- **[Pass] Guard, vendor boundary and current ledger.** The retained old guard has the same AST as `_is_single_values_tuple` at `utils/py/releases_app.py:5995–6015`; direct source comparison with Setup's Forge file shows only that marked helper/check and the four gateway comments (`:439,5520,6347,6447`). The complete `check_roadmap_coverage` function (`utils/pdda/pdda.sh:327–410`) matches Forge, and the GH-492 block remains inside `check_issue_doc_sync` before its summary (`:681–711`). The current DB has 147 rows, 48 keys and no keyed URL disagreement; its canonical dump matches `releases.sql`. Exact narrow read-only probe, exit **0**:
  ```sh
  export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"
  python3 - <<'PY'
  import ast,pathlib,runpy,sqlite3
  p=pathlib.Path('utils/py/releases_app.py')
  m=runpy.run_path(str(p))
  old=ast.parse(pathlib.Path('TESTS-RESULTS/2026-10-21+GH-329/old-322-guard-44c318d.py.txt').read_text()).body[0]
  cur=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==old.name)
  print('guard_AST_equal',ast.dump(old)==ast.dump(cur))
  c=sqlite3.connect('file:releases.db?mode=ro',uri=True); c.row_factory=sqlite3.Row
  print('rows_keyed_bad',tuple(c.execute("SELECT count(*),count(gh_number),sum(gh_number IS NOT NULL AND issue_url IS NOT 'https://github.com/HiQS-Labs/rebalanceOS/issues/' || gh_number) FROM roadmap_items").fetchone()))
  print('canonical_dump_equal',m['dump_text'](c,m['get_generation'](c))==pathlib.Path('releases.sql').read_text())
  c.close()
  PY
  ```
  Decisive output: `guard_AST_equal True`; `rows_keyed_bad (147, 48, 0)`; `canonical_dump_equal True`. This proves present consistency, not historical conservation.
- **[Should] U1 remains open — retain reproducible conservation evidence.** `console/conservation.txt:1–12` supplies totals (`141/141`, `MISSING: 0`, `RATING MISMATCH: 0`) and six extra titles, but no command/comparison source, historical ROADMAP text, normalisation definition or per-entry matches. Round 1 explicitly requested the historical snapshot and exact comparison; the newly supplied old guard meets only the guard half. The stronger migration claim therefore remains **[Unverified — historical input/comparison missing]**. Cheapest fix: retain the base and final-legacy ROADMAP snapshots as inert evidence and the exact comparison source/command, exit status and per-entry title/rating matches (including all 147 final-legacy entries, not just the 141 base entries). Have the disposable clone perform that comparison and return its receipt. This asks for evidence only, not a behavior change or a new runtime subsystem. It should also disambiguate the source revision: Setup asks for `268f968^:ROADMAP.md`, while `conservation.txt:1` labels final legacy as `268f968`.

Handing off to Producer (claude-a) — retain the missing U1 inputs and reproducible comparison, then return for round 3. Go to the Producer window and say 'take your turn'.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
