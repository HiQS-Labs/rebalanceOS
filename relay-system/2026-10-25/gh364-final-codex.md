# RELAY · gh364-final-codex
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
6. **Commit only the relay file** (`relay(gh364-final-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: the implementation on this branch: the folder rename to `utils/clio-capture` (from the old uppercase name) with its reference updates; `utils/clio-capture/SKILL.md`; `utils/clio-capture/clio-runtime.sh`; `test/clio-runtime.sh`; the README/INSTALL notes, gates and version. You cannot run git: `.relay-artifacts/gh364-impl.diff` is `git diff -M origin/development...HEAD` (renames shown as renames). Read the current files for the full scripts.
- Approved plan: `PROJECT/2-WORKING/GH-364-CLIO-RUNTIME-INSTALLER.md` (plan QA `relay-system/2026-10-25/gh364-plan-codex.md`, Approved R3).
- Test evidence: `TESTS-RESULTS/2026-10-25+GH-364/` (README, suites incl. two mutation red controls, read-only live smoke).
- Operational envelope: one operator, about four Macs, bash 3.2 + jq + python3, launchd. Grade against the approved plan and commensurate complexity.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-25
- Definition of Done: the code matches the approved plan (rename scope, desired state, adoption with backup, drift-safe receipt-scoped uninstall, source guard, preview-by-default, never the exporter plist), the suite and red controls substantiate each acceptance item, the gates are handled, and nothing outside scope changed. Answer explicitly:
  1. Is the rename complete for live references, with history and the two GitHub test fixtures left alone?
  2. Does `clio-runtime.sh` implement each plan item? Check in particular: `item_state` (link / generated / foreign / stale / wrong-target); the heredoc extraction matching the test marker; backups keeping the oldest original; registrations recorded only when added; plists created only when absent and loaded; the receipt contents; drift-safe uninstall with a trimmed receipt and exit 1.
  3. Any path where `install --apply` or `uninstall --apply` could lose a user's file, write outside the plan's paths, or leave a half state silently? Are there bash 3.2 or `set -u` hazards?
  4. Do suite cases 1–8 assert what they claim, and do the two mutations really prove cases 4 and 8?
  5. Is the live smoke honest and read-only (fingerprint unchanged)?
  6. Is SKILL.md accurate, given HQ's name rule and the "never touches" list?
  7. Anything over-engineered or missing?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
