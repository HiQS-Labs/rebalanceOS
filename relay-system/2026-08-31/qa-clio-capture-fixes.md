# RELAY · QA clio-capture fixes
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-08-31.
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
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **Verdict**
     (Approved | Changes requested | Blocked). **Review the whole file, not just the diff** (GH-268):
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
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(qa-clio-capture-fixes): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/clio-capture.sh** — the read-only path that
  `relay-drive.sh --artifact-file /Users/noelsaw/.claude/hooks/clio-capture.sh` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: aider   ·   Producer: claude-a
- Started: 2026-08-31
- Definition of Done: QA the updated regex filters in the script.
  1. Does the regex correctly match and strip `Used tool:` or `Ran command:` lines? Explain your reasoning with citations.
  2. Does the regex for tags use the `"gms"` flag (dot-all) so multi-line tags like `<task-notification>\n...\n</task-notification>` will be completely stripped?
  3. Is the newline squashing filter `\n[ \t]*\n[ \t]*\n+` replaced with exactly one backslash string `"\n\n"` so it doesn't emit literal `\n` characters in the JSON output?
## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
### Reviewer (aider) — r1
swept file: yes
Verdict: Approved

Findings:
- [Pass] `Used tool:` / `Ran command:` stripping is correct for line-start prefixes — `.relay-artifacts/clio-capture.sh:68`. The regex `^\"?(Ran command:|Viewed |Used tool:|The user has approved this document\\.)[^\\n]*\\n?` with `gm` anchors each line, matches the prefix case-insensitively, consumes to end of line, and removes the optional newline.
- [Nit] The same line-start regex does not match indented prefixes because it lacks `^\\s*` — `.relay-artifacts/clio-capture.sh:68`. If indented synthetic lines can occur, consider `^\\s*\"?`. Non-blocking for the stated DoD.
- [Pass] Tag stripping uses dot-all for multi-line tags — `.relay-artifacts/clio-capture.sh:66`. The `; ""; "gms")` flags include `s`, so `.*?` can span newlines to the matching `</\\1>` close tag. Note: `.relay-artifacts/clio-capture.sh:76` separately drops raw rows containing `<task-notification>` before cleaning; that is a capture filter, not a tag-regex defect.
- [Pass] Newline squashing replacement uses actual newline escapes, not literal backslash-n — `.relay-artifacts/clio-capture.sh:69`. The replacement is `"\n\n"` in the jq string, so the cleaned prompt contains two newline characters; JSON output may encode them as `\n`, but the data does not contain literal `\n` text.
- [Pass] Whole-file sweep found no additional Blocker/Should issues in the pre-existing script — `.relay-artifacts/clio-capture.sh:1-151`. Optional observations only: lock cleanup relies on stale-break if an unexpected failure occurs after lock acquisition (`.relay-artifacts/clio-capture.sh:104-128`), and full-log ID scanning may become costly as the log grows (`.relay-artifacts/clio-capture.sh:138-148`).

Pre-existing defects: none found at Blocker/Should severity.

Handoff: relay closed (Approved), no further turn needed.

<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->
▶ TAKE YOUR TURN (aider)
<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->
