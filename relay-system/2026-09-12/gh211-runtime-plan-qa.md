# RELAY · GH-211 bounded runtime recovery plan QA
<!-- Single source of truth. Read the entire file before acting. -->

NEXT: Reviewer
STATUS: Open
ROUND: 1 / 4

## ▶ TAKE YOUR TURN — read this first

1. Read this whole file and act only when `NEXT` names your role.
2. Reviewer: grade findings `[Blocker]`, `[Should]`, `[Nit]`, or `[Pass]`, cite file:line, propose a
   concrete fix, declare `swept file: yes|no`, and set `Verdict: Approved|Changes requested|Blocked`.
   Do not edit product or plan files.
3. Producer: disposition every finding, apply accepted fixes, and append one response block.
4. Append one block at the bottom; never rewrite earlier turns. Flip `NEXT`, update `STATUS`, and
   increment `ROUND` only when the Producer opens another cycle.
5. Commit only this relay file and explicitly name the next role. Reviewer alone may close Approved.

## Setup

- Artifact: `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md`
- Recon: `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY/recon-bounded-runtime.md`
- Reviewer: codex · Producer: claude-a
- Definition of Done: the plan is grounded, minimal, diagnosable, blast-priced, and independently
  executable without risking existing runtime/database/Git work or activating 3-Eyes.

Read the artifact and Recon Map in full, then inspect `SCHEDULER.md`, `SOP.md`, `AGENTS.md`, and cited
code/tests as needed.

Questions:

1. Does every proposed change follow a verified current call/write path, with unsupported claims
   exposed as gates rather than assumptions?
2. Is extending the existing job guard and scheduler policy the smallest coherent fix, without
   duplicating supervision or reactivating 3-Eyes?
3. Are timeout semantics, exit codes, process-tree reaping, lifecycle evidence, and per-job ceilings
   implementable and testable without guessing?
4. Do stack, doctor, pulse health, Git publication, and semantic repair close the actual false-green
   paths without expanding public schemas or destructive authority?
5. Are database and dirty-Git recovery shields, tripwires, backups, and rollback sufficient to
   preserve unique local work?
6. Does every phase have falsifiable proof: red controls, non-empty artifacts, full gates,
   independent final QA, safe deployment, and handoff to GH-210?
7. Flag missing scope, overreach, unsafe ordering, contradiction, or weak acceptance. Cite file:line
   and give the cheapest correction.

## Ground rules

1. This thread is the single source of truth; agents share no memory.
2. One turn is one appended block. Findings are bullets, not essays.
3. Reviewer changes only this relay file; no push.
4. The relay ends only on Reviewer Approved or escalates at round four.

## Log

<!-- ↓↓↓ NEXT TURN goes here; marker stays last ↓↓↓ -->
