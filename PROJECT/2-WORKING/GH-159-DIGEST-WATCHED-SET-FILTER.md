---
gh_issue: 159
source: https://github.com/HiQS-Labs/rebalanceOS/issues/159
title: "GH-159 — the digest's watched-set filter guards one section; every headline collector filtered on date only"
status: "Implemented 2026-09-03 on fix/gh159-digest-watched-set; live control recorded below"
created: 2026-09-03
owner: noel
doc_type: fix
goal: >
  Make the watched-repo ignore list mean one thing everywhere. Before this change it
  governed collection but not presentation, so an ignored third-party repo's traffic —
  authored entirely by strangers — reached the twice-daily digest and therefore a shared
  Slack channel.
effort: 2
complexity: 2
risk: 2
phases: 1
ratings_provisional: false
---

# GH-159 — digest watched-set filter

## TOC

1. [What was wrong](#1-what-was-wrong)
2. [Why it was invisible](#2-why-it-was-invisible)
3. [What changed](#3-what-changed)
4. [Live control](#4-live-control)
5. [Invariants preserved](#5-invariants-preserved)
6. [What this does NOT fix](#6-what-this-does-not-fix)
7. [Acceptance](#7-acceptance)

## 1. What was wrong

`utils/hiqs_digest.py` resolved the watched set in exactly one place — the data-staleness
report — and nowhere else. The SHIPPED / merged / commit collectors queried the artifact
tables with a **day-window predicate only**:

| line (pre-fix) | query |
|---|---|
| 348 / 352 | `github_commits` / `github_direct_commits` inside the day-commits CTE |
| 420 / 427 | by_repo aggregate on `merged_at` / `created_at` |
| 463 / 476 | `merged_total` and the merged detail list |
| 494 / 505 | `closed_at` window, and the same with `AND merged` |

Any repo present in the corpus, authored by anyone, landed in the digest.

Caught live: the 2026-09-03 1705 dry run led with `deusdata/codebase-memory-mcp: Merged
7 PRs` — a repo the operator had explicitly ignored hours earlier, with **zero** operator
commits ever, the seven PRs belonging to six unrelated accounts (CaptainMittens 2,
DeusData 2, rarepops 2, LazyXuan 1, angusgastle 1, shafty023 1). The same defect produced
the 2026-09-01 headline "Merged 11 PRs" from eight other people's work.

The digest reaches Slack indirectly — it git-pushes `digests/hiqs-<date>-<slot>.md` into
`Hypercart-Dev-Tools/rebalance-git-pulse` and AEGIS Sleuth's snapshot-relay polls that
directory — so a contaminated digest is outward-facing and effectively irreversible.

## 2. Why it was invisible

The ignore list governs **collection**, not **presentation**. Adding a repo to
`github_ignored_repos` removes it from `get_watched_repos()`, so nothing new syncs — and
the operator sees `watched` drop by one, which reads like the lever worked. It did, for
collection. Every row the repo already wrote stays in `github_items`,
`github_commits` and `github_direct_commits` **forever**, and the digest kept reporting
them. One lever, two meanings, depending on which consumer you asked.

## 3. What changed

Two new helpers in `utils/hiqs_digest.py`:

- `resolve_watched_repos(db)` — the current watched set, canonicalized and lowercased,
  recomputed live. Raises on failure or on an empty result.
- `_watched_predicate(watched, canonical)` — returns `(sql, params)` binding the set as
  parameters and comparing against the **same** canonical expression the queries group by.

`collect_github(db, bounds, watched)` now takes the watched set as a **required positional
parameter with no default**. That is deliberate. A permissive default would let the
unfiltered path return the moment one caller omitted the argument, and this module
publishes to a shared channel. The day-commits CTE carries the predicate once, so
`commit_total`, the commits detail list and the by_repo commits branch all inherit it from
a single site; the four `github_items` queries carry it explicitly.

`collect_repo_freshness(db, now, watched_lower)` now receives the set rather than
resolving its own, so the two halves of the GitHub section cannot disagree about what is
being watched.

`build_facts` resolves once per run and **fails the whole GitHub section closed** if the
watched set will not resolve: the honest output is "unavailable", not the entire artifact
corpus. Fail-open on an unreadable guard is #156's defect class.

## 4. Live control

Run against the production corpus at
`~/Library/Application Support/rebalance-os/rebalance.db`, watched set = 67 (the
contaminant absent). "pre" re-admits `deusdata/codebase-memory-mcp` to the set to
reproduce the old behaviour on the same rows.

| date | merged_total pre → post | commit_total pre → post | contaminant rows post | legit repos identical |
|---|---|---|---|---|
| 2026-09-01 | 40 → 28 | 361 → 318 | none | yes (11 repos) |
| 2026-09-03 | 26 → 19 | 298 → 261 | none | yes (10 repos) |

Pre-fix, that one repo contributed 43 commits / 12 merged PRs on 09-01 across 23
contributors, and 37 commits / 7 merged PRs on 09-03 across 15. Every genuinely watched
repo's `(commits, prs_merged)` pair is unchanged — the filter removes the contaminant and
nothing else.

Suite: `tests/test_hiqs_digest.py`, 74 passed. Four new tests, of which two are the ones
that prove the filter constrains — the pre-existing tests hand it everything they inserted,
so the filter is inert there and must not be read as coverage of it:

- an unwatched repo's merged PRs, commits and direct pushes are all absent;
- the negative control — the same corpus, the same day, the repo watched — reports it, so
  the removal is the filter and not a broken fixture;
- a repo watched under the new org spelling still reports rows stored under the old one;
- an unresolvable watched set fails the GitHub half closed and never calls the collector.

## 5. Invariants preserved

- **Canonical repo identity (#147).** Comparison is against the canonicalized lowercased
  expression, so an org mirror stored under the old owner spelling still matches a repo
  watched under the new one.
- **`merged_total` keeps `COUNT(DISTINCT {canonical} || '#' || number)`.** A mirrored repo
  holds the same PR number twice; a plain `COUNT(*)` read "10 merged" on a day that
  shipped five.
- **`_utc_day_bounds` untouched.** Strict single local-calendar-day half-open window, each
  boundary resolved independently because a DST day is 23 or 25 hours.
- **No persisted watchlist.** The set is recomputed live, so the filter self-heals the
  moment the operator adds or removes an ignore.

## 6. What this does NOT fix

**Admission.** `_activity_repos` (`src/rebalance/ingest/index_ops.py:878`) sums authorship
and participation signals equally:

```sql
AND ( commits + pushes + prs_opened + prs_merged
    + issues_opened + issue_comments + reviews ) > 0
```

One issue comment on a stranger's repo auto-monitors it for 14 days — that is what
admitted this repo, and the function's own docstring already says passive signals "must
not auto-monitor a repo". Tracked as tweak #1 in #158. GH-159 fixes presentation; #158
fixes admission. Both are needed: without #158 the next contaminating repo is one comment
away, and it will still be synced, still be a project-promotion candidate, and still be
counted everywhere in the activity layer outside the digest.

**Blast radius outside the digest** is unchanged: `refresh_index` sync targets,
`list_watched_repos`, the pulse watched-repo rollup (`pulse.py:497`), `next_actions`
(`next_actions.py:1121`), and project auto-promotion, which draws candidates directly from
`auto_discovered` (`project_inference.py:914-941`).

**The 12 remaining `auto_discovered` repos** have not been audited the same way. Worth
doing, not done here.

**Today's digest was left as-is** by operator decision. The contaminated repo drops out of
tomorrow's window on its own — verified twice: it is in the ignored set, so
`refresh_index` cannot land new rows; and `_utc_day_bounds` is a strict single-day window
whose newest rows for that repo are dated 2026-09-03.

## 7. Acceptance

- [x] Every listed collector filtered by one watched set, resolved once per run.
- [x] Live control on the real corpus: contaminant present pre-fix, absent post-fix, on
      both 2026-09-01 and 2026-09-03.
- [x] Counts for genuinely watched repos identical before and after.
- [x] Alias handling verified: a repo watched under one org spelling still reports rows
      stored under its mirror spelling.
- [ ] #158 tweak #1 (`_activity_repos` authorship vs participation split) — separate, open.

## Related

- Triage of record: `PARKED/2026-09-03-digest-repo-contamination.md`
- Same family: `PARKED/2026-09-01-hiqs-digest-repo-aliasing.md`, #147
- Depends on nothing; #158 is the companion fix, not a prerequisite.
