# SOP — Standard Operating Procedure

Do not store any credentials or secrets in this file, other repo files, or any PII in public facing GH issues. The same rule covers machine-specific absolute paths (e.g. a deploy runtime folder's real location) — keep those in your own gitignored `temp/RUNTIME.md`, never in a tracked file. See the pattern in `AGENTS.md` § "Deploy runtime folder".

This document codifies how work in this repo gets **evidenced**. It is written for
whoever picks up the next task, human or model, and it is binding on both.

---

## 1. The rule

> **Verified beats plausible. A claim whose evidence is unpublished is an assertion.**

If you state that something was measured — in a GitHub issue, a PR body, a commit
message, `ROADMAP.md`, a code comment, or a reply to the operator — the measurement
must be retained in [`TESTS-RESULTS/`](TESTS-RESULTS) where a reader can check it
without access to your machine.

This exists because it has already failed here. A retrieval change was tested on 5
queries with no ground truth, the result looked negative, the improvement was
reverted, and the conclusion was reported as settled. It was noise. Re-run properly
(39 queries, hand-established targets, paired significance test) the same change won
decisively — 14 improved, 0 regressed, p=0.0137 — and the earlier call had been
suppressing a real fix for weeks. See
[`TESTS-RESULTS/2026-08-20+GH-81/`](TESTS-RESULTS/2026-08-20+GH-81).

The lesson is not "test more." It is: **a small unverifiable test is worse than no
test**, because it manufactures false confidence and then gets cited.

## 2. When a campaign is required

Run one — and publish it — before any of these:

- **Choosing or replacing a model, library, or algorithm** where the claim is that one performs better than another.
- **Reverting or rejecting a change on empirical grounds.** "I tried it, it didn't help" is a claim and needs the same evidence as "I tried it, it helped." This is the specific failure above.
- **Any performance, retrieval-quality, or accuracy number** that will appear in an issue, PR, or doc.
- **Declaring a system healthy or a defect fixed** where the proof is behavioural rather than a passing unit test.

Not required for: ordinary code changes covered by the test suite, refactors with no
behavioural claim, or documentation.

**If it is not worth a campaign, it is not worth an empirical claim.** Say "not
measured" instead. That is a legitimate and useful thing to write.

## 3. How to run one

### 3.1 Write the protocol first, and freeze it

Before generating a single number, write down: the question, what is being compared,
the dataset, the metrics, and — critically — **the decision rule**: what result would
lead to which action, including the results that would embarrass the current design.

Put it in `PROJECT/2-WORKING/`. A decision rule written after seeing results is not a
decision rule; it is a rationalisation.

### 3.2 Establish ground truth by hand

For retrieval, ranking, or classification work, the correct answer must be determined
by a person **reading the artifact** — not by another model, and not by the system
under test. Discard any item whose correct answer cannot be established; do not guess
it. Record how many you discarded.

Watch for near-duplicates. If several items would legitimately satisfy the same query,
single-target scoring is invalid and will silently penalise every system equally
while looking like a real measurement.

### 3.3 Get the protocol reviewed before running it

Use `/relay-xyz` (or an equivalent independent review) on the **protocol**, not just
the results. Review after the fact can only rationalise; review before can still
change the experiment.

On GH-81 it changed the experiment twice, and one of those changes is why the
headline finding was detectable at all — the original significance rule would have
returned "no measurable difference, keep the incumbent" almost regardless of the
data. Transcripts: [`qa/`](TESTS-RESULTS/2026-08-20+GH-81/qa).

### 3.4 Include a dumb baseline

Always score the boring option — keyword search, the previous version, a constant, a
coin flip. Without it you cannot tell "our system is good" from "this task is easy."
On GH-81 the shipped configuration scored **below plain SQLite full-text search**,
which is not a fact any amount of comparing sophisticated options to each other would
have surfaced.

### 3.5 Use a paired test when systems answer the same inputs

Comparing independent per-system confidence intervals throws away the pairing and
buries real effects under between-item difficulty. Use a paired test (Wilcoxon
signed-rank for bounded/tied metrics), correct for multiple comparisons (Holm), and
report **effect size alongside p** — a significant tiny effect is a real and
reportable outcome.

Report "no significant difference" plainly when that is the answer. It is a result.

### 3.6 Prove the instrument constrains

Before trusting a new test, **make it fail on purpose.** Revert the fix and confirm
the test goes red. A test that passes against broken code measures nothing, and a
green suite full of them is worse than no suite because it is trusted.

### 3.7 Publish

Follow [`TESTS-RESULTS/README.md`](TESTS-RESULTS/README.md): campaign folder named
`YYYY-MM-DD+GH-<issue>`, `SUMMARY.md`, the primitive `.jsonl`, the scripts as run,
the QA transcripts verbatim, the raw console output.

Every aggregate in the summary must be recomputable from the primitive records. If it
isn't, the primitive is incomplete or the number is unsupported.

## 4. Reporting

### 4.1 Threats to validity are mandatory

Every `SUMMARY.md` ends with what would make the result wrong: sample size, sampling
bias, lack of blinding, deviations from protocol, what was *not* measured. Write them
even when — especially when — the result came out the way you hoped.

State deviations explicitly. On GH-81, one model ran at a reduced context window
because the full one exhausted GPU memory; that is recorded, along with the check
showing it did not explain the outcome.

### 4.2 Retract loudly

If a campaign overturns an earlier published conclusion, **say so in the same place
the original was published**, link both, and state what was wrong with the first
attempt. Do not quietly supersede it. Someone is relying on the old claim.

### 4.3 Do not overstate scope

Say what was measured, not what it implies. GH-81 measured the vector retriever in
isolation, while production fuses vector and lexical search — so "no model beat
keyword search" was a component-level result and would have been badly misleading
stated as a system-level one. That correction is in the summary because it was caught
before publication; catching it after would have meant a retraction under §4.2.

## 5. Naming things precisely

Ambiguous names cost real time and cause real errors. When identifying a model,
library, or version, use the **full identifier**, and verify it against the artifact
rather than repeating it from memory or a doc.

- Not "BGE small" → **`BAAI/bge-small-en-v1.5`**
- Not "the embedding model" → the full repo ID and dimension

Model families use several independent axes at once — family, size tier, language,
and release version — and collapsing any of them creates questions like "is this the
small one or the v1.5 one?" when the answer is *both*. See
[`docs/EMBEDDING-MODELS.md`](docs/EMBEDDING-MODELS.md) for this repo's naming
conventions and the current model's exact identity.

Verify from ground truth: the code constant, the recorded run metadata, and the
downloaded artifact should agree. Where they disagree, say which one governs.

## 6. The same thing collected twice is a defect, not a rounding error

> **One real-world entity must contribute to a metric exactly once. If an alias, a rename,
> a mirror, a fork, or a casing variant causes it to be counted twice, that is a defect —
> catch it, fix the read path, and remove the duplicate rows from the store.**

This is the source of truth for the rule. `AGENTS.md` and `GUIDING-PRINCIPLES.md` point here.

### Why it has its own section

A GitHub org rename put the same repository in `github_activity` under two spellings on the
same `scan_date`. Every read path that aggregated those rows **summed** them, so one day's
48 commits and 13 PRs were reported as 86 and 26. Nothing failed, no error was raised, and
the number was simply wrong in every ranking built on it — `top_active_repos`, the
`github_balance` MCP tool, Focus 5, the dashboard, the morning brief.

The test written to catch exactly this inserted the duplicate row with **every metric set to
zero**, so summing it changed nothing and the test passed. It could never have failed. That
is the part worth remembering: the duplicate was known about, a guard was written for it, and
the guard was inert.

### The rule, concretely

The three controls are **detect, reconcile, repair**. All three are required and none substitutes
for another: detection is the only proactive step, reconciliation is what stops a wrong number
being published, and repair is what protects every consumer that does not use the canonical read
path. They are a set, not a sequence — repair the store before or after fixing reads, but do both.

1. **Read the schema to decide the semantics — then do not expect it to enforce them.** If a table
   carries a snapshot — `UNIQUE(...) ON CONFLICT REPLACE` is the tell — then **one row wins**
   (latest `scanned_at`), and summing across aliases is wrong. If rows are genuinely disjoint
   increments, summing is right. The schema tells you which, and that is all it does: a uniqueness
   key built on a **mutable** identifier does not prevent duplicates, it *creates* them. In
   `github_activity` the key includes `repo_full_name`, so an org rename produced a new key, both
   spellings coexisted, and the constraint never fired. That is the whole origin of this defect.
2. **Reconcile at read.** Every aggregate over an entity that can have aliases maps to a canonical
   identity *before* grouping, never after, and never sums across aliases of one entity.
3. **Repair the store too.** Reconciling reads leaves wrong rows in the database for any consumer
   that does not use the canonical path — MCP tools, dashboards, exports. Re-key the stale rows to
   the canonical identity and drop superseded snapshots.
4. **Order matters when de-duplicating.** On a table declared `ON CONFLICT REPLACE`, renaming
   a row onto an existing key **silently destroys the row already there**. Delete the
   superseded rows *first*, then rename. Back up before either.
5. **Never let a de-dup test assert on zeros.** The duplicate fixture must carry the same
   non-zero values as the row it duplicates, and the test must be witnessed failing before the
   fix. A de-dup test that has never gone red is not evidence.
6. **Purge the metric, not just the source.** A number already published from doubled data is
   wrong and gets cited. Correct it, or say plainly that it was not recomputed.

### What this applies to

Any identity with more than one spelling: renamed GitHub orgs and repos, mirrors, forks,
casing variants, email aliases, Slack user IDs versus display names, project aliases in
`project_priority_rules`, and vault note paths that moved. It is not a GitHub-specific rule.

### Enforcement

`tests/test_alias_dedup_invariant.py` pins the invariant with synthetic fixtures and no
dependency on any operator's configuration or org names. It is a deterministic suite test, not
a check against live data.

---

**Related:** [`TESTS-RESULTS/README.md`](TESTS-RESULTS/README.md) (structure and
conventions) · [`AGENTS.md`](AGENTS.md) (working agreements) ·
[`ROUTER.md`](ROUTER.md) (prior-art checks before building)

## 7. A merge is not a deploy

> **Scheduled jobs run from the runtime folder, not from the branch you merged. Until
> someone pulls, the fix does not exist.**

The fleet (`launchd`) is pinned to one checkout — the path in
`~/.config/rebalance/runtime-root`, shown as `Target root` by `scripts/stack.sh status`
— and that checkout is updated deliberately, by hand, with

```
git -C "$(cat ~/.config/rebalance/runtime-root)" pull --ff-only origin development
```

This exists because it has already failed here. On 2026-09-04 eight PRs merged to
`development` in one day, including the digest filter (#163) and the compressor-gate
fix (#171). The runtime had last been pulled on 2026-09-02. Both 13:05 and 17:05
digests went to Slack still leading with the repo #163 removes, and
`obsidian-vault-embeddings` kept failing on the gate #171 relaxes — 51 commits of
merged, CI-green, verifiably working code, none of it running. Nothing reported the
gap; it was found by reading the digest by hand.

**The rule, concretely**

- After merging to `development`, run `bash scripts/stack.sh drift`. It prints how many
  commits the runtime trails and the exact pull command. Exit 1 means behind.
- `stack.sh status` prints the same line at the bottom, so the check rides along with
  the tool ROUTER.md already names as ground truth.
- The `.githooks/post-merge` hook prints it after every `git pull` in your dev
  checkout. Enable once per clone: `git config core.hooksPath .githooks`. It is a
  reminder, never a gate — it cannot fail a merge.
- A deploy is done when `stack.sh drift` says `up to date`, not when the PR says
  `Merged`. Say which in the PR or issue if it matters — "merged" and "deployed" are
  different claims (§ 5).

**Enforcement.** `tests/test_runtime_drift.py` pins the check with two throwaway
repositories and no dependency on any operator's machine — including that it still
measures the runtime when run from inside a git hook, where `GIT_DIR` points elsewhere.

## 8. Which GitHub repos get monitored

> **Authorship monitors a repo. Participation does not. There is no watchlist file.**

Settled on 2026-09-06 under GH-158. The monitored set is recomputed from scratch on
every refresh by `get_watched_repos()` in `src/rebalance/ingest/index_ops.py`:

```
watched = (project ∪ external ∪ activity ∪ pushed) − ignored
```

**A repo is monitored when any ONE of these holds:**

1. **You listed it.** It is in `repos:` on an active project in the project registry.
   This is the only manual list, and it never ages out.
2. **You flagged it external.** A project marked `external: true` is monitored for
   *everyone's* activity, not just yours. Never ages out.
3. **You authored in it recently** — a commit, a push, or a pull request opened or
   merged. One event is enough. "Recently" means the repo appeared in a GitHub scan
   run in the last 14 days; each scan aggregates a 30-day event window, so a repo can
   stay eligible up to roughly 44 days after your last contribution. Expiry is by scan
   date, not contribution date.
4. **Someone pushed to it in the last 14 days** and you can see it, per GitHub's own
   pushed-repos list. This path is *not* authorship-checked: a collaborator's push to a
   private org repo you have access to monitors it too. It exists because the events
   feed drops collaborator pushes and caps at 300 events. If that catches a repo you do
   not want, ignore it (below); tightening this path is a separate decision.

**These do NOT monitor a repo:** starring or watching it, forking it (your first push
to the fork does), opening an issue, commenting on an issue, or reviewing a pull
request. Those are participation, and monitoring a stranger's repo because you left a
comment ingests its entire history and reports other people's work as yours
(`PARKED/2026-09-03-digest-repo-contamination.md`). Editing a project board is not in
GitHub's events feed at all and is not a signal.

**A repo stops being monitored when:**

- it is explicitly ignored — `rebalance config add-github-ignored-repo <owner/repo>`.
  Ignore always wins, over every rule above; or
- it ages out — if activity or a push was its only reason to be monitored, it leaves
  the set silently once no scan in the last 14 days has carried it (see rule 3 for why
  that is later than 14 days after your last commit). There is no other drop mechanism,
  and none is planned. Note this does not drop a repo that has been promoted to a
  project or listed in `repos:` — those stay until you remove or ignore them.

**A repo becomes a project on its own** once 3 or more commits to it (all-time in
collected data, threshold configurable) are attributed to you or to a configured
cloud-agent author (`CLOUD_AGENT_AUTHORS` in `pulse.py`). The promoted row is
machine-owned and never overwrites a curated project of the same name, and from then
on the repo is monitored through the registry, so it no longer ages out. See
"Auto-promotion" in `AGENTS.md`.

**Enforcement.** `tests/test_watched_repos.py::test_participation_only_does_not_auto_watch_repo`
pins that a repo with only issues, comments and reviews stays out while a repo with a
single pull request comes in.


## GH-282 — fleet delivery deployment and lessons

Fleet mode reuses the existing collector, common publication lock and schedules. It does not
select a central Mac. Every participating Mac owns its generated paths and full-history SQLite
replica; remote delivery is eventual on the existing Git Pulse cadence. The Obsidian note is a
combined human-readable projection and is never the capture/control plane.

1. Verify canonical collector identity before opting in: configured `device_id` must be present,
   lower-case and safe, with no pending legacy migration. Inventory local writers, including manual
   CLI/MCP callers, and verify the private checkout is clean and its pending commits are accounted for.
2. Back up the declared runtime revision, configs, copied collector executable, canonical CLIO
   helper, private DB (SQLite backup API), original note and personal header. Verify hashes and DB
   integrity. Keep machine paths and original private content in ignored local deployment receipts.
3. Fast-forward the stable runtime to landed `development`. Update the already installed collector
   copy if it is not a symlink. Keep launchd labels and intervals unchanged; refresh existing long-running
   runtime processes as needed. Do not activate 3-Eyes or disabled jobs as part of this deployment.
4. In collector config set `fleet_mode=true`, the existing canonical `device_id`, and
   `fleet_sync_subdir` matching Rebalance's `sync_subdir`. Set Rebalance `pulse_fleet_enabled=true`
   and `pulse_device_id` to that same ID. Python validates literal collector settings on every publish.
   Fleet mode overrides caller `push=True` and `PULSE_PUSH`; a successful local commit is `queued`,
   never labelled remotely pushed. Shared historical files/pointers are retained but not updated.
5. For CLIO, install the separately reviewed canonical helper, configure its fleet inventory, and set
   explicit `clio_store_path`, `clio_database`, `clio_owner_uuid` in collector config. Export only
   `devices/<CLIO-UUID>/clio.jsonl`; imported origins stay in private SQLite, outside all staged paths.
   The pre-existing `snapshots/` relay remains separate. Never derive a CLIO UUID from a hostname.
6. Run actual local rendering, collector delivery and canonical reconcile; verify upstream objects,
   DB integrity/history preservation, header and the same note path. A fake fixture is useful for
   contract proof but does not qualify an actual offline/rejoin or all-Mac pilot. Other Macs remain
   disabled until their individual installation/source-coverage and archive-capacity checks pass.
7. Rollback disables Python fleet mode and restores the backed-up collector/config/runtime only
   once the private checkout is clean and no fleet commits are unpushed. Otherwise keep the new
   collector and preserved pending history until reconciled; never reset, stash or discard it.

The collector staggers once before its inherited lock. Network operations have a 900-second total
budget and per-call 120-second default timeout, with up to five extra seconds for termination;
local scanning/export overhead adds to lock time. Busy producers skip with 75 and retry on their
existing schedule. They cannot record an attempt while another process holds the lock; age of the
last delivered status remains the signal. Failed network delivery cannot report its failure remotely
until a later delivery succeeds. Fleet health adds bounded local Git reads to the legacy pure-YAML
reader; missing or unverifiable upstream evidence is conservatively not publishing. Experimental
health-check reuses that canonical reader when installed, and otherwise warns for opted-in devices.

Lessons: a merged PR is not a deployed runtime; a copied collector is a second deployment surface;
Python hostname IDs and collector IDs were different; an inherited-lock re-exec must not repeat the
stagger inside the lock. Empty repository inventories must work under macOS Bash 3.2. Preserve
pending commits and use exact owner paths; a heartbeat alone never attests application output.

Fleet render aging uses a named 10-hour bound: 7 hours of scheduled overnight pause, one hour
for fall-back DST, the producer's half-hour budget, one collector interval and half-hour network/
stagger grace. Explicit failed attempts and queued output are visible immediately; a silently
stopped renderer can take that long to age out. Doctor/health detail distinguishes queued, failed
(exit N), unavailable proof and old delivered output. A CLIO export/validation fault deliberately
stops that Mac's collector before a new heartbeat; preserve the previous snapshot, inspect the
backup/DB and cumulative guard, then rerun the existing collector after repair.

A successful local render waiting for the next collector delivery intentionally reports a temporary
doctor WARN (`queued, awaiting collector`). Warning-level health triage may report it during that
window. Observe the installed collector phase across three real intervals before changing alert
policy; this warning does not mean the render failed or its queued commit was lost.

Studio activation lessons: bootstrap all known preserved CLIO origins once with explicit origin
selection, then configure normal exports for the local owner only. Imported records must never
be echoed by routine exports. The first upgraded collector heartbeat advertises fleet mode; an
old unmarked heartbeat still uses legacy health until that delivery. Verify queue-to-delivered
health after this first check-in, not before it. Test missing/mismatched settings as well as valid
configuration: a refusal must return a structured error or doctor configuration failure, with no
Git writes. Briefly unload only loaded local delivery jobs, then restore the identical plists.
Keep capture and same-note export running, and verify preserved record payloads as well as counts.

### CLIO fleet consumer qualification

The canonical CLIO SQLite remains authoritative; the existing configured compatibility export contains full history across known origins. Verify the resolved source before adding a second reader. Raw history totals differ from filtered consumer totals: reconcile eligible projection keys and canonical source references, including multiple origins sharing one filtered prompt. JSONL records are separated by LF, not Unicode line separators. Preserve existing consumer keys and attach provenance additively. Use the existing semantic maintenance facade for selected, nonembedding projection; neither an empty result nor a guard skip proves consumer readiness. Keep scheduled memory deferral separate from delivery failure and never relax the whole stack to obtain a green receipt.
