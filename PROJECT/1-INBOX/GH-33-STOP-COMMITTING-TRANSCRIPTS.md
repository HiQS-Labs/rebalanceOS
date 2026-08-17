---
gh_issue: 33
source: https://github.com/HiQS-Suite/rebalanceOS/issues/33
title: "GH-33 Stop committing relay transcripts & reclaim git history bloat"
status: "Proposed (1-INBOX — not yet active)"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: hygiene
goal: >
  Ensure transcript generation never pollutes git history by enforcing strict .gitignore rules
  for relay-system/ and finalizing the archive of the legacy bloated repository.
effort: 2
complexity: 1
risk: 2
phases: 2
ratings_provisional: true
roadmap_exempt: true
---

# GH-33 — Stop Committing Relay Transcripts & Reclaim Git History

## Status

| What was just completed | What's next |
|---|---|
| New repo `HiQS-Suite/rebalanceOS` created with clean history (.git at 18MB, down from 433MB; 743 tracked files, 0 tracked transcripts or sqlite blobs). | Phase 0 verification of .gitignore rules and completion of legacy repo archival checklist. |

## Why

In the previous repository checkout, `.git` expanded to 433MB due to:
- Committed SQLite blobs in `ask_self/index/rebalance-OS.sqlite` (~57MB total).
- 167 tracked files in `relay-system/` including `.codex.md` transcripts up to 1.6MB each.

While the new repo starts fresh, we must enforce structural guards so transcripts are never tracked, and complete the GH-291 Phase 4 retirement of the legacy repo.

## Table of contents

- [Phase 0 — Prior art review & research (Lock in the plan)](#phase-0--prior-art-review--research-lock-in-the-plan)
- [Phase 1 — Gitignore audit and pre-commit guard](#phase-1--gitignore-audit-and-pre-commit-guard)
- [Phase 2 — Finalize upstream repo archival (GH-291)](#phase-2--finalize-upstream-repo-archival-gh-291)
- [Lessons Learned (For Future Agents)](#lessons-learned-for-future-agents)

## Phase 0 — Prior art review & research (Lock in the plan)

**Prior art & Code pointers:**
- `.gitignore`: ignores `relay-system/`, `marathon-system/`, `.tick/`, `*.sqlite`, `temp/`.
- `utils/pdda/pdda-lib.sh`: checks and guards.
- `PROJECT/2-WORKING/GH-291-REPO-CONSOLIDATION.md` (or archived equivalent): org transfer and retirement steps.

**Research / Inventory:**
1. Check `.gitignore` in repo root to confirm patterns `relay-system/` and `marathon-system/` are active.
2. Confirm `git ls-files relay-system/` returns zero tracked files.

**Acceptance criteria for Phase 0:**
- Git status and `.gitignore` verified clean.

## Phase 1 — Gitignore audit and pre-commit guard

- [ ] Audit `.gitignore` for complete coverage of agent transcripts, SQLite files, logs, and venvs.
- [ ] Add a contract test or pre-commit check in `tests/test_repo_hygiene.py` verifying no files in `relay-system/` or `.sqlite` files are tracked in git.
- [ ] Add README note on local cache hygiene ("What's safe to delete").

**QA gate:**
- `git status` clean; `git ls-files -- "relay-system/*" "*.sqlite"` returns empty.

## Phase 2 — Finalize upstream repo archival (GH-291)

- [ ] Complete issue transfer / synchronization with old repo.
- [ ] Rotate OAuth credentials if previously exposed.
- [ ] Archive `Hypercart-Dev-Tools/rebalance-OS` as read-only.

**QA gate:**
- Upstream repo archived; all ongoing development rooted in `HiQS-Suite/rebalanceOS`.

## Lessons Learned (For Future Agents)

_(fill in before moving to `PROJECT/3-COMPLETED`)_
