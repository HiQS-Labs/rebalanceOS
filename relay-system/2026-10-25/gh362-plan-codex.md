# RELAY · gh362-plan-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-25.
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
6. **Commit only the relay file** (`relay(gh362-plan-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/2-WORKING/GH-362-CLIO-UPSTREAM-SYNC.md` (plan only; no code written yet)
- Evidence (read-only, seeded): `.relay-artifacts/gh362-evidence.txt`. It holds the exact `diff -u` of each synced path (this repo vs XYZ-CLIO `bacd26f`; XYZ-CLIO is not in this clone), proof that the tests and fixtures are already identical, the ruff output for the two upstream Python files under this repo's config, and the writer's `dirname "$0"` helper calls.
- Source to read for grounding: `utils/CLIO/` (current), `utils/pdda/check_script_inventory.py` and `utils/pdda/script_inventory_baseline.json` (L58-60), `pyproject.toml` `[tool.ruff] extend-exclude`, `.githooks/pre-push` (ruff stages ~L111-112), `.github/workflows/ci.yml` (ruff steps), `.agents/skills/clio/SKILL.md`, `AGENTS.md` (CLIO pointer L14), `PROJECT/PDDA.md`, `ROUTER.md`.
- Requirements (issue #362, operator decision D): make `utils/CLIO` byte-identical to XYZ-CLIO `bacd26f` (adding `clio-store.py` and its test); declare this copy CLIO's upstream where maintainers will see it; keep every repo gate green; install nothing.
- Operational envelope: a personal repo and a ~4-Mac fleet; this is a file sync plus doc lines. Grade against commensurate complexity: no new suites, services or automation (the publisher is a separate later step).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-25
- Definition of Done: the plan's recon matches the evidence, the sync list is complete (nothing in XYZ-CLIO's `utils/CLIO` or CLIO tests left out, nothing Rebalance-only clobbered), the gate decisions are sound, the upstream declaration is visible to maintainers, and the checks have red controls. Answer explicitly:
  1. Is the sync list complete and correct? Does any Rebalance consumer depend on behaviour or anchors the new INSTALL.md or the scripts remove?
  2. Script-inventory ratchet: is growing the baseline with exactly one entry the right call, versus the #249 relocation precedent or a pragma exemption? Cite the checker's rules.
  3. Ruff: is extending `extend-exclude` to `utils/CLIO` and `test/clio-store.py` justified (byte-identity for the 0c publisher), versus fixing the five findings and reformatting here? Does the exclude hide anything first-party that should stay linted?
  4. Is the README "Upstream" section plus the AGENTS.md line enough for maintainers to see the direction, given INSTALL.md stays upstream bytes until 0c?
  5. Are PDDA/RELEASES intake and the docs gate handled per `PROJECT/PDDA.md` (capture, park, rate, promote, repoint)?
  6. Anything over-engineered, or a requirement missed?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
