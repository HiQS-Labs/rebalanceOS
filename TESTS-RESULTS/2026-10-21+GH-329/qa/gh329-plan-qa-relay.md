# RELAY · rebalanceOS GH-329+GH-348 plan QA (codex)
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
6. **Commit only the relay file** (`relay(rebalanceos-gh-329-gh-348-plan-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review (the PLAN, before any implementation): `PROJECT/2-WORKING/GH-348-RETIRE-ROADMAP-MD.md`
- Evidence: `TESTS-RESULTS/2026-10-21+GH-329/RECON.md` (read-only recon, file:line cited)
- Requirements: GitHub issues HiQS-Labs/rebalanceOS #329 and #348. Their acceptance lists are reproduced in the plan's
  "Tracked issues" and "Plan" sections. Run `gh issue view 329` and `gh issue view 348` if you can; otherwise use the plan.
- Source paths to check claims against:
  - `utils/py/releases_app.py` (the root fork).
  - `utils/pdda/pdda.sh` (`check_roadmap`, `check_roadmap_coverage`), `utils/pdda/prior-art-check.sh`.
  - `scripts/check_doc_links.py`, `src/rebalance/ingest/releases_scan.py`, `tests/test_releases_app_dump_parse.py`.
  - `.pdda-mode`, `.gitignore:75`, `pyproject.toml` (ruff exclude), `ROADMAP.md`, `ROUTER.md`, `AGENTS.md`.
  - XYZ Forge prior art: a read-only clean clone of Forge origin/development `1573dd4b7` (the exact revision the plan
    re-vendors) sits OUTSIDE your worktree at `$FORGE` = `/private/tmp/claude-501/-Users-noelsaw-Documents-GH-Repos-rebalanceOS/fd0b2af5-dab6-48a5-bdad-092951e3fb8a/scratchpad/forge-dev`. Read
    `$FORGE/utils/py/releases_app.py`, `$FORGE/utils/pdda/pdda.sh`, `$FORGE/utils/py/wave_reconcile.py`,
    `$FORGE/relay-automation/xyz-vendor.sh`, and `git -C $FORGE show 9e5c79979 --stat` (GH-269). Read only.
    `.xyz/` is gitignored and will not be in your worktree.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-21
- **Operational envelope:** single-operator local developer tooling. One repo and one SQLite ledger file, committed
  as `releases.db` + `releases.sql`, with no concurrent writers beyond git merges. Grade against the stated
  requirements and commensurate complexity. Do not ask for multi-tenant, distributed-lock or enterprise rollback
  machinery. This repo forbids new script/LaunchAgent sprawl (ROUTER.md GH-241) but allows pytest tests.
- Definition of Done (for the plan):
  - Every #329 and #348 requirement maps to a plan step or to an explicit, reasoned non-goal.
  - Plan claims are grounded in the cited paths.
  - It extends the existing writer (`releases_app.py roadmap` verbs) rather than building a parallel one.
  - Blast radius, ordering (phase 1 before 2; the marker flip and file delete together), rollback and falsifiable
    checks with red controls are adequate.
  - The ratings (#348 70/55/50/25, #329 75/60/50/45 provisional) are grounded.

### Questions for the Reviewer
1. **Re-vendor vs supported path.** #329 asks for "Forge's supported path rather than copying files by hand". Recon
   §0.3 says `xyz-vendor.sh` writes only `.xyz/` (gitignored) and never the tracked root `utils/py/releases_app.py`
   that the governed skills run first. Is a hand re-vendor of one file at a pinned SHA, plus one marked local delta
   (#322 guard), the right reading? Check `$FORGE/relay-automation/xyz-vendor.sh` to confirm or refute.
2. **#322 local delta.** Forge's `parse_dump` lacks the `_is_single_values_tuple` guard; the measured result is 2 of 6
   tests failing. Is carrying it as one marked delta acceptable, or does it hide a real Forge defect? (Upstreaming it
   is out of this repo's scope and goes to a follow-up.)
3. **Schema v5→v9 in one commit with the app.** Is that ordering safe? Is any caller in this repo still running the
   v5 code path (check `src/rebalance/ingest/releases_scan.py` PRAGMA tolerance, `tests/`)?
4. **Re-keying titles (step 5).** Is a one-off scratch transform acceptable when it is not committed but its receipt
   is? Are the keying rules right: HiQS-Labs and HiQS-Suite URLs only, never Hypercart, skip duplicate or multi-issue
   entries, never rewrite URLs? Does Forge's `_roadmap_gh_number` / `_roadmap_issue_url` (in
   `$FORGE/utils/py/releases_app.py`) key `**#N — Title** ([#N](url))` the way the plan assumes? Will
   `reconcile-state` handle a HiQS-Suite `issue_url` correctly (it is the same issue database through GitHub's
   redirect), or should those stay unkeyed?
5. **Flip atomicity (step 6).** Marker and file deletion in one commit: are there consumers that read `.pdda-mode`'s
   first line only (`utils/pdda/pdda-lib.sh`) and would misparse the new line?
6. **Coverage port (step 7).** Is porting only `check_roadmap_coverage` plus the GH-492 drift block from Forge's
   `pdda.sh` enough, or does the DB branch depend on helpers that this repo's older `pdda.sh`/`pdda-lib.sh` lacks?
7. **Doc links (step 8).** Is repointing historical PROJECT links to a GitHub permalink of the last ROADMAP.md
   acceptable, compared with leaving them and allowlisting? Note the repo memory rule: old-org URLs in history are not
   rewritten. These links point at the in-repo file, not at an org URL.
8. **Non-goals.** `wave_reconcile.py` and the hosted `wave-reconcile.yml` are left in `.xyz/` and not vendored into
   the tracked tree (recon §4: harness dependencies). Is that a defensible reading of #329, or a missed requirement?
9. Anything missing, wrongly scoped, or over/under-engineered? Cite file:line.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
