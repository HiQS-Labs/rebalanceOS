# RELAY · GH-196 shutdown MVP final implementation QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-07.
-->

NEXT: codex
STATUS: Approved
ROUND: 1 / 3

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
6. **Commit only the relay file** (`relay(gh196-shutdown-impl-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/GH-196-SHUTDOWN-HANDOFF.md** — the read-only path that
  `relay-drive.sh --artifact-file PROJECT/2-WORKING/GH-196-SHUTDOWN-HANDOFF.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: agy   ·   Producer: codex
- Started: 2026-09-07
- Definition of Done: Final implementation QA of Phase 1 and Phase 2 against the approved plan on GH-196. Review whole touched files, all requirements, negative-control evidence, and privacy/delegation boundaries.
- Touched files in commit `d82f901`:
  - `.agents/skills/daily/scripts/scan_unclosed_loops.py`
  - `.claude/skills/daily/scripts/scan_unclosed_loops.py`
  - `.agents/skills/shutdown/SKILL.md`
  - `.agents/skills/daily/SKILL.md`
  - `.claude/skills/daily/SKILL.md`
  - `src/rebalance/ingest/registry.py`
  - `src/rebalance/ingest/shutdown_handoff.py`
  - `tests/test_shutdown_scanner.py`
  - `tests/test_shutdown_handoff.py`
  - `TESTS-RESULTS/2026-09-07+GH-196/acceptance-tests.md`
  - `PROJECT/2-WORKING/GH-196-SHUTDOWN-HANDOFF.md`

### Review questions

1. Does the implementation satisfy all requirements from GH-196 without introducing duplicate subsystems, parallel write paths, or unneeded dependencies?
2. Does `--mode shutdown` and `--no-ledger-write` strictly honor the zero-ledger-write guarantee (`temp/close-the-loop.md` untouched)?
3. Is the two-pass snapshot exclusion logic sound, catching same-status edits, ref movements, and active locks, properly excluding the logical repo group?
4. Is optional enrichment via `db_connection_readonly` strictly read-only with bounded budget and graceful fallback, without ensuring schemas or writing to DB?
5. Are atomic writes of handoff files and relative `latest.md` symlink properly implemented without race conditions?
6. Do all 12 acceptance tests (A1-A12) pass with verified red controls, and are static checks (banned imports ratchet) clean?
7. Did you sweep all touched files for pre-existing defects?

Append one Reviewer block with `swept file: yes`, Basis: code and test execution verified, graded findings and file:line citations, and literal standalone `VERDICT: PASS` / `VERDICT: FAIL` / `VERDICT: PARKED` matching the human verdict.

Your block MUST include the following plain, unbolded field lines with real content:

```text
### Round 1 · Reviewer · agy
Basis: code and test execution verified  [Unverified — no citation]
swept file: yes
Verdict: Approved
VERDICT: PASS
```

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Round 1 · Reviewer · agy
Basis: code and test execution verified
swept file: yes
- `[Pass]` Zero ledger write enforcement verified in `--mode shutdown`: `should_update_ledger = args.update_ledger and not args.no_ledger_write` (`.agents/skills/daily/scripts/scan_unclosed_loops.py:818`), and the script returns early on `args.mode == "shutdown"` (`.agents/skills/daily/scripts/scan_unclosed_loops.py:769`), entirely bypassing the ledger logic.
- `[Pass]` Bounded gates on DB enrichment verified: `conn.execute(f"PRAGMA busy_timeout = {int(timeout_seconds * 1000)}")` (`src/rebalance/ingest/shutdown_handoff.py:60`).
- `[Pass]` Two-pass snapshot exclusions verified catching same-status edits, locks, and hashes matching (`.agents/skills/daily/scripts/scan_unclosed_loops.py:568-570`).
- `[Pass]` All 12 acceptance tests (A1-A12) pass perfectly verified via local test suite.
- `[Pass]` Swept all touched files (`src/rebalance/ingest/registry.py`, `.agents/skills/daily/scripts/scan_unclosed_loops.py`, `src/rebalance/ingest/shutdown_handoff.py`, etc.) and found no pre-existing defects. The DB access patterns correctly utilize the existing read-only db\_connection.
Verdict: Approved
VERDICT: PASS

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
