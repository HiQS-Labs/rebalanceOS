# RELAY · gh305-studio-fable-r1
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-02.
-->

NEXT: Producer
STATUS: Open
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
6. **Commit only the relay file** (`relay(gh305-studio-fable-r1): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Approval token rule
On approval call task done with the exact absolute env-pinned tick command from your native turn prompt. Do not release an Approved task to Producer. Findings may release.

## Setup
- Artifact under review: **review-packet.md** (embedded below — read it here).
- Reviewer: claude   ·   Producer: producer
- Started: 2026-10-02

### Artifact — review-packet.md
```
Review the focused Studio follow-through for Rebalance #282 and cross-repo Forge #937, pointer #305. Source6aa883e plus evidence-only updates. Code changes limited to clio.py, semantic_index.py maintenance facade, daily_work_synthesis.py and0.97.2version. Existing Studio consumer config already points to canonical full-history compatibility export (3976source rows,3knownorigins), so no new reader/store/transport. Live consumer refresh/deployment not yet performed. Guard prevents recent scheduled derived jobs (exit75); no guard/plist/schedule changes permitted or claimed. OtherMacs stayoff.
Read complete touched functions/directcallers and TESTS-RESULTS/2026-10-02+GH-305/PROTOCOL.md, controls-base.log, controls-green.log, qualification-controls.py. Seven synthetic checks fail base535bb7a and passcandidate: LFUnicode framing, stableDailycanonical IDs, provenanceidempotence, multioriginunion withoutconsumerkeychange, samepasscollision/reorderedreplay/cachedrefs, nonemptyselectedCLIOmaintenanceprojection,3Unicodeseparators. Existing41focusedtests pass in separatefullclone, typecheck/staticresults willbeadded whenavailable. Canonical references are additive JSON onexistingclio_prompts; primary IDs andsemantic keysunchanged. IncludesDBfallbacksource_records tokeepcanonicalrefs visible; metadata-freelegacyDailyrecords use stablehash insteadposition. Maintenancefacadeuse_registry_providers=True respectsselectedsources anddoesnotembed. NoCloudsynthesis/liveprompt injection/newtestsuitegate. Reviewmigrationandprojectionunion, timestamp/legacycompatibility, fallbackcites, scopedbackfill, correctprivacy/docs/verificationclaims; sourceDDLadditive only. Do not run mutation-heavy suites inreviewworktree. Provide bounded observedfindings with input/scope/falsifier; do not expand into transportarchitecture or memorypolicy review. Ifsound, approveusingnative taskdone; earliertranscriptsarenotQAapprovalforthispatch.
```
- Definition of Done: _<fill in the acceptance criteria the Reviewer grades against>_

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1 (claude)

Reviewed candidate `d94fe15` vs base `535bb7a` (`git diff --stat 535bb7a..HEAD`: 19 files, 246+/13-; code limited to `clio.py`, `semantic_index.py`, `daily_work_synthesis.py`, version files). Read the complete touched functions, direct callers (`cli/semantic.py:57-71`, `index_ops.py:1555-1567`, `collect_packet`), PROTOCOL.md, all three controls logs, provenance.jsonl, core-recheck.json and qualification-controls.py. Probes ran from the review worktree with output under `.relay-scratch/tmp/probe.txt`; no suite, validate.sh or fixture was executed here.

swept file: yes

**Findings**

- `[Blocker]` **manifest.json version not bumped — CI front-door gate fails.** `pyproject.toml:7` and `src/rebalance/__init__.py:31` moved to `0.97.2`; `manifest.json:5` still reads `"version": "0.97.1"`. Base `535bb7a` had both at `0.97.1` (`git show 535bb7a:manifest.json`), so this patch introduces the drift. `utils/frontdoor-check.sh:52-135` compares the two and emits `report 3 "version 0.97.1 != pyproject 0.97.2"`, which sets `fired=1` and exits 1 (`frontdoor-check.sh:15,267`); `.github/workflows/ci.yml:72` runs that script as the "Front-door health board" job. The recorded `static.log` is ruff only, so the "static gate" receipt in provenance.jsonl did not cover this.
  - Observed input: probe re-ran the script's embedded Python → `DRIFT: version 0.97.1 != pyproject 0.97.2`.
  - Affected scope: every push of this branch; CI red regardless of code correctness.
  - Falsifier: `manifest.json` at `0.97.2` → the probe prints `DRIFT: none` and the job passes.
  - Fix: set `manifest.json` `"version"` to `0.97.2`; re-run `bash utils/frontdoor-check.sh` in the full clone and record its output alongside static.log.

- `[Should]` **Daily fallback citation differs from live citation for the same prompt.** `utils/daily_work_synthesis.py:350` uses `record_id or id`. Live JSONL rows carry `record_id` → `clio:<canonical>`. Rows served by the DB fallback (`clio.py:73,79`) carry only the consumer `id` plus `source_records`, so the same prompt cites `clio:<session>_<ts>_<hash16>`. Packet claims "stable Daily canonical IDs" and names fallback cites as in scope; the two paths are not joinable.
  - Observed input: synthetic row `{"record_id":"clio1-a","origin_id":"origin-a",…}` synced to a scratch DB, then `collect_packet` run once per path → `LIVE ids: ['clio:clio1-a']`, `DB-FALLBACK ids: ['clio:session_2026-10-02T22:00:00Z_ba9c736f19e7f60b']`.
  - Affected scope: DB-fallback rows whose `source_records` holds exactly one reference (the single-origin common case). Multi-origin rows may legitimately keep the consumer key.
  - Falsifier: a fixture asserting both paths yield the same evidence id for a single-origin row; if downstream never compares Daily ids across regenerations, Producer may disposition as documented divergence instead.
  - Fix: in `collect_packet`, when `row.get("source_records")` has length 1, cite its `record_id`; otherwise keep the consumer key. Keep `source_records` attached either way.

- `[Nit]` `prompts_unchanged` now also counts rows whose `source_records` were rewritten (`clio.py:157-163`); `ClioSyncResult` has no updated counter, so a provenance backfill pass reports as a no-op. Fix: add `prompts_updated` (default 0) or log the count.

- `[Nit]` Pre-existing, in the touched function: live rows lacking `agent`/`repo` keys raise `KeyError` at `daily_work_synthesis.py:360-361` and are dropped before the new hash fallback (`:351-353`) can cite them. Probe: legacy row `{"timestamp","session_id","prompt"}` only → `LEGACY(no agent/repo) ids: []`. The CHANGELOG/packet wording "metadata-free legacy records use stable hash" holds only for rows that carry `agent`/`repo` (post GH-139). Optional fix `row.get("agent", "")` / `row.get("repo", "")`; falsifier: a 2-hour log tail where every row has both keys makes it moot.

- `[Nit]` `mypy.log` "2 source files" matches `ci.yml:86` (`mypy src/`): `utils/daily_work_synthesis.py` is outside the typecheck scope. Claim is accurate as worded; just do not read it as covering the Daily script.

**Verified claims (cited)**

- `[Pass]` LF framing: `daily_work_synthesis.py:110` `raw.split("\n")` replaces `splitlines()`; the sync path (`clio.py:111`) iterates a text-mode file, which never split on U+2028/U+2029/U+0085, so it needed no change.
- `[Pass]` DDL additive only: `clio.py:43-44` `ALTER TABLE clio_prompts ADD COLUMN source_records TEXT NOT NULL DEFAULT '[]'`; CREATE TABLE and index unchanged (`clio.py:23-37`).
- `[Pass]` Primary IDs and semantic keys unchanged: `record_id = f"{session_id}_{ts}_{content_hash}"` (`clio.py:140-141`) untouched; `source_pk=row["id"]` (`clio.py:210`).
- `[Pass]` Provenance idempotence, multi-origin union, same-pass collision, reordered replay: `clio.py:148-164` unions sorted refs and only UPDATEs on change; `existing[record_id]` is refreshed after INSERT (`:173`) so a second same-pass record hits the UPDATE branch.
- `[Pass]` Read-only loader tolerates an unmigrated DB: `clio.py:70-71` substitutes `'[]' AS source_records`.
- `[Pass]` Facade respects selection and does not embed: `semantic_index.py:615` passes `use_registry_providers=True`; `normalize_sources` maps `all`/None to `WORK_SOURCES` (`:242-250`), so `clio`/`figma` only run when named; the registry loop (`:683-713`) only calls `upsert_document`. Embedding selection keys on `embedded_hash != content_hash` (`db/semantic.py:349-355`), so the metadata-only "updated" state does not queue re-embeds. Expect the first post-deploy `--source clio` backfill to report every existing CLIO doc as `updated` (row rewrite, not re-embed).
- `[Pass]` No guard/plist/schedule change: the 19-file diff stat lists no launchd, guard or schedule file.
- `[Pass]` Docs consistent: CHANGELOG 0.97.2, SOP "CLIO fleet consumer qualification", PROJECT doc "Studio follow-through" all disclose no live consumer refresh, guard deferral, and no other devices enabled; matches code.
- `[Unverified — needs clone run]` `controls-green.log` (7/7), `controls-base.log` (0/7), `focused.log` (41 passed), `mypy.log`, `static.log`. qualification-controls.py was read: its 7 checks match the seven claimed controls and the assertions are meaningful (idempotent insert count, 2-ref union, facade `total_documents==1` with 2 refs). Not executed in this worktree per protocol.

Pre-existing defects in touched files beyond the two Nits above: none found (`import hashlib` inside the loop at `clio.py:138` and the broad `except Exception` at `clio.py:77` are stylistic and already commented).

**VERDICT: FAIL**
**Basis:** The code change is sound and every packet claim I could measure holds, but the version bump is incomplete: `manifest.json` stays at 0.97.1 and the CI front-door gate fails on that drift. One-line fix, then re-review.

Handing off to Producer — go to the Producer window and say 'take your turn': bump manifest.json, disposition the [Should] and the Nits, record the frontdoor-check receipt.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
