---
gh_issue: 336
source: https://github.com/HiQS-Labs/rebalanceOS/issues/336
title: "git-pulse-sync-repair 2.4e: stuck-rebase backup patch drops binary edits (needs --binary)"
status: "Captured — plan in QA on fix/rebalanceOS-gh336-binary-safe-rebase-backup-2026-10-19"
created: 2026-10-19
updated: 2026-10-19
owner: noel
doc_type: bugfix
goal: >
  Make the stuck-rebase backup in git-pulse-sync-repair complete for binary edits, so the
  operator's "abort with backup" decision (GH-334) holds as written. Keep it a wording fix to an
  existing procedure, finished and redeployed in one bounded session.
effort: 1
complexity: 1
risk: 2
phases: 1
ratings_provisional: false
roadmap_exempt: false
---

# GH-336: binary-safe stuck-rebase backup

## Status

| What was just completed | What's next |
|---|---|
| Sanity check: **fix now, minimal**. Triangulate card and bounded plan written (below). | Codex plan QA (relay, at most 2 rounds), then implement. |

## Observed problem

Step 2.4e of `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:99-100` (merged in #335, e5a42ed)
saves the in-progress edits with `git -C "$PULSE" diff HEAD > "$G/pulse-repair-$S.patch"`. Without
`--binary`, a changed binary file is written as `Binary files a/x and b/x differ`, which carries no
content. The step's own check ("non-empty when `git diff HEAD` is non-empty") still passes. Step 2.4f
(`rebase --abort`) then resets the file, and the edit is gone. The two backup branches do not hold it:
`-head` is the rebase's HEAD commit, not the working tree. The plan repeats the command at
`PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md:95`. `SOP.md`'s GH-334 paragraph does not quote it
(`git grep -n 'diff HEAD' -- '*.md'`).

## Sanity check (2026-10-19)

- **Real?** Yes. Scratch repro: after `git rebase --abort`, a plain `git diff HEAD` patch cannot
  restore a binary edit (`cannot apply binary patch to 'b.bin' without full index line`), so the edit
  is lost.
- **Credible harm on the actual data?** Low. `~/git-pulse-sync` tracks 327 files, 0 of them binary
  (`git diff --numstat <empty-tree> HEAD`, `-` rows: 0). There were 0 binary changes in its last 200
  commits. Step 2.4 did not run in the 2026-10-19 repair on noels-mac-studio, so nothing was lost.
- **Why fix anyway?** The operator approved the abort *only with a verified backup* (GH-334 decision;
  `SOP.md` GH-334 exception). The current procedure claims a guarantee it does not keep. The fix is
  one flag plus one check.
- **Disposition:** fix now, minimal. PRS `rated 30/35/50/90`:
  - priority 30: not blocking, step 2.4 is rare
  - severity 35: silent loss of an operator edit, but no binaries exist today
  - appeal 50: neutral
  - effort 90: one flag

## Triangulate card

```
SUBJECT: make step 2.4e's backup patch keep binary edits
CELL:    reversible x crossing (the vendored copy rides the pulse repo to every device) -> recon-lite + falsify
GROUND:  the command appears in SKILL.md:99-100 (procedure) and the GH-334 plan :95 (spec). SOP.md
         does not quote it. The installed copies are Skills Army links to Deployed Skills/
         git-pulse-sync-repair (6 app roots on this Mac); other devices get it via the pulse pull.
FALSIFY: belief "git diff --binary HEAD captures every tracked edit during a conflicted rebase,
         and git apply restores it onto the -head backup". It SURVIVED in a scratch repo:
         - setup: conflicted text file resolved but unstaged, conflicted binary overwritten,
           unrelated binary staged
         - result: patch, abort, then apply onto a worktree at bk-head restored all three byte for byte
         - alternative: `git stash create` FAILS while the index has unmerged paths, so it is rejected
SMALLEST:`--binary` on one command + a stricter check line, mirrored in the plan.
         - skipped: tar or file-copy backup; add when a --binary patch is observed failing to restore
         - skipped: untracked-file backup; untracked files already survive the abort
UNKNOWNS:Git LFS pointers or submodules in the pulse repo would change this. Settle with
         `git -C ~/git-pulse-sync lfs ls-files` and `.gitmodules`; today neither is in use
         (no .gitmodules, 0 binaries).
```

## Plan (one PR, timeboxed)

**Scope:**
1. `SKILL.md` 2.4e: `git -C "$PULSE" diff --binary HEAD > "$G/pulse-repair-$S.patch"`. Change the
   check to "the patch must be non-empty when `git diff HEAD` is non-empty, and must contain no
   `Binary files … differ` line". Add a one-line restore hint:
   `git -C "$PULSE" worktree add --detach <dir> pulse-repair-backup/$S-head && git -C <dir> apply <patch>`.
2. The GH-334 plan, step (e) at `:95`: mirror the same wording, with no other changes.
3. Fold-in, same file, wording only (from the GLM 5.3 QA Nits on #335). Each is one line, and each is
   dropped on the first review pushback rather than debated:
   - 2.3 and 3.1: use `"$RB/.venv/bin/rebalance"` instead of a bare `rebalance`. This Mac has no
     `rebalance` on PATH.
   - Step 0: if `$RB` and the plist's `ProgramArguments` root differ, adopt the plist's root and
     re-run doctor.
   - 2.1: loading the collector (`RunAtLoad` true) starts a run immediately, so record step 3's
     baselines first, or treat that run as the observed one. This happened in the 2026-10-19 run.

**Verification (no new tests; repo policy):**
- Smoke, main path: re-run the scratch repro with the exact new command line from `SKILL.md`. All three
  edit kinds must restore.
- Red control: the old command loses the binary edit in the same scenario.
- Adjacent path: a rebase whose conflicts are text-only. The patch has no binary hunks, still applies,
  and the stricter check passes.
- Record the commands, output and the repro script (`.sh.txt`) under
  `TESTS-RESULTS/2026-10-19+GH-336/`, with `provenance.jsonl`.
- Gate: docs-only paths, so run the pre-push hook's static gate; no full suite.

**Delivery:**
1. Final Codex QA (relay): 1 round, 2 at most.
2. PR to `development`; the operator merges.
3. After the merge, refresh the installed copy with the Skills Army HQ CLI only:
   `intake.py --apply update git-pulse-sync-repair --source <clean development checkout>/experimental/git-pulse/git-pulse-sync-repair`,
   then `sync.py --status` and `sync.py --apply`, then verify the links. Other devices receive it
   through the pulse.

**Non-goals:**
- Redesigning the backup (tar, file copies, stash).
- Backing up untracked files.
- LFS or submodule support.
- Changing step 2.4's other prerequisites.
- The collector's "Skipping <repo>: not a git repo" log noise (separate; likely macOS privacy
  access, unverified).
- Closing #333 (operator).

## Timebox and pivots

Budget: about 90 minutes of active work, plus waiting on reviewers. Stop rules:

| Trigger | Pivot |
|---|---|
| Plan QA asks for a backup redesign, LFS, untracked files or a new script | Decline as unproven generalization unless it cites an observed input in the pulse repo. Park it. |
| Plan QA disputes the GLM Nit fold-in | Drop the fold-in. Ship the `--binary` fix alone. |
| The smoke shows `--binary` failing to restore some case | Fall back to saving the changed files themselves (`git diff --name-only -z HEAD` → `tar` into `$G/pulse-repair-$S.tar`) as the 2.4e mechanism. Re-QA once. |
| Plan QA reaches round 2 without Approved | Ship the one-flag fix as a simple change. Record the open points in the issue. |
| Final QA reaches round 2 without Approved, or the relay round cap (3) | Stop and ask the operator. Do not start round 3. |
| Elapsed active time passes 2 hours | Ship whatever is verified (at least the one-flag fix). Park the rest with a revisit trigger. |
| A new unrelated defect appears | File it. Do not fold it in. |

## Acceptance

- `SKILL.md` 2.4e saves a `--binary` patch, and its check rejects `Binary files … differ`.
  - Falsifier: the smoke red control restores the binary edit with the old command. That would mean
    the defect was misdiagnosed.
- The plan step (e) matches `SKILL.md`.
- The smoke receipt shows all three edit kinds restored under the new command, and the binary edit lost
  under the old one.
- After merge, the deployed copy's 2.4e contains `--binary` in every enabled app root
  (`grep -c 'diff --binary HEAD'` in each linked `SKILL.md`, which must be 1).
