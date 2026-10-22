# RELAY · rebalanceOS GH-329+GH-348 final QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-21.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 1 / 3

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
  Full-suite result is appended below by the Producer before your turn.
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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
