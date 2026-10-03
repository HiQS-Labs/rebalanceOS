# GH-307 close-the-loop flags — review gate & smoke campaign

| | |
|---|---|
| **Date ran** | 2026-10-02 (PT) / 2026-10-03 (UTC receipts) |
| **Tracking issue** | [HiQS-Labs/rebalanceOS#307](https://github.com/HiQS-Labs/rebalanceOS/issues/307) |
| **Working doc** | [PROJECT/2-WORKING/GH-307-CLOSE-LOOP-FLAGS.md](../../PROJECT/2-WORKING/GH-307-CLOSE-LOOP-FLAGS.md) |
| **Systems under test** | `rebalance-os` 0.98.0 — PR #308 head `519a99e` (builder gate + review) and `281efb2` (review follow-ups) |
| **Environments** | (a) builder: Mac Mini runtime clone, 2026-10-02 (reported in PR #308, not rerun here); (b) review: disposable full clone in `/tmp`, Python 3.13 venv with all extras, against a consistent SQLite `.backup` snapshot of this device's 5.17 GB `rebalance.db` (6,885 `github_items`, 44,435 `github_direct_commits`, 3,593 `github_branches`, 11,984 `github_links`) |
| **Duration** | full suite 5m14s; everything else < 2 min |
| **Output files** | `measurements.jsonl` (primitive), `console/*.log` `*.json` `*.txt` (raw), `scripts/` (commands as run) |

## Why this campaign exists

PR #308's body and the working doc cite empirical numbers (full-suite gate counts,
~0.2 s smoke, corpus suppression fractions) that had no published campaign. This
folder publishes the review-time re-measurements that back the PR's merge decision,
plus the builder-reported numbers with their provenance. Review QA log:
[working doc § Codex/peer QA](../../PROJECT/2-WORKING/GH-307-CLOSE-LOOP-FLAGS.md).

## Headline

| Gate | Result | Provenance |
|---|---|---|
| Focused suites (`test_github_close_loop`, `test_github_readiness`, `test_queries_mirror_invariance`) @ final head | **41/41 pass** (7 close-loop incl. 2 added red-first edge tests) | `console/focused-tests.log` |
| Full suite @ `519a99e` (review device, all extras) | **2,649 passed, 1 failed, 20 skipped, 10 xfailed** | `console/full-suite-pr308-519a99e.log` |
| Same failing test on unchanged `development` (e46150a) | **fails identically** → device-environment-dependent, pre-existing | recorded in `measurements.jsonl` |
| Full suite @ final head | CI `hiqs (3.12/3.13)`, `root-noembed`, `seam`, `lint`, `typecheck` green at merge | PR #308 checks |
| Mutation red-controls (4) | **each mutation caught by the expected test(s)**; post-control tree clean, 7/7 green | `console/mutation-red-controls.log` |
| Read-layer / script-inventory / banned-imports ratchets | clean (52 baseline sites; reasoned `CANONICAL-PATH-OK` datetime pragma verified accurate — `time_ops` has no duration helper) | PR #308 review |
| `pdda.sh run` | 25 observe-mode errors, **0 reference GH-307** (all pre-existing on other docs) | PR #308 review |

## Findings

1. **All five flag rules verified against two independent ground truths** on real
   device data: raw SQL over the snapshot (resolved newest-copy-wins rows) and live
   GitHub — PR #294 has a failing `root-noembed` check live; issues #288/#270/#277
   have no closing PR per `closedByPullRequestsReferences`; branch
   `review/gh562-agy-qa` is live on the XYZ-forge remote; the PR #308 → issue #307
   link row suppresses `started_not_shipped` on the corpus.
2. **Smoke: `ok` on all three repos, sub-second warm** — 0.42 s (rebalanceOS),
   0.66 s (XYZ-forge), 0.25 s (Needle-fork) on the post-fix head; 6.2 s when the
   5 GB snapshot is page-cache cold. Builder-reported ~0.2 s on the Mini corpus is
   corroborated in magnitude. Receipts: `console/cli-smoke-*.json|.time`.
3. **Review fixes changed nothing on real data** — the `(?![0-9a-z])` commit-reference
   boundary and evidence rewording produce identical flag counts pre/post fix
   (15/13/4): no letter-suffixed issue references exist in this corpus. The fix is
   strictly conservative (fewer false deliveries).
4. **Builder-reported corpus fractions are Mini-corpus numbers** and were not
   reproduced byte-identically on this device: "15,367/15,471 default-branch commits"
   vs. this device's largest repo at 10,699/10,699; "removes 47 of 121 candidates"
   vs. 113 candidates here with ≤54 suppressed (LIKE-based SQL upper bound of the
   code's boundary regex). Same mechanism, comparable magnitude, different sync
   windows. Raw recomputation: `console/corpus-fractions.txt`.

## Threats to validity

- **Single-device corpus.** All review measurements come from one device's sync
  window; corpora on other devices differ (the builder's Mini numbers above are
  attributed, not reproduced).
- **SQL recomputation is approximate.** `corpus-fractions.txt` uses `LIKE` matching
  without the number-boundary lookahead, so its suppression count is an upper bound;
  the resolved-rows CTE approximates the reader's newest-copy-wins rule by
  `MAX(fetched_at)`.
- **Post-fix full suite not re-run locally.** The local full-suite receipt is at
  `519a99e`; the final head differs by 4 files (regex lookahead, evidence string,
  CLI hint, tests) and is covered by green CI instead.
- **Device-environment-dependent tests exist.** The one local full-suite failure
  (`test_doctor_scheduled_stack::test_declared_root_overrides_running_checkout`)
  reproduces identically on unchanged `development`; CI lanes are the merge gate.
- **Snapshot timing.** The snapshot was taken while scheduled jobs could write;
  SQLite `.backup` produces a consistent copy, but it represents one instant, and
  `started_not_shipped` branch rows are last-synced, not live (documented in the
  working doc Risks).
