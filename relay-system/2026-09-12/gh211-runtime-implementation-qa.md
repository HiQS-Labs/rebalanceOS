# RELAY · GH-211 bounded runtime recovery implementation QA
<!-- Single source of truth. Read the entire file before acting. -->

NEXT: claude-a
STATUS: Changes requested
ROUND: 1 / 4

## ▶ TAKE YOUR TURN — read this first

1. Read this whole file and act only when `NEXT` names your role.
2. Reviewer: inspect the complete branch diff against `origin/development`. Grade findings
   `[Blocker]`, `[Should]`, `[Nit]`, or `[Pass]`; cite file and line; propose a concrete fix; declare
   `swept diff: yes|no`; and set `VERDICT: Approved|Changes requested|Blocked`.
3. This is read-only product QA: edit only this relay file. Never push.
4. Append one block at the bottom; never rewrite earlier turns. Reviewer may close on Approved by
   setting `NEXT: Closed` and `STATUS: Approved`.

## Setup

- Target repository: `/Users/noelsaw/Documents/GH Repos/rebalanceOS-gh211`
- Base: `origin/development`
- Branch: `fix/gh211-bounded-runtime-recovery`
- Issue: `HiQS-Labs/rebalanceOS#211`
- Plan: `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY.md`
- Recon: `PROJECT/2-WORKING/GH-211-MAC-STUDIO-RUNTIME-RECOVERY/recon-bounded-runtime.md`
- Evidence: `TESTS-RESULTS/2026-09-12+GH-211/README.md`
- Reviewer: codex · Producer: claude-a

Review the full diff, not merely the listed files. Read `AGENTS.md`, `GUIDING-PRINCIPLES.md`,
`SOP.md`, and `ARCHITECTURE.md` first. Verify:

1. Every finite scheduled job receives exactly one positive wall-clock ceiling while pulse-server is
   the only `none` exemption; timeout reaps the process tree and produces one truthful terminal event.
2. Stack and doctor detect over-age live jobs without breaking incumbent exit/lifecycle contracts.
3. Pulse health implements the documented 06:53 grace and 90-minute boundaries and returns 503 stale.
4. In-repo Git publishers share one lock and correctly handle dirty-identical and committed-unpushed
   states without losing work or falsely claiming publication.
5. Semantic orphan repair is dry-run by default, transactional, auditable, and requires both ordinary
   and large-run confirmations where applicable.
6. Version, manifest, changelog, docs, tests, compatibility, security, error paths, and rollback are
   coherent. Flag any scope expansion, missed caller, race, false-green assertion, or regression.

## Evidence supplied by producer

- Focused integrated suite: 124 passed.
- Python 3.13 root suite: 2,347 passed, 20 skipped, 10 xfailed, 143 subtests passed.
- Python 3.13 HiQS suite: 163 passed, 1 skipped, 1 xfailed.
- Ruff, format, mypy, banned-import, doc-link, frontdoor, shell syntax, and read-layer checks green.
- Python 3.12 lane is running independently and is not claimed complete until recorded below.

## Log

## Round 1 — Codex review

VERDICT: Changes requested

swept diff: yes

- [Should] `src/rebalance/ingest/semantic_index.py:83-95` selects and counts orphan IDs before
  `BEGIN IMMEDIATE`. A concurrent semantic writer can create a matching document between that read
  and the transaction, after which repair deletes an embedding that is no longer orphaned; the
  confirmation threshold is likewise based on pre-transaction state. Start the write transaction
  before `orphaned_embedding_ids()`, derive the count/sample under that transaction, then delete and
  commit. Add a regression that inserts the matching document at the former read/write seam and
  proves its embedding survives (or proves the writer is excluded until repair commits).
- [Should] `src/rebalance/ingest/pulse.py:999-1004` calls publication verified when
  `git show` output and expected content match only after `.strip()`. A remote file that differs
  solely in leading/trailing whitespace can therefore be falsely reported as published, contrary
  to the exact-content recovery contract. Compare the complete strings (or bytes) without
  normalization and add a remote-content test whose only difference is terminal or leading
  whitespace.

The current graph generation was fresh for Python/test paths with no recorded parse gaps. The
operational `scripts/` subtree is intentionally excluded from that graph, so the scheduler, stack,
and pulse-server paths were checked directly from source. The supplied Python 3.12 lane remains
unclaimed, as stated by the producer.

<!-- ↓↓↓ NEXT TURN goes here; marker stays last ↓↓↓ -->
