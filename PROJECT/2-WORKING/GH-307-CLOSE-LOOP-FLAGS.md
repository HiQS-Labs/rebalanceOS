---
gh_issue: 307
source: https://github.com/HiQS-Labs/rebalanceOS/issues/307
title: Close-the-loop flags from the local GitHub corpus
status: Implemented — final Codex QA and PR pending
created: 2026-10-02
updated: 2026-10-02
owner: Grok (start-task)
goal: Give the GH-300 storyline experiment and the XYZ-forge#709 triple-arm work one deterministic, per-repo close-the-loop report read from the existing corpus, so nothing re-fetches GitHub.
doc_type: project
branch: feat/gh307-close-loop-flags
effort: 2
complexity: 2
risk: 1
phases: 1
---

# Close-the-loop flags from the local GitHub corpus

## Status

| What was just completed | What's next |
|---|---|
| Implemented `infer_close_loop_flags`, the `all_issues` reader opt-in, `fetch_direct_commit_messages` and `rebalance github-close-loop`, at version 0.98.0. Five focused tests plus two readiness tests pass, and two mutation red controls fail as expected. A smoke run on a copy of the Mini corpus returned `ok` for rebalanceOS, XYZ-forge and Needle-fork in 0.2 s. | Final Codex QA and a ready PR. Follow-ups: a Needle-fork#79 adapter, an MCP tool, a Focus 5 line (#120), and per-ref commit provenance. |

Rating: **rated 65/35/50/75**.
- **Priority 65:** the operator calls Rebalance the flagship, and this unblocks #300, XYZ-forge#709 and Focus 5 (#120) without a second GitHub read path.
- **Severity 35:** a feature, with no defect or data loss.
- **Appeal 50:** neutral; the operator didn't set it.
- **Effort 75:** cheap, because it reuses the existing resolved-item reader.
- **Recurrence:** N/A, since this is a feature and not a defect class (14-day versus prior 14-day windows don't apply).

## Phase 0 — Prior Art Review

- `src/rebalance/ingest/github_readiness.py::_classify_issue` already derives `draft_pr`, `blocked_review_changes`, `blocked_checks` and `open_without_pr`. It only covers milestone issues and has no ages. **Extend, don't replace.** The new function sits beside it and reuses the same resolved data.
- `src/rebalance/ingest/db/queries.py::fetch_release_readiness_data` is the alias-aware, newest-copy-wins reader (SOP §6) for items, links and branches. When no milestone is given it auto-picks one and filters issues to it. **Reuse it** with one opt-out keyword. A new SQL reader would duplicate the #29/#150 read layer.
- `src/rebalance/ingest/github_reconciliation.py`, close candidates: open issues that a merged PR probably fixed. This is the *inverse* of closed-without-delivery, so the two stay separate.
- The `github_direct_commits` table already exists and is filled by sync. It is used to suppress closed-without-delivery false positives when a default-branch commit references the issue. In the local corpus that removes 47 of 121 candidates.
- GH-300 storyline experiment (PRs #299/#301, draft): this plan supplies its deterministic flag input. It doesn't touch them.
- Needle-fork#79 timeline pipeline: a consumer. Its adapter is a follow-up after this lands.

## Requirements

1. One function: `infer_close_loop_flags(database_path, repo_full_name, *, stale_days=7, since_days=30, now=None) -> dict`. It returns JSON-safe data:
   - `status`: `ok` or `no_local_data`
   - `repo_full_name`, `as_of`, `params`, `counts` per flag
   - `flags`: a list of `{flag, item_type, number, title, html_url, evidence}`, sorted by flag and then number
2. Flags. All rules are deterministic, and there are no LLM labels.
   - `stale_pr`: open, non-draft PR whose `updated_at` is at least `stale_days` old.
   - `forgotten_draft`: open draft PR whose `updated_at` is at least `stale_days` old.
   - `pr_needs_refinement`: open PR with `review_decision == CHANGES_REQUESTED` or `check_status == failing`. It can co-occur with stale or draft.
   - `closed_without_delivery`: closed issue with `state_reason` either `completed` or empty, and `closed_at` within `since_days`. Either of these means the issue was delivered, so no flag is raised:
     - **any** merged PR linked by a PR→issue `github_links` row (`closes` *or* `mentions`). This is deliberate: the flag is surfaced for confirmation, so a weak association suppresses rather than alarms.
     - a direct commit on `refs/heads/<default_branch>`, committed at or after the issue's `created_at`, whose message references `#N` or `GH-N`.

     `not_planned` is excluded. Evidence says "confirm", because this is surfaced for review, not asserted.
   - `started_not_shipped`: open issue meeting all of these:
     - it has a branch matching `(?:^|[/_-])gh-?N(?![0-9a-z])` (case-insensitive);
     - no PR in any state links it;
     - no PR's `head_ref` is a matching branch;
     - its `updated_at` is at least `stale_days` old.

     Branches named only by a bare number are not matched (documented limitation).
3. CLI: `rebalance github-close-loop --repo O/R [--stale-days 7] [--since-days 30] [--db PATH] [--output text|json]`, in `src/rebalance/cli/github.py`, mirroring `github-close-candidates`.
4. No writes beyond the existing `ensure_github_schema` call that sibling readers already make. There is no network access.

## Smallest surface (ordered)

1. `src/rebalance/ingest/db/queries.py`:
   - Add `all_issues: bool = False` to `fetch_release_readiness_data`. When it's True, skip the milestone issue filter. The default is unchanged.
   - Add `fetch_direct_commit_messages(conn, repo_full_name, *, ref, since_iso) -> list[dict]` returning `message` and `committed_at`. It is alias-aware, keeps only the given ref (the default branch), and is bounded by `committed_at >= since_iso`, where the caller passes the earliest `created_at` among candidates. SQL stays inside `ingest/db/`, which `check_read_layer.py` enforces.
2. `src/rebalance/ingest/github_readiness.py`: add `infer_close_loop_flags` (about 90 lines) plus a small `_age_days` helper that uses `parse_utc_iso`.
3. `src/rebalance/ingest/db/__init__.py`: export the new query if the package re-exports queries (follow the existing pattern).
4. `src/rebalance/cli/github.py`: add the `github-close-loop` command (about 40 lines).
5. `tests/test_github_close_loop.py`: a temp DB seeded with one positive and one negative twin per flag, `no_local_data`, a milestone-default regression for readiness (an unchanged count), and a JSON CLI smoke test via Typer `CliRunner` if siblings test their CLIs that way.
6. Version 0.97.2 → 0.98.0 in `pyproject.toml`, `manifest.json` and `src/rebalance/__init__.py`. Add a CHANGELOG `## [0.98.0] - 2026-10-02` entry and one README CLI line next to `github-close-candidates`.
7. Plan doc status, plus a ROADMAP move to In progress.

## Non-goals and deferred

- An MCP tool, a Focus 5 UI line, and Swift changes. Focus 5 can consume the JSON later (#120).
- A CLIO-based started-not-shipped condition. On the Mini corpus `clio_prompts` is empty, and the CLIO store is separate.
- Cross-repo links, which `github_links` stores as same-repo only.
- An exact "no push since last review" rule. The review_decision and check_status flags approximate it.
- A Needle-fork#79 adapter and storyline prose (#300).

## Risks and rollback

- **Sync window:** items outside the synced window are invisible, so flags are lower bounds. This is stated in the CLI text output.
- **Direct-commit provenance:** `github_direct_commits` keeps one row per repo and SHA, and `ref` is the last push ref observed, so default-branch evidence is best-effort. A wrong ref can only flip a confirm-only flag. Per-ref provenance would need a schema change and is deferred.
- **Closed-without-delivery precision:** cross-repo or squash-without-reference deliveries still false-flag. Evidence asks for confirmation, and the #300 operator spot-check (at least 70% useful) decides whether to tighten the rule.
- **Rollback:** the change is purely additive (a new function, a new command, and an opt-in keyword). Revert the PR.

## Tests and gate

- **Focused:** `pytest tests/test_github_close_loop.py tests/test_github_readiness.py`.
- **Gate, once on the final commit:**
  - `pytest tests/`
  - `utils/pdda/pdda.sh run`
  - `python utils/pdda/check_script_inventory.py --check`
  - `python utils/pdda/check_read_layer.py`
  - `rebalance doctor`, if it runs in the task clone; otherwise report that.

## Acceptance

- Every flag has at least one positive and one negative twin test, and they pass.
- The readiness default milestone filtering is unchanged (a regression test covers it).
- `rebalance github-close-loop --repo HiQS-Labs/rebalanceOS --output json` runs against a real local DB.
- The read-layer, script-inventory and PDDA checks are green, or any failures are pre-existing and identical on `development`.

## Codex plan QA log

**Round 1** (Codex `gpt-6-sol` via relay-xyz `consult.sh`, read-only worktree, 2026-10-02 PT): verdict CHANGES.

| # | Finding | Disposition |
|---|---|---|
| 1 | Reusing `fetch_release_readiness_data` with `all_issues` is right; add a regression test. | Accepted (already planned). |
| 2 | The columns and values are valid. | Pass. |
| 3 | BLOCKER: the commit window can miss pre-window delivery, and direct commits come from any branch. | Accepted. The window now starts at the earliest candidate's `created_at`, and only the default-branch ref counts. Locally 15,367 of 15,471 direct commits are default-branch. |
| 4 | Link kind is discarded, so a mention counts as delivery. | Accepted as an explicit decision: any merged association suppresses the flag (stated in the rule). The reader is unchanged. |
| 5 | Check PR `head_ref`; the regex accepts `gh307suffix`. | Accepted. A head_ref match suppresses the flag, and the lookahead is `(?![0-9a-z])`. Bare-number branches are a documented limitation. |
| 6 | Version 0.98.0 and the rating 65/35/50/75 are fine. | Pass. |

**Round 2** (re-run after a Mac Mini disconnect interrupted the first attempt): verdict CHANGES. Findings 4 and 5 were confirmed resolved, and the window fix was confirmed.

| # | Finding | Disposition |
|---|---|---|
| R2-1 | BLOCKER: `github_direct_commits.ref` is last-writer-wins per SHA (`schema.py:654`, `db/github.py:330`), so default-branch provenance is not guaranteed. | **Adjudicated: not a blocker for this scope (ponytail / commensurate).** The flag is advisory and asks for confirmation. A wrong ref only flips a confirm-only suggestion, and locally 99.3% of rows are default-branch. Per-ref provenance needs a schema and writer change, which is out of envelope. The limitation is recorded under Risks, and the default-branch filter stays as best-effort evidence. No round 3 on the plan; the final code QA re-checks. |
