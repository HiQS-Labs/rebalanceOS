# RELAY · GH-196 shutdown MVP feasibility and safety
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
6. **Commit only the relay file** (`relay(gh196-shutdown-design): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md`
- Reviewer: agy   ·   Producer: codex
- Started: 2026-09-07
- Definition of Done: MVP implementation plan is grounded, minimally scoped, safe, portable, and falsifiable. No code is built yet; textual plan approval only.
- Handoff: cli-driven (agy), shipped relay-xyz, review-only ALLOW_PATHS.

### Read set and questions

Read the entire plan, `PROJECT/4-MISC/recon-gh196-shutdown.md`, and the user requirements in `relay-system/2026-09-07/gh196-shutdown-completeness.md`. Check actual source files named in the plan: both daily skills/scanners, existing collect.sh, DB connection/read/registry/config seams. Treat the old graph as a lead only. Do not run the ledger-writing scanner or runtime data operations.

1. Does the plan extend the existing scanner/reader and keep one writer per artifact? Can basic deployment actually work from a neutral CWD with no Rebalance runtime? Are paired skills/compatibility entry assumptions implementable?
2. Does activity admission honor edits within old repos, dirty/untracked/deleted work, branch changes, calendar-day boundaries, distinct clones, and honest unknowns? What is the cheapest missing case that would invalidate the report?
3. Can the two-pass design notice edits that leave porcelain strings unchanged, distinguish its own scan/output from other activity, and exclude ongoing repo groups without pretending to prove inactivity? Are its limits proportionate to an MVP?
4. Does optional enrichment genuinely avoid schema writes, refresh/publishing/secrets, duplicate SQL and stale context as safety clearance? Are existing read seams and boundedness claims accurate?
5. Does the handoff preserve deliberate PR deferrals and the next phase of an unfinished arc through a later daily cycle? Are snapshot/history/latest ownership and partial writes well specified?
6. Is report-only default and scoped approval enforceable without a second cleanup engine? Does delegation describe actual merge-cleanup capability or assume unavailable guarantees? Are live revalidation, dependency failures and private local output boundaries explicit?
7. Is the acceptance matrix falsifiable with nonempty controls, and does each requirement map to a check? What is missing or overengineered, with smallest correction first? Keep SOLID proportional: no speculative abstractions.
8. Does coordination with open PR #195 and issues #150/#192 avoid duplicate work and scope creep? Is the plan a useful finishable MVP instead of a disguised platform project?

Append one Reviewer block with `swept file: yes`, Basis: textual only, graded findings and file:line citations, and literal standalone `VERDICT: PASS` / `VERDICT: FAIL` / `VERDICT: PARKED` matching the human verdict. Findings must distinguish genuine plan blockers from optional future improvement. Approved/PASS is planning approval, not implementation safety proof. Do not edit the artifact, execute tests/runtime operations, commit code, or push; the shim owns the reviewer commit/token.

The earlier completeness turn omitted Basis and was rejected (driver exit 8), despite finding all requirements mapped. Reconfirm its mapping against the current artifact; do not rely on its invalid approval. Your block MUST include the following plain, unbolded field lines with real content (not merely a description in your final chat):

```text
### Round 1 · Reviewer · agy
Basis: textual only — reviewed the plan and cited source; no implementation executed
swept file: yes
Verdict: Approved OR Changes requested OR Blocked
VERDICT: PASS OR FAIL OR PARKED
```

Choose one value for each verdict, not the literal OR list. Append graded findings and Answers with actual file:line citations. The absolute relay path supplied by the driver has a corresponding relative path inside your current isolated worktree; use that worktree-relative path. Do not search the whole filesystem. Do not change the original checkout directly. All plan phases are upcoming: review the phase-qa rubric (DRY, proportional SOLID, observability, phase-specific tests), but do not claim implementation tests or deployment happened.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Round 1 · Reviewer · agy
Basis: textual only — reviewed the plan and cited source; no implementation executed
swept file: yes
Verdict: Approved
VERDICT: PASS

- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:114-118`: Extends existing scanner, enforces one writer, and specifies basic mode uses only standard library/Git without Rebalance runtime.
- [Should] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:118`: To achieve neutral CWD execution, explicitly state that existing Rebalance imports in `scan_unclosed_loops.py` must be moved inside functions or guarded. Fix: Note to guard imports when extending.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:125-145`: Activity admission correctly discovers without mtime filters, handles worktrees, bounds dates, and classifies missing/detached state as explicit unknowns.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:154-163`: Two-pass design uses content fingerprints, and excludes entire logical repo groups based on locks/processes.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:203-214`: Optional enrichment uses `db_connection_readonly` and explicitly forbids schema creation/refresh.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:188-190`, `231-233`: Deliberate deferrals are preserved; unique run IDs and atomic writes prevent partial reads.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:217-229`: Execution is report-only by default and cleanly delegates to `merge-cleanup` by name.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:286-297`: The acceptance matrix (A1-A12) is falsifiable with concrete red controls.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md:78-82`: Adjacency coordination is defined; it avoids duplicate work and explicitly does not wait for #150/#192.
- [Pass] `TESTS-RESULTS/2026-09-07+GH-196/plan-r1.md`: Swept the artifact; no pre-existing defects found.

relay closed (Approved), no further turn needed

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
