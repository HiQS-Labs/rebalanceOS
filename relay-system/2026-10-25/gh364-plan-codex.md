# RELAY · gh364-plan-codex
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
6. **Commit only the relay file** (`relay(gh364-plan-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/2-WORKING/GH-364-CLIO-RUNTIME-INSTALLER.md` (plan only; no code written yet)
- Evidence (read-only, seeded): `.relay-artifacts/gh364-evidence.txt`. It holds Skills Army HQ's name rule and `add` arguments (outside this repo), the collection `.gitignore`, and this Mac's live CLIO install (hooks, plists, registrations, loaded jobs; private paths anonymised).
- Source to read for grounding: `utils/CLIO/INSTALL.md` (Install ~L27-305, Auto-sync ~L618-670, Codex/Agy ~L673-758, Uninstall ~L760-810), `test/clio-capture.sh` (heredoc extraction L18-20), `utils/CLIO/README.md`, `AGENTS.md`, `ARCHITECTURE.md` (catalog row), `pyproject.toml` (ruff exclude), `utils/pdda/check_banned_imports.py`, `utils/pdda/check_script_inventory.py`, `.agents/skills/clio/SKILL.md`, `PROJECT/PDDA.md`.
- Requirements (issue #364 and the operator-reviewed installer plan, decisions A–D settled, folder rename chosen by the operator): one installer, run from the Skills Army–deployed copy, that installs, repairs, upgrades, checks and removes CLIO capture on a Mac. Hooks are symlinks into the deployed copy (decision A); HQ is unchanged and only records a prerequisite (B); `CLIO_MIN_PROMPT_CHARS` 20 is already the default (C); the installer traces to a source revision, makes no hand copies, backs up and adopts an existing hand install, never rewrites the exporter schedule, and never runs from a task clone. Acceptance is listed in the plan's suite cases.
- Operational envelope: one operator, about four Macs, bash 3.2 + jq + python3, launchd. Grade against commensurate complexity: no daemon, no HQ changes, no multi-user threat model, no generic installer framework.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-25
- Definition of Done: the plan meets every requirement with the least machinery; the rename is complete and leaves history alone; the desired state matches what INSTALL.md installs today (without rewriting the exporter plist); adopting a hand install is safe and reversible; the checks are falsifiable with red controls; and the gates are handled. Answer explicitly:
  1. Is renaming to `utils/clio-capture` the right fix for the HQ name rule, and is the reference list complete and correct (including what is deliberately left as history or fixture data)?
  2. Does generating the writer and shim into `~/.claude/hooks` (tracked by checksum), instead of into the collection, respect decision A and the "never dirty the Pulse tree" rule? Is the `stale` status, plus `upgrade`, an adequate refresh for them?
  3. Do the symlinked helpers work with the writer's `$(dirname "$0")/clio-store.py` lookup and the plists' `~/.claude/hooks/<script>` paths?
  4. Are the backup-before-replace, receipt-scoped uninstall, and "create tailer plists only when absent; never the exporter" rules safe for this Mac's live state, as shown in the evidence?
  5. Is collapsing repair/upgrade into an idempotent `install` acceptable against the plan's four verbs?
  6. Are suite cases 1–7 sufficient and bounded, and is anything missing (e.g. Linux without launchd, a missing `~/.zcode`)?
  7. Anything over-engineered?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
