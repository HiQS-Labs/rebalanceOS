# RELAY · gh305-studio-fable-r2
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-02.
-->

NEXT: Producer
STATUS: Approved
ROUND: 1 / 4

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
6. **Commit only the relay file** (`relay(gh305-studio-fable-r2): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Approval token rule
On approval call task done using the exact env-pinned command supplied by the native turn. Do not release Approved to Producer.

## Setup
- Artifact under review: **review-r2.md** (embedded below — read it here).
- Reviewer: claude   ·   Producer: producer
- Started: 2026-10-02

### Artifact — review-r2.md
```
Final focused re-review of Rebalance Studio follow-through #282 / Forge #937. Read QA/gh305-studio-fable-r1.md and inspect changes after fc55f96 at fe78517. R1 Blocker fixed: manifest.json now0.97.2, matches pyproject andinit; nativefrontdoor receipt willbeadded afterfinish. R1 Should fixed: single-refcachedrows citecanonicalrecord_id exactlyaslive, multi-refkeepconsumerkeywithallreferences. Legacyagent/repomissing no longer dropsrow; provenanceenrichment reports prompts_updated (default0) and unchangedexcludesupdated; index_ops exposesupdatedcount. Original corepatch reviewed r1unchangedotherwise; recheck affectedfunctions/callers only asneeded. Source6aa original, fe78517fixes. Final74existingaffectedtests passed in separatefullclone,9recordedcontrolsfailbase535 andpassfixedcandidate. Controls nowinclude cachedcitationmatching andmetadatafreelegacyretention. Remainingtype/frontdoor receipts are beingcaptured, no qualification claim iffail. ReadPROTOCOL andallfinalreceipts present. No newgate/testsuite/DB/vector/pushloop/ledgerwriter. Source consumerstillusesconfigured fullhistory compatJSONL; additiveorigin references preserveoldconsumerkeys. Scopedmaintenanceprojection reusesregistryanddoesnotembed. Memorypolicy/plists/schedules unchanged; core26normalexportscomplete/3deliveredrevisionsobserved, localconsumerrefreshnotyetdone. No otherdeviceenabled,7day/fleetpending. ReviewallR1findings disposition: implementedBlocker/Should/counter/legacyrow; mypyutilityscopeaccurateasoutside src gate, no broader utilitymypyclaim. DefinitionofDone: no actionableblockingfindings, versionmanifestaligned, matchingcitationsandfullsource-referenceunion, nonembeddingfacade selectedprovidercorrect, privacy/docs honest. NativePASSmustmarkApprovedandtaskdoneusingenvpin; noApprovedrelease toproducer. Do not run suites inreviewworktree. Avoid reopening settled fleettransport/memorydecision.
```
- Definition of Done: Version consistency, stable live/cache citations, additive canonical-reference preservation and truthful bounded qualification; no open Blocker or Should.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1 (claude)

Reviewed fix commit `fe78517` against R1 (`QA/gh305-studio-fable-r1.md`, candidate `d94fe15`): `git show fe78517` = 6 files, 26+/6- (`manifest.json`, `clio.py`, `index_ops.py`, `daily_work_synthesis.py`, `qualification-controls.py`, PROJECT doc). Re-read the complete touched functions (`collect_packet` :335-375, `sync_clio_prompts` :93-187, `load_recent_clio_prompts` :66-79, `_refresh_clio` :2036-2058), the 9-check controls script, PROTOCOL.md, every receipt log and provenance.jsonl. Probes ran from this worktree with output under `.relay-scratch/tmp/`; no suite, validate.sh, mypy or ruff executed here (neither module is installed in this worktree: `python3 -m mypy --version` → `No module named mypy`).

swept file: yes

**R1 dispositions checked**

- `[Pass]` **R1 Blocker (manifest drift) fixed.** `manifest.json:5` `"version": "0.97.2"` = `pyproject.toml:7` = `src/rebalance/__init__.py:31`. Probe A re-ran the drift section of `utils/frontdoor-check.sh:53-127` verbatim → `rc=0`, stdout empty (no `version … != pyproject` line, no tool-surface drift). The CI front-door job no longer fires on this branch.
- `[Pass]` **R1 Should (live vs cached citation) fixed as specified.** `daily_work_synthesis.py:351-353`: no `record_id` + exactly one `source_records` entry → cite that `record_id`; otherwise keep the consumer key. Probe C through the real DB fallback (`load_recent_clio_prompts`, scratch DB synced from one synthetic row): `LIVE ['clio:clio1-a']` / `DB-FALLBACK(1 ref) [('clio:clio1-a', [{'record_id': 'clio1-a', 'origin_id': 'origin-a'}])]` — identical id, references retained. Probe B: 2-ref row → `clio:s_2026-10-02T22:00:00Z_abcd` (consumer key kept); 0-ref row → consumer key kept. Falsifier from R1 satisfied.
- `[Pass]` **R1 Nit (updated counter) fixed.** `clio.py:90` `prompts_updated: int = 0`; `:157-167` splits UPDATE → `updated += 1` from `unchanged += 1`; `index_ops.py:2055` surfaces it. Probe B: `SYNC1 1 0 0`, `SYNC2 0 1 0`, `SYNC3(new origin) 0 0 1` (inserted/unchanged/updated).
- `[Pass]` **R1 Nit (legacy rows without agent/repo) fixed.** `daily_work_synthesis.py:363-364` `row.get("agent", "")` / `row.get("repo", "")`. Probe B: `{"timestamp","session_id","prompt"}` → `('clio:6bb3b4a7…', '', '')` — retained with the sha256 identity fallback at `:354-356`; `scrub("")` returns `""` (`:89`).
- `[Pass]` R1 mypy-scope Nit dispositioned accurately: PROJECT doc `:177` states the daily utility is outside the `mypy src/` gate (`ci.yml:86`); no broader claim made.

**Artifact claims**

- `[Pass]` Controls script now 9 checks (`qualification-controls.py:54-64`); the two new checks assert exactly the R1 Should/Nit behaviour. Both fail at base by construction (`row["agent"]` KeyError; id = `clio:legacy-key`) and `controls-final-base.log` lists all 9 as base failures, `controls-final-green.log` 9/9 — consistent with the code.
- `[Pass]` No new gate, suite registry, DB, vector store, push loop or ledger writer: diff stat is confined to the six files above; no plist/schedule/workflow file touched.
- `[Pass]` PROJECT doc `:177` is truthful about what was fixed and the mypy boundary.
- `[Unverified — needs clone run]` `final-focused.log` 74 passed; `controls-final-*.log`. Not executed here per protocol; harness gate follows this turn.
- `[Unverified — needs clone run]` **Type and static receipts are stale relative to `fe78517`.** `mypy.log` and `static.log` were last recorded at `d94fe15` (`git log -- …/mypy.log`), before the fix touched `clio.py` and `index_ops.py`, both inside `mypy src/` scope. The artifact discloses this ("remaining type/frontdoor receipts are being captured, no qualification claim if fail"), so it is not a truthfulness fault; the harness gate must re-run `mypy src/`, `ruff check .`, `ruff format --check .` and `bash utils/frontdoor-check.sh` on the final head. The change is a dataclass int field and two `.get()` calls, so I expect green.

**New findings (no behaviour change requested)**

- `[Nit]` `daily_work_synthesis.py:350` still carries a non-dict branch (`else row["id"]`) but `:351` and `:363-364` now call `row.get(...)` unconditionally; a `sqlite3.Row` would raise `AttributeError`, which `:374` does not catch. Probe B: `NONDICT raised AttributeError 'sqlite3.Row' object has no attribute 'get'`. Dead in practice — both producers return dicts (`recent_prompt_rows` → `json.loads` rows, `:97,112`; `load_recent_clio_prompts` → `dict(row) | …`, `clio.py:79`). Optional cleanup: drop the `isinstance` branch or add `AttributeError` to the except tuple.
- `[Nit]` A single `source_records` entry lacking `record_id` drops the row silently (`:353` KeyError → `:374`). Probe B `BADREF` → `[]`. Unreachable from this codebase: `clio.py:150-152` only writes references that carry both keys. Noting for the sweep only; no fix requested.

Pre-existing defects in the touched functions beyond the two Nits above: none found (R1's `import hashlib` in the loop at `clio.py:139` and the commented broad `except` at `:77` stand).

**VERDICT: PASS**
**Basis:** Definition of Done met: version manifest aligned across all three files and the front-door drift probe is clean; single-origin cached citations now equal live citations through the real DB fallback while multi-origin rows keep their consumer key with every reference; canonical references are additive and the updated counter is surfaced; the packet and PROJECT doc are truthful about the pending type/frontdoor receipts. No open Blocker or Should. Type/static/frontdoor receipts for the final head are the harness gate's to record; a red there would reopen this, not the code review.

Relay closed (Approved), no further turn needed. Producer: record the `mypy src/`, ruff and `frontdoor-check.sh` receipts for the final head alongside the existing logs before claiming qualification.


### Attestation · relay-drive — 2026-10-02T22:53:28Z
task: GH305-STUDIO-FABLE-R2
reviewer: claude
status: Approved
reviewed-head: 072adb2898b870f3aca807f061b6b03104ea4397
added-range: 7391+5900
added-sha256: b9ec5837b48def61154084277c4f2ec3abc88d5fd496e82f5f9d43b45090bb8a
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
