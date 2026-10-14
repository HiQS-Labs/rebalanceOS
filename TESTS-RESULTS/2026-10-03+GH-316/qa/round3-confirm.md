# GH-316 round-3 confirmation (verbatim)

Codex confirmation pass on HEAD d3ccc2f, 2026-10-03. Verdict: **APPROVE — satisfies both
round-2 conditions; no further changes required.** Fenced verbatim (GH-88 rationale).

## Prompt

````
# GH-316 round-3 confirmation — final revision after round-2 fixes

You pre-approved this outcome in round 2: "Fix manifest metadata and the date-sensitive fixture, rerun focused checks, then approve." Both fixes are now applied on HEAD (d3ccc2f). Confirm the two fixes and issue the final verdict — this is a confirmation pass, not a fresh full review; do not re-litigate round-2 passes.

## The two fixes to verify

1. **manifest.json tool metadata** — `tools` list now has `hiqs_work_activity` ("Show HiQS work activity (commit/PR/issue) balance across active projects") as canonical, with `github_balance` kept as "Deprecated alias of hiqs_work_activity; identical behavior".
2. **tests/test_hiqs_work_activity_alias.py** — fixture dates now generated as `date.today() - timedelta(days=1)` (parameterized INSERT), so the 30-day window can never go stale.

## Also changed since the reviewed HEAD 61c431f

- Both consult transcripts (plan r1 + final) relocated under `TESTS-RESULTS/2026-10-03+GH-316/qa/` and fenced verbatim in four-backtick blocks — the raw worktree links must not be repointed (GH-88 rationale) but were tripping the doc-links ratchet when committed bare.

## Focused checks rerun green on HEAD

`test_hiqs_work_activity_alias.py` + `test_mcp_probe.py` + `test_doc_links.py` — 15 passed; ruff + mypy clean.

Output: verdict APPROVE / CHANGES with file:line evidence.

````

## Advisor output

````
**NO FIRSTHAND VERIFICATION CITED** — treat conclusions as conditional (codex's answer carries an unsupported [Pass]/verified/confirmed-style claim with no quoted span or file:line citation nearby, despite the consult PREAMBLE asking advisors to cite evidence.)

> **ATTESTATION**
> Model: gpt-6-astra
> Provider: openai
> Sandbox: read-only

Reading additional input from stdin...
OpenAI Codex v0.159.1
--------
workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-52169-cm4lvxp9
model: gpt-6-astra
provider: openai
approval: never
sandbox: read-only
reasoning effort: low
reasoning summaries: none
session id: 01a100a3-a17d-7950-9309-807101321fb0
--------
user
You are an INDEPENDENT advisor in a one-shot cross-model consult. Another model is answering the SAME question separately and a coordinator will reconcile both answers, so give your own honest, specific read — do not hedge toward a consensus you cannot see. Read any repo files the question references (cite file:line). Respond with: (1) a short direct ANSWER; (2) graded FINDINGS — [Blocker]/[Should]/[Nit]/[Pass] — where applicable; (3) a one-line RECOMMENDATION. You are ADVISORY ONLY: output your analysis as text; do not rely on writing files (you are running in a throwaway copy).

=== CONSULT QUESTION ===
# GH-316 round-3 confirmation — final revision after round-2 fixes

You pre-approved this outcome in round 2: "Fix manifest metadata and the date-sensitive fixture, rerun focused checks, then approve." Both fixes are now applied on HEAD (d3ccc2f). Confirm the two fixes and issue the final verdict — this is a confirmation pass, not a fresh full review; do not re-litigate round-2 passes.

## The two fixes to verify

1. **manifest.json tool metadata** — `tools` list now has `hiqs_work_activity` ("Show HiQS work activity (commit/PR/issue) balance across active projects") as canonical, with `github_balance` kept as "Deprecated alias of hiqs_work_activity; identical behavior".
2. **tests/test_hiqs_work_activity_alias.py** — fixture dates now generated as `date.today() - timedelta(days=1)` (parameterized INSERT), so the 30-day window can never go stale.

## Also changed since the reviewed HEAD 61c431f

- Both consult transcripts (plan r1 + final) relocated under `TESTS-RESULTS/2026-10-03+GH-316/qa/` and fenced verbatim in four-backtick blocks — the raw worktree links must not be repointed (GH-88 rationale) but were tripping the doc-links ratchet when committed bare.

## Focused checks rerun green on HEAD

`test_hiqs_work_activity_alias.py` + `test_mcp_probe.py` + `test_doc_links.py` — 15 passed; ruff + mypy clean.

Output: verdict APPROVE / CHANGES with file:line evidence.

hook: SessionStart
hook: SessionStart Completed
codex
I’ll check the two fixes and the transcript relocation, keeping this confirmation scoped to the round-2 conditions.

exec
/bin/zsh -lc 'pwd; git rev-parse --short HEAD; git status --short; cat SOP.md; cat ARCHITECTURE.md' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-52169-cm4lvxp9
 succeeded in 12205ms:
/private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-52169-cm4lvxp9
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-H3jOy59a' (errno=Operation not permitted)
2026-10-03 00:21:41.145 xcodebuild[61489:320501722]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:21:42.711 xcodebuild[61489:320501676] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-Nype2QUo' (errno=Operation not permitted)
2026-10-03 00:21:43.694 xcodebuild[64986:320507411]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:21:43.984 xcodebuild[64986:320507366] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
d3ccc2f
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-MVx1DNd3' (errno=Operation not permitted)
2026-10-03 00:21:45.755 xcodebuild[66250:320509509]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:21:46.031 xcodebuild[66250:320509451] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
git: warning: confstr() failed with code 5: couldn't get path of DARWIN_USER_TEMP_DIR; using /tmp instead
git: error: couldn't create cache file '/tmp/xcrun_db-s3ismw1e' (errno=Operation not permitted)
2026-10-03 00:21:46.790 xcodebuild[66897:320510597]  DVTFilePathFSEvents: Failed to start fs event stream.
2026-10-03 00:21:47.059 xcodebuild[66897:320510542] [MT] DVTDeveloperPaths: Failed to get length of DARWIN_USER_CACHE_DIR from confstr(3), error = Error Domain=NSPOSIXErrorDomain Code=5 "Input/output error". Using NSCachesDirectory instead.
?? QA/
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

Studio follow-through (0.97.2): source and package metadata can disagree in an editable install; confirm both after deployment. Restart only existing owned long-running consumers so they import the landed code. A manual named-source refresh proves the local consumer, not the guarded schedule. Read-only XYZ facts may be useful while explicitly partial; record errors and unchanged ledger bytes without repairing unrelated history.

1. Verify a clean runtime and retain a verified SQLite backup plus the affected local configuration before activation.
2. Fast-forward the runtime to the tested, independently reviewed landing; refresh its editable package metadata without changing dependencies.
3. Restart existing long-running consumers only; preserve the note identity, installed job plists and exporter/collector cadences.
4. Preview and run the existing named CLIO refresh and selected nonembedding semantic maintenance facade. Reconcile eligible keys and every origin reference, and compare prior consumer IDs and prompt payloads to the backup.
5. Verify Daily citations, same-note/header preservation and delivered transport. For the optional XYZ seam, use existing explicit roots and prove the ledger is unchanged; retain the partial flag.
6. Observe normal guarded jobs before declaring scheduled consumer readiness. On rollback, restore the previous approved runtime and package metadata; restore only the changed config keys. Additive provenance columns are compatible with the previous reader. Use the verified consumer backup only for an observed data regression, with consumer writers paused; never rewind canonical CLIO history to undo a projection change.
# rebalance OS — ARCHITECTURE.md

> **Before building anything, check whether it already exists.** The four prior-art checks (open PRs on *both* repos, `ROADMAP.md` → In progress, a cross-package grep including `HiQS/` and `utils/3-eyes/`, and the full suite including the parts CI skips) are in [ROUTER.md](ROUTER.md) — canonical there, deliberately not restated here.


> How data flows through the system. For execution decisions see the [PROJECT/](PROJECT) docs — canonical detail for a specific effort, governed by [PROJECT/PDDA.md](PROJECT/PDDA.md) — for tool specs see [MCP.md](MCP.md), for the *why* behind these decisions see [GUIDING-PRINCIPLES.md](GUIDING-PRINCIPLES.md).

> **New maintainer? Start with [Maintainer Orientation](#maintainer-orientation-start-here)** — the load-bearing symbols, the two hubs, where to start reading, and one end-to-end trace. **This doc is load-bearing, not decorative:** `audit_modules` (the `audit_modules` MCP tool / [scripts/audit_modules.py](scripts/audit_modules.py)) and the PDDA gate enforce that collectors, render modules, and scheduled jobs stay documented here — update ARCHITECTURE.md in the *same PR* as any structural change.

---

## Core Pipeline

**Opt-in historical projection (GH-230):** `src/rebalance/ingest/clio_journey.py` (run as `rebalance clio-journey-replay`) reads a frozen CLIO JSONL
prefix or canonical marker-backed Markdown export and existing GitHub snapshots via the read-only
DB gateway. It emits a new private run directory with two journey views, source evidence and coverage.
It is not an `all` collector, never updates the index, and does not call a model or publish into a vault.
Its opt-in `--explicit-links-only` policy joins outcomes only through typed qualified GitHub URLs;
other mentions are retained under `unresolved_refs` and excluded from grouping/event attachment.
The independent `--qualified-transitions` option adds a third candidate view for exact new-task
requests naming a different qualified issue. Its grouping and event joins use qualified URLs
regardless of legacy reference settings. Original views and start hints remain unchanged; a split
is not completion. The GH-232 retained-metadata composition recipe is campaign-only, not a new
runtime adapter or collector.
The independent `--issue-evidence` flag appends all qualified trial-issue mentions, including
unassigned prompts, with separate chat labels and visible coverage gaps. It does not alter original
grouping, start hints or evidence membership. Pull-request/foreign/bare-number mentions cannot
supply trial-issue identity; direct issue facts retain event and retrieval times separately.
The campaign-only retained-facts recipe can compose `closingIssuesReferences` via `--delivery-links`
and append three fixed A/B comparisons via `--review-cases`. Whole artifact URLs, typed identities,
merge state/window, retrieval chronology and conflicting records are checked before publication.
This is not the production `github_links` text-matching store or reconciliation scorer. Optional
renderer metadata adds observed relationship receipts, never chat causation or deployment proof.

**INVARIANT**: **Compose, don't mutate**. No new query surfaces (like `semantic_query` vs `ask`) or UI renderers (web server vs static HTML) may be introduced without a plan to deprecate and replace the old one. If extending an existing pipeline, build reusable primitives in `src/rebalance/lib/` instead of duplicating logic in the caller.

```
Signals (data sources)
  │
  ▼
Ingest Layer (source-specific collectors)
  │
  ▼
SQLite + sqlite-vec (unified local store)
  │
  ▼
Query Layer (context gathering + prompt assembly)
  │
  ▼
Two-Layer LLM
  ├── Layer 1: Local Qwen3 (fast first-pass synthesis)
  └── Layer 2: Host Agent (review, adapt, present)
  │
  ▼
User (via MCP host: VS Code, Claude Desktop, etc.)
```

Every raw incoming source follows the same pattern: **collect → normalize → store → query**. The collector registry in `index_ops.py` currently also includes derived local scans and post-ingest/export jobs (`code`, `semantic`, `sync`, `focus5`, `ask_self`), so not every registered scope is a raw upstream signal. The query layer and LLM layers are source-agnostic once data is in SQLite.

### Sync model (in plain English)

Every `refresh_index` run is **incremental** — nothing is re-downloaded from scratch. What "incremental" means depends on what the upstream API lets us ask for cheaply, but three patterns cover every source:

1. **Hash/ID delta** — only fetch or reprocess what actually changed. Used by: vault notes, GitHub artifacts, embeddings.
2. **Window refetch + upsert** — refetch a bounded time-or-count window every run and upsert by ID; nothing is auto-deleted. Used by: GitHub activity (last 30d events), calendar (30d back / 7d forward), email (newest 100 `in:inbox` messages).
3. **Full refetch + column-diff** — refetch the whole upstream set, compare row-by-row, and keep everything as history. Used by: sleuth reminders.

A few caps to know about up-front:

- **Email** is capped at the **newest 100 inbox messages per run** today (Phase 1, shipped 2026-05-12) — default filter `in:inbox`, overridable via `gmail_query_filter` in `temp/rbos.config`. Not "important and starred." See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).
- **Calendar** refetches a **30-day back / 7-day forward window** by default; a 365-day backfill is available on demand via the CLI.
- **GitHub activity** is bounded by the GitHub Events API's own ~30-day retention.
- **Vault, sleuth, embeddings** are unbounded — they cover everything they can see.

Detailed per-source mechanics live in [Storage Layer → Sync semantics per source](#sync-semantics-per-source).

---

## Maintainer Orientation (start here)

New to the codebase? Read this section first — it is the mental model the rest of the doc assumes.

### The two hubs (the model that prevents confusion)

The system has **two** central things with *opposite* roles. Conflating them is the most common newcomer mistake:

- **Orchestration spine — fan-OUT.** `refresh_index()` plus the `COLLECTORS` registry in
  [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py) reach **out** into every collector. This is the
  one intended write/refresh entry point. New ingestion work registers here (`register_collector(Collector(...))`).
- **Persistence base — fan-IN.** [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_database_path()` (answers *which* DB file)
  → `db_connection()` in [src/rebalance/ingest/db/](src/rebalance/ingest/db) (answers *how* to open it). Everything reaches **down** to these.

They compose in a single hop (`refresh_index() → db_connection()`). Keeping orchestration and persistence in
**separate** nodes is *why the codebase has no god-object* despite `db_connection()` being the single most-connected
symbol: it is a thin, stateless connection factory (a dependency *sink*), not a place where logic lives. **Read from it
freely; think twice before changing it** — its blast radius is the whole system.

### Load-bearing symbols (you will see these in almost every file)

| Symbol | Where | What it is / why it's everywhere |
|---|---|---|
| `db_connection()` | `ingest/db/connection.py` | SQLite factory (WAL, foreign keys, 30s busy-timeout, sqlite-vec). Every collector opens its connection here. **High fan-in, zero business logic.** |
| `resolve_database_path()` | `paths.py` | "Which DB file" — layered resolver (`--database` flag → `REBALANCE_DB` → canonical app-data path → user config). Single source of truth for the DB location. |
| `_read_config()` / `_write_config()` | `ingest/config.py` | Layered config + secrets (`temp/rbos.config` + keyring/secret-store). |
| `CalendarConfig` | `ingest/calendar_config.py` | Validated calendar settings (event filters, signal weights). |
| `normalize_github_repo_name()` | `ingest/github_scan.py` | Canonical `owner/repo` string used across every GitHub path. |
| `refresh_index()` | `ingest/index_ops.py` | The orchestrated ingest entry point (see "two hubs" above). |
| `rank_next_actions()` | `ingest/next_actions.py` | Entry point for the "what to do next" engine (see [Query Layer](#the-next-actions-engine-what-to-do-next)). |
| `run_doctor()` | `doctor.py` | Health-check orchestrator; backs `rebalance doctor` (run it before claiming a change works). |

### Where to start reading when touching X

| If you're working on… | Start in | Then read |
|---|---|---|
| A data source (add/fix ingest) | `ingest/index_ops.py` (the `COLLECTORS` registry) + that source's `ingest/<source>.py` | [Adding a New Source](#adding-a-new-source) |
| The read / query side | `ingest/semantic_index.py` (retrieval primitive) + `ingest/querier.py` (`ask()` orchestrator) | [Query Layer](#query-layer) |
| Focus 5 roster / ranking | `ingest/focus5_scan.py` | the `web.py` `/focus-5` route |
| Apple Reminders | `ingest/apple_reminders.py` (read) + `ingest/apple_reminders_write.py` (write, via signed helper) | — |
| "What to do next" | `ingest/next_actions.py` | [The Next Actions engine](#the-next-actions-engine-what-to-do-next) |
| Web dashboard surfaces | `web.py` + `web_components.py` | [Invocation Modes](#invocation-modes) |
| Config / secrets | `ingest/config.py` + `paths.py` | [Credentials](#credentials) |
| Scheduling / launchd jobs | [SCHEDULER.md](SCHEDULER.md) + `scripts/*_sync.sh` | [Invocation Modes](#invocation-modes) |
| The database itself (schema/migrations) | `ingest/db/` (connection, schema, migrations) | [Storage Layer](#storage-layer) |

### One request, end-to-end (worked trace)

A `rebalance refresh` (or the `refresh_index` MCP tool) flows through real symbols like this:

1. **`refresh_index()`** [`index_ops.py`] resolves the scope and iterates the `COLLECTORS` registry (each entry added via `register_collector(Collector(...))`).
2. Each collector's **`sync_*()`** runs fetch → normalize → upsert — e.g. `sync_apple_reminders()`, `github_scan()`, `sync_sleuth_reminders()`.
3. The collector opens storage via **`db_connection(path, ensure_<source>_schema)`** and upserts (e.g. `sync_apple_reminders()` → `upsert_apple_reminders()` → `db_connection()`).
4. **Derived stages** follow (`code`, `semantic`, `sync`): the unified semantic index is rebuilt by `backfill_semantic_documents()` and embedded.
5. **Read side:** `semantic_index.query()` (raw retrieval primitive; MCP `semantic_query`) and `querier.ask()` (broad synthesis orchestrator) read the *same* SQLite via `resolve_database_path()` → `db_connection()`.
6. **Surfaces:** the `web.py` routes (`/focus-5`, `/auth-log`, what's-next), the Typer CLI, and the MCP tools all read through that one persistence base.

---

## Signal Sources

Raw incoming sources have a priority, a collector module, and a target table. The table below is the canonical field spec; for per-effort execution detail see the [PROJECT/](PROJECT) docs, and for current status see [ROADMAP.md](ROADMAP.md).

| Priority | Source | Collector | Storage | Vectorized | Status |
|----------|--------|-----------|---------|------------|--------|
| P1 | GitHub | `github_scan.py` + `github_knowledge.py` + `github_readiness.py` + `github_reconciliation.py` | `github_activity`, `github_repo_meta`, `github_branches`, `github_items`, `github_comments`, `github_documents`, `github_embeddings` | Yes — structured repo signals plus semantic corpus for issues, PRs, comments, reviews, commit messages, and issue/PR reconciliation | Active |
| P1 | Obsidian Vault | `note_ingester.py` + `embedder.py` | `vault_files`, `chunks`, `keywords`, `links`, `embeddings` | **Yes** — Qwen3-Embedding-0.6B, 1024-dim, sqlite-vec | Active |
| P2 | Google Calendar | `calendar.py` | `calendar_events` table (default window 30d back / 7d forward; no auto-deletion) | No — structured event data | Active |
| P3 | Sleuth reminders (Slack) | `sleuth_reminders.py` | `sleuth_reminders` table | No — structured reminder rows | Active |
| P4 | Email (Gmail) | `gmail.py` + `semantic_index.py` | `email_messages` | Yes — subject + snippet participate in the unified semantic index | Active (Phase 1, shipped 2026-05-12): newest 100 `in:inbox` messages per run; metadata + snippet only, no body parsing yet |
| P4 | Figma comments | `figma.py` + `semantic_index.py` | `figma_comments` | Yes — registry-provider semantic docs for comments | Active (opt-in): requires a PAT plus explicit `figma_file_keys` allow-list |

### Other registered collector scopes

These are registered in `index_ops.py` and dispatch through the same `refresh_index()` orchestrator, but they are not raw upstream data sources:

| Scope | Kind | Purpose | Included in `all` |
|---|---|---|---|
| `code` | derived local scan | AST/code chunk collection into the unified semantic index | Yes |
| `semantic` | projection stage | Unified semantic backfill + embed maintenance | Yes |
| `sync` | export stage | Export calendar/email snapshots to the pulse sync repo | Yes |
| `focus5` | derived local scan | Build the device-local Focus 5 roster + signal cache | No |
| `ask_self` | derived local scan | Inventory ask_self indexes on this device | No |

### Source → Table fanout

```
EXTERNAL SOURCES                  INGESTORS (src/rebalance/ingest/)                  STORAGE
                                                                                     (SQLite @ $REBALANCE_DB
                                                                                      + sqlite-vec)

GitHub REST API ─────▶ github_scan.py            user events (last 30d)       ──▶ github_activity
  (api.github.com)   │                                                            github_repo_meta
                     ├▶ github_knowledge.py      per-repo artifacts:           ──▶ github_items (issues/PRs)
                     │                             issues, PRs, comments,          github_comments
                     │                             reviews, commits, checks,       github_commits
                     │                             branches, milestones,           github_check_runs
                     │                             releases                        github_branches
                     │                                                             github_milestones
                     │                                                             github_releases
                     │                                                             github_links
                     │                                                             github_documents
                     │                                                          ─ github_embeddings (vec0)
                     ├▶ github_readiness.py      release-state inference       ── (reads only)
                     └▶ github_reconciliation.py issue ↔ PR matching           ── (reads only)

Obsidian Vault ──────▶ note_ingester.py          walk *.md, chunk, TF-IDF,    ──▶ vault_files, chunks,
  (filesystem)       │                             wikilinks                       keywords, links
                     └▶ embedder.py              Qwen3-Embedding-0.6B         ──▶ embeddings (vec0, 1024-dim)
                                                   via mlx-embeddings

Google Calendar ─────▶ calendar.py               OAuth token (keyring+JSON),  ──▶ calendar_events
  (Calendar API)                                   30d back / 7d forward

Sleuth Web API ──────▶ sleuth_reminders.py       Bearer auth, stdlib urllib,  ──▶ sleuth_reminders
  (Vultr dev :2020)                                GET /workspace/<name>/
                                                   reminders?format=rebalance

Gmail API ───────────▶ gmail.py                  desktop OAuth (gmail.readonly), ──▶ email_messages
  (gmail.googleapis.com)                           filter in:inbox by default,
                                                   newest 100 messages/run

Gmail MCP connector ─▶ gmail.py                  agent-pushed message payloads ─▶ email_messages
  (opt-in push path)                               via ingest_email_messages()

Figma Comments API ───▶ figma.py                 file-key allow-list + PAT    ──▶ figma_comments
  (api.figma.com)                                                                        │
                                                                                         └─▶ semantic_documents
                                                                                             semantic_embeddings

Project Registry ────▶ registry.py +              MD registry → projects.yaml ──▶ project_registry
  (vault markdown)     preflight.py                → SQLite projection
```

### Invocation points

| Source | CLI | MCP tool(s) | Daily-sync step |
|---|---|---|---|
| GitHub activity | `rebalance github-scan` | `github_balance` | 3 |
| GitHub artifacts | `rebalance github-sync-artifacts`, `github-embed`, `github-query` | `semantic_query`, `github_release_readiness`, `github_close_candidates` | on demand |
| Obsidian vault | `rebalance ingest notes`, `ingest embed`, `query`, `search` | `semantic_query`, `search_vault` | 1 + 2 |
| Google Calendar | `rebalance calendar-sync`, `calendar-create-event`, `calendar-snap-edges`, `calendar-daily-report`, `calendar-weekly-report` | `create_calendar_event`, `review_timesheet`, `classify_event`, `snap_calendar_edges` | 4 |
| Sleuth reminders | `rebalance sleuth-sync` | `sleuth_sync_reminders` | 5 |
| Email (Gmail) | `rebalance refresh`, `semantic-backfill`, `semantic-query` | `refresh_index`, `semantic_query`, `ingest_gmail_messages` | 6 |
| Figma comments | `rebalance refresh` | `refresh_index` | opt-in |
| Focus 5 | `refresh_index(scope=["focus5"])`, `rebalance serve` / pulse server | web `/focus-5` route | opt-in |
| ask_self inventory | `refresh_index(scope=["ask_self"])` | `list_ask_self_repos` | opt-in |
| Project registry | `rebalance ingest preflight`, `ingest sync`, `onboard` | `list_projects`, `run_preflight`, `confirm_projects`, `onboarding_status` | on demand |

> Registry write discipline (Phase 5, `ingest/lifecycle.py`): discovery is
> read-only and stamps candidates with `provenance` (remote-activity /
> vault-note; local-scan reserved); `confirm_and_write` is the only curated
> write path; activity inference maintains only rows it created (marked
> `inference.generated_by`) and never touches curated rows; priority rules
> overlay at read time and are never persisted.

> Preferred write path: `refresh_index(scope=[...])` is the orchestrated entry
> point. Several source-specific CLI/MCP write commands still exist for
> historical/operator reasons, but some of them bypass the collector/orchestrator
> layer and call leaf ingest functions directly.

> **Sleuth production is read from a published file — no inbound access.** The
> Sleuth box pushes its reminders to a private git repo
> (`rebalance-git-pulse:sync/sleuth/reminders-<ws>.json`); rebalance-OS reads the
> local clone (`base_url` is a `file://`/local path). No SSH tunnel, no open port.
> See [SLEUTH_SYNC.md](SLEUTH_SYNC.md). (Dev still hits the API directly.)

### Source → Consumer fanout (report & synthesis surfaces)

The GH-150 contract: every surface that reads the activity signal — script entrypoint,
scheduled job, MCP tool — has a row here, so "is this new report needed, and what does
it read?" is answered in the diff instead of buried in a 400-line file.
`tests/test_consumer_catalog.py` enumerates entrypoints (`__main__` under `utils/` +
`scripts/`, minus the pdda tooling and the stood-down 3-Eyes tree), scheduled-job
scripts (the SCHEDULER.md policy table), and MCP tools (`@mcp.tool()` in
`src/rebalance/mcp/tools/`) and fails on any surface without a row
(`uncataloged consumer`). Column rules the test enforces: **LLM primitive** is `querier`,
`none`, or `own (R2-baseline: <path>)` — a private client may only exist by naming the
ratchet baseline that will shrink when it dies; **Input path** containing "own SQL"
must name its `R1-baseline:` file the same way; **Replaces** is `—` or an existing
Surface. When fe1's shared read layer lands, new rows must read `db/queries.py` and the
baseline references become violations.

| Surface | Entrypoint | Cadence | Input path | LLM primitive | Channel | Replaces |
|---|---|---|---|---|---|---|
| Daily full refresh | scripts/daily_sync.sh | daily 06:30 | orchestrator (`refresh_index`) | none | DB write | — |
| Hourly GitHub sync | scripts/github_sync.sh | hourly :45 | orchestrator (`refresh_index`, artifact window 7d) | none | DB write | — |
| Vault embeddings job | scripts/obsidian_vault_embeddings.sh | hourly :15 | orchestrator (`refresh_index` vault+semantic) | none | DB write | — |
| Pulse page | scripts/pulse_sync.sh | hourly :00 | pulse renderer (own SQL R1-baseline: src/rebalance/ingest/pulse.py) | none | pulse repo README | — |
| Pulse web render | scripts/pulse_web_sync.sh, scripts/pulse_web.py | 30 min | pulse renderer (same snapshot) | none | web/pulse.html | Pulse page |
| Pulse server | scripts/pulse_server.sh, scripts/pulse_server.py | daemon | DB read layer + pulse renderer | none | localhost:8767 | — |
| Pulse warning watch | scripts/pulse_warning_watch.py | 15 min | HTTP probe of pulse-server | none | temp JSONL | — |
| Daily work synthesis canary | scripts/daily_work_synthesis.sh, utils/daily_work_synthesis.py | 15 min, opt-in | existing CLIO/calendar/reminder read APIs + Daily repository/CPU scanners | own (R2-baseline: utils/daily_work_synthesis.py) | append-only temp Daily log + sanitized receipt JSONL | — |
| CLIO journey replay | src/rebalance/ingest/clio_journey.py (`rebalance clio-journey-replay`) | manual, opt-in | frozen CLIO export + bounded read-only GitHub snapshot (GH-230 exception) | none | new private replay directory | — |
| Health issue reporter | scripts/health_issue_reporter.py | hourly :10 + 3×/day triage | doctor subprocess + GitHub API | own (R2-baseline: scripts/health_issue_reporter.py) | GitHub issues | — |
| Daily note rollover | utils/obsidian_rollover.sh, utils/obsidian_daily_rollover.py | daily 00:40 | vault filesystem | none | Obsidian daily note | — |
| Progress digest | scripts/hiqs_digest.sh, utils/hiqs_digest.py | 2×/day 13:05/17:05 | own SQL (R1-baseline: utils/hiqs_digest.py) + doctor + semantic | querier | pulse repo digests/ → Slack relay | — |
| Daily synthesis | utils/daily_synthesis.sh, utils/daily_synthesis.py | daily 18:20 | pulse.collect_pulse_snapshot + git-pulse device files | querier | Obsidian note + CLIO log | — |
| Dashboard note | src/rebalance/ingest/note_builder.py | on refresh | own SQL (R1-baseline: src/rebalance/ingest/note_builder.py) + calendar | own (R2-baseline: src/rebalance/ingest/note_builder.py) | vault dashboard note | — |
| Claude Cloud signal grade | utils/claude_cloud_daily_grade.py | daily | ingest/claude_cloud sessions API | none | Obsidian block | — |
| Claude Cloud jobs POC | scripts/cc_cloud_jobs.py | manual | api.anthropic.com fetch (R2-baseline: scripts/cc_cloud_jobs.py) + gh | none | stdout + temp/ | Claude Cloud signal grade |
| Web dashboard data | scripts/dashboard.py | manual | own SQL (R1-baseline: scripts/dashboard.py) | none | dashboard payload | — |
| Chat eval | scripts/chat_eval.py | manual | eval corpus | none | stdout | — |
| Module audit | scripts/audit_modules.py | manual / MCP | repo tree + docs | none | audit report | — |
| Doc link check | scripts/check_doc_links.py | manual | repo docs | none | stdout | — |
| Extension build | scripts/build_extension.py | manual | capabilities tree | none | built artifacts | — |
| Capabilities index | scripts/generate_capabilities_index.py | manual | repo tree | none | capabilities index | — |
| Calendar OAuth setup | scripts/setup_calendar_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Gmail OAuth setup | scripts/setup_gmail_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Cloud daily grade helpers | utils/job_guard.py | per job | process guard | none | job lifecycle | — |
| Vector store reclaim | utils/gh250/reclaim.py | manual (historical) | vector store | none | store maintenance | — |
| Releases ledger CLI | utils/py/releases_app.py | manual | releases.db | none | ledger + dump | — |
| Releases cycle rollup | utils/py/releases_cycle.py | on demand | releases.db (read-only) | none | rollup markdown/dashboard | — |
| MCP: index_status | src/rebalance/mcp/tools/index.py | on demand | status snapshot (coverage probe) | none | MCP | — |
| MCP: refresh_index | src/rebalance/mcp/tools/index.py | on demand | orchestrator | none | MCP | — |
| MCP: diagnose_repo | src/rebalance/mcp/tools/index.py | on demand | own SQL (R1-baseline: src/rebalance/ingest/diagnose.py) | none | MCP | — |
| MCP: list_watched_repos | src/rebalance/mcp/tools/index.py | on demand | watched-set view | none | MCP | — |
| MCP: list_ask_self_repos | src/rebalance/mcp/tools/index.py | on demand | ask_self index | none | MCP | — |
| MCP: publish_pulse | src/rebalance/mcp/tools/index.py | on demand | pulse renderer | none | MCP | — |
| MCP: peek_source | src/rebalance/mcp/tools/index.py | on demand | parameterized table peek | none | MCP | — |
| MCP: get_next_actions | src/rebalance/mcp/tools/index.py | on demand | next_actions engine (R1-baseline: src/rebalance/ingest/next_actions.py) | querier | MCP | — |
| MCP: semantic_query | src/rebalance/mcp/tools/index.py | on demand | semantic index | none | MCP | — |
| MCP: audit_modules | src/rebalance/mcp/tools/hygiene.py | on demand | repo tree + docs | none | MCP | — |
| MCP: calendar tools | src/rebalance/mcp/tools/calendar.py | on demand | calendar_events | none | MCP | — |
| MCP: onboarding tools | src/rebalance/mcp/tools/onboarding.py | on demand | registry/lifecycle + gmail push | none | MCP | — |
| MCP: projects tools | src/rebalance/mcp/tools/projects.py | on demand | registry; github_balance → own SQL (R1-baseline: src/rebalance/ingest/github_scan.py) | none | MCP | — |
| MCP: retrieval tools | src/rebalance/mcp/tools/retrieval.py | on demand | vault FTS; readiness → own SQL (R1-baseline: src/rebalance/ingest/github_readiness.py) | querier | MCP | — |
| MCP: sleuth tools | src/rebalance/mcp/tools/sleuth.py | on demand | sleuth source | none | MCP | — |

Grouped rows (one row covering several same-shape tools, e.g. "MCP: calendar tools")
name their module; the test resolves them. Two surfaced read paths have no entrypoint
of their own and are carried by the rows above: `pulse.collect_pulse_snapshot`
(daily synthesis) and the querier synthesis primitive itself.

### Credentials

| Source | Secret store | Mechanism |
|---|---|---|
| GitHub | OS keyring + out-of-repo secret store (`~/.config/rebalance-os/secrets`, `0600`) fallback; `gh` CLI as last-resort read fallback | PAT: classic `repo` scope, or fine-grained with All-repos read-only Contents/Metadata (public-only tokens hide private work); persisted to keyring + secret store for launchd reachability — no longer written to `temp/rbos.config` |
| Google Calendar | `google-calendar.env` (client credentials) via `resolve_secret_path()` + OAuth user-token in keyring with a JSON fallback at `~/.config/rebalance-os/secrets/google-calendar-oauth` (a legacy pickle migrates to JSON on read) | OAuth 2.0 user consent |
| Sleuth | OS keyring + secret store (`~/.config/rebalance-os/secrets/sleuth_web_api`); legacy `*.env` files still read for un-migrated devices | Bearer token, 64-hex |
| Gmail | Desktop OAuth token in keyring + JSON fallback at `~/.config/rebalance-os/secrets/google-gmail-oauth`, or MCP push-ingest mode | `gmail.readonly` desktop OAuth, or agent-pushed `ingest_gmail_messages` path when `gmail_ingest_method=mcp` |
| Figma | OS keyring + secret store for the PAT; `temp/rbos.config` holds only the (non-secret) file-key allow-list | Personal access token + explicit file selection |
| Obsidian vault | none | filesystem read only |

Env-file paths resolve via [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_secret_path(name)` — the layered chain is `REBALANCE_SECRETS_DIR` env var → `secrets_dir` field in `~/.config/rebalance-os/config.json` (set via `rebalance config set-secrets-dir`) → `~/secrets/` legacy default. The domain CLI loaders (for example, [src/rebalance/cli/calendar.py](src/rebalance/cli/calendar.py) and [src/rebalance/cli/sleuth.py](src/rebalance/cli/sleuth.py)) use this resolver, so the repo is portable across operator home directories without hardcoded env-file paths. Env files should sit at mode 600. Env files are parsed manually (no `python-dotenv`). Nothing with a secret value is committed.

### Adding a New Source

> **The current preferred way to add a source is the collector / `SourceModule`
> contract — see [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py)
> and the developer guide [PLUGINS.md](PLUGINS.md).** It covers the registry
> descriptor, the optional `semantic_docs` provider, secrets/keyring, numbered
> migrations, and tests, with Figma as the worked example. The steps below are
> the practical recipe for the built-in sources.

1. **Collector** — write `src/rebalance/ingest/<source>.py` following the `sleuth_reminders.py` or `github_scan.py` shape: a dataclass for one record, a `sync_*()` function that fetches → normalizes → upserts, and a module-local `ensure_<source>_schema(conn)`. Use `db_connection(path, ensure_fn)` from the `ingest/db/` package.
2. **Schema** — keep the `CREATE TABLE` inside `ensure_<source>_schema`. Only promote to the shared `ingest/db/` package if more than one module needs it. Use existing tables for unstructured text that should be embedded.
3. **Registry** — register the source in `index_ops.py` with `register_collector(Collector(...))`. Add `requires=...`, `semantic_docs=...`, and/or `candidates=...` metadata if the source needs preconditions, participates in the unified semantic index, or contributes next-action candidates to the HiQS ranking. The `candidates=` provider is how a source reaches the ranked "what to do next" verdict — no edit to the ranker's dispatch.
4. **Credentials** — if the source uses env-style secret files, resolve them through `resolve_secret_path()` and a small domain loader (see `cli/calendar.py` / `cli/sleuth.py`). Never hardcode secrets in repo files.
5. **Next-action candidates** — to feed the HiQS ranking, supply a `candidates=` provider on the `Collector` (a function `bundle → list[candidate dict]`, each Attested with `source`/`evidence`/`why`). `_operator_candidates()` walks the registry, so no ranker edit is needed. A source participates in `ask()` automatically once it is in the ranked bundle — `ask()` reads the whole ranking via `_gather_hiqs_context()`.
6. **Prompt section** — the HiQS section in `_build_prompt()` already renders every ranked source; add a bespoke `_build_prompt()` block only for context that is NOT a ranked next-action.
7. **CLI + MCP** — add thin wrappers in `src/rebalance/cli/*` and `src/rebalance/mcp/tools/*` if the source needs direct user-facing operations beyond `refresh_index()`.
8. **Scheduled refresh** — ensure `included_in_all` and any explicit scheduler usage match the source's intended unattended behavior.
9. **Tests** — add `tests/test_<source>.py` that stubs the outbound call (patch `urlopen` for HTTP, filesystem for local sources). Verify insert / unchanged / update semantics.

No changes needed to the query layer, LLM synthesis, or MCP transport.

---

## Storage Layer

Single SQLite file resolved by `src/rebalance/paths.py::resolve_database_path()`. Default canonical location is `~/Library/Application Support/rebalance-os/rebalance.db` on macOS (or `$XDG_DATA_HOME/rebalance-os/rebalance.db` on Linux); `REBALANCE_DB` env var, an `--database` flag, or a user-config override all win against the canonical path when set. sqlite-vec extension loaded for vector operations.

### Write discipline (one writer per table)

The single most important invariant for a new maintainer to preserve:

- **Reads are unrestricted.** Anything may open `db_connection()` and `SELECT`. The "Tables by Domain" list below names the *writer* for each table — that ownership is about **writes**, not reads.
- **One writer per table.** Each table is written by exactly one module (e.g. `github_activity` ← `github_scan.py`, `sleuth_reminders` ← `sleuth_reminders.py`, `semantic_documents` ← the `semantic` stage only). Do not add a second writer; extend the owning collector instead.
- **Writes go through the orchestrator.** New ingestion/refresh writes register as a `Collector` in `index_ops.py` and run under `refresh_index()` — not as a fresh leaf that opens `db_connection()` and upserts on its own.
- **Known, accepted exceptions (direct `db_connection()` writers outside `refresh_index`).** A few interactive/operator commands write directly *by design* — they are human-in-the-loop mutations, not unattended ingest: `rebalance github-sync-artifacts` (`cli/github.py::github_sync_artifacts()`) and the `rebalance apple-reminders` write path (`cli/apple_reminders.py`). Most other direct `db_connection()` calls from `cli/*` (`onboard`, `config-doctor`, `raw`, `dashboard-render`) are **reads**, which are fine. If you add a new direct *writer*, document it here and say why it can't go through the registry.

### Tables by Domain

```
Project Registry (writer: registry.py::sync_db(), the single low-level upsert)
  project_registry          — canonical project metadata. Rows are either curated
                               (write_semantics="confirmation_gated", written only
                               via the onboarding confirm_projects()/confirm_and_write()
                               path — see lifecycle.py) or machine_owned (never
                               clobbers a curated row of the same name). Two
                               machine_owned producers currently call sync_db():
                               project_inference.py's activity/calendar inference
                               (generated_by "activity_inference_v1") and GH-124's
                               commit-threshold auto-promotion (generated_by
                               "commit_threshold_v1", wired into _refresh_github()
                               in index_ops.py, immediately after the watchlist
                               guard). _is_inference_owned() recognizes both markers.

GitHub activity (writer: github_scan.py)
  github_activity            — per-repo event counts, keyed by (login, repo, scan_date)

GitHub artifacts (writer: github_knowledge.py; schema in `ingest/db/`)
  github_repo_meta           — repo-level metadata (default branch, issue/project support)
  github_branches            — local branch inventory for promotion/release inference
  github_labels              — label dictionary per repo
  github_milestones          — open/closed milestones with due dates
  github_releases            — published tags/releases
  github_items               — issues and PRs (unified table, item_type discriminates)
  github_comments            — issue/PR/review comments
  github_commits             — PR commit history
  github_check_runs          — CI check results per head_sha
  github_links               — explicit and inferred issue↔PR cross-references
  github_documents           — per-artifact embeddable document rows
  github_embeddings          — sqlite-vec virtual table for artifact embeddings
  github_embedding_meta      — model name + dim for the GitHub corpus

Unified Semantic Index (single writer: the `semantic` collector stage in index_ops.py)
  semantic_documents         — canonical cross-source document rows (vault chunks +
                               GitHub issues/PRs/comments/commits, Gmail
                               messages, and registry-provider sources such as
                               Figma comments). Written exclusively by
                               _refresh_semantic_only() via
                               semantic_index.py::backfill_semantic_documents().
                               Consumed by semantic_query() and the LLM context layer.
  semantic_embeddings        — sqlite-vec virtual table, float[1024], keyed by
                               semantic_documents.id. Unified ANN search target.
  semantic_embedding_meta    — model name, dimension, embedder_version, last_embed_at

Vault Ingestion (writer: note_ingester.py)
  vault_files                — one row per .md file, with content_hash for delta detection
  chunks                     — heading-based chunks, FK to vault_files (CASCADE delete)
  keywords                   — TF-IDF top-K per chunk, FK to chunks (CASCADE delete)
  links                      — wikilinks and embeds, FK to vault_files (CASCADE delete)

Embeddings (writer: embedder.py)
  embeddings                 — sqlite-vec virtual table, float[1024], keyed by chunk_id
  embedding_meta             — model name, dimension, last embed timestamp

Email (writer: gmail.py)
  email_messages             — message metadata + snippet, keyed by Gmail message_id.
                               Upsert-only rolling window (newest matching messages);
                               also projected into semantic_documents.

Google Calendar (writer: calendar.py)
  calendar_events            — event id, summary, start/end, location, attendees, description
                               Keyed by Google event ID (INSERT OR REPLACE). Default sync window
                               is 30 days back + 7 days forward (365-day backfill available via
                               the CLI). No automatic deletion; manual cleanup if pruning is needed.

Sleuth reminders (writer: sleuth_reminders.py)
  sleuth_reminders           — one row per Slack reminder, keyed by reminder_id (TEXT PK).
                               Upsert with diff-based insert/update/unchanged counts;
                               first_seen_at preserved across syncs. Rows are never
                               deleted — state transitions (scheduled → posted → completed)
                               are mirrored as UPDATEs.

Figma (writer: figma.py)
  figma_comments             — comment rows keyed by Figma comment key, synced from
                               an explicit file-key allow-list. Also projected into
                               semantic_documents via the registry-provider path.

Device-local inventories / derived jobs
  ask_self_indexes           — per-device inventory of ask_self indexes found on disk
  focus5_repo_signals        — cached per-repo Focus 5 signals for the current device
  focus5_roster              — persisted top-5 Focus 5 roster snapshot
```

### Sync semantics per source

Every source is incremental, but the meaning of "incremental" depends on what the upstream API supports. The three patterns from [Sync model](#sync-model-in-plain-english) map cleanly onto the table below:

- **Vault notes** — *hash delta.* SHA-256 of raw file bytes stored in `vault_files.content_hash`. On re-ingest, unchanged-content files have their `last_modified` refreshed if the on-disk mtime moved forward (a "touch") but skip all parsing and embedding work — surfaced as `touched_files` in the ingest result. Changed-content files are deleted (CASCADE clears chunks/keywords/links) and re-inserted.
- **GitHub activity** — *window refetch.* Keyed by `(login, repo_full_name, scan_date)` with `ON CONFLICT REPLACE`. Each scan re-pulls the user's last ~30 days of events and overwrites *today's* row only; older days are left alone.
- **GitHub artifacts** — *hash/ID delta with window.* Keyed by `(repo_full_name, item_type, number)` for items; comments/commits/checks keyed by GitHub ID. `ON CONFLICT REPLACE` on every sync, with a `since_days` lookback to skip artifacts that haven't been touched in that window.
- **Embeddings** — *hash delta.* Chunks (vault) or documents (GitHub corpus) without a corresponding embeddings row get embedded. A model-version change recorded in `embedding_meta` / `github_embedding_meta` triggers a full re-embed of that corpus.
- **Calendar** — *window refetch.* Keyed by Google event ID with `INSERT OR REPLACE`. Re-sync overwrites existing events and adds new ones within the requested window (default 30d back / 7d forward; 365d on demand for backfill). No auto-deletion — events removed upstream stay in the local DB until manually pruned.
- **Sleuth reminders** — *full refetch + column-diff.* Keyed by `reminder_id`. Column-level diff against the stored row decides insert/update/unchanged; `first_seen_at` is set on insert and never overwritten; `last_seen_at` and `last_synced_at` refresh on every sync. Missing reminders are NOT deleted — terminal states (`completed`, `canceled`) remain as history.
- **Email (Gmail)** — *window refetch, count-bounded.* Keyed by Gmail `message_id` with upsert. Each run pulls the newest 100 messages matching the configured filter (default `in:inbox`, override via `gmail_query_filter` in `temp/rbos.config`). Phase 1 stores metadata + Gmail snippet only — no full body, no historical backfill, no auto-delete. See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).

---

## Query Layer

All consumers read from the same SQLite file. The query layer is source-agnostic.

**Read-side ownership model (Phase 3, Option C):**

| Surface | Role | Owner |
|---|---|---|
| `semantic_query()` MCP tool | Unified raw retrieval primitive | `semantic_index.query()` — owns source vocabulary, freshness, hybrid RRF |
| `chat_with_data()` | Citations-first interactive retrieval | `chat.py` — owns scope aliases (`work`/`code`/`all`), citation shaping; delegates retrieval to `semantic_index` |
| `ask()` | Broad mixed-context synthesis/orchestration | `querier.py` — owns project/calendar/temporal framing; not the canonical retrieval primitive |

```
SQLite @ $REBALANCE_DB
   │
   ├──▶ semantic_index.query()     ── unified raw retrieval primitive
   │    (MCP: semantic_query)          source vocab + hybrid RRF
   │         │
   │         ├──▶ chat_with_data() ── citations-first presentation layer
   │         │    (dashboard /api/chat)  scope aliases, citation shaping
   │         │
   │         └──▶ ask() (partial)  ── contributes to synthesis context
   │
   ├──▶ querier.py::ask()          ── broad orchestrator: gathers project,
   │    (MCP: ask, CLI: ask)           calendar, temporal + semantic signals;
   │                                   synthesizes via local Qwen3 (optional)
   │
   ├──▶ daily_report.py /          ── per-day / per-week calendar rollups
   │    weekly_report.py              with project classification
   │
   ├──▶ github_scan.py             ── per-project commit/PR/issue counts
   │    ::get_github_balance()        (surfaced as the github_balance MCP tool)
   │
   ├──▶ github_readiness.py /      ── release-state inference + issue↔PR
   │    github_reconciliation.py       close candidates
   │
   └──▶ mcp/server.py              ── exposes all of the above as MCP tools
                                       to Claude Code, Claude Desktop, etc.
```

`querier.py` is the synthesis orchestrator (not the retrieval primitive). A single `ask()` call:

1. **Gathers context** from all sources in parallel-ready functions:
   - `_gather_project_context()` — registry entries + repos map
   - `_gather_github_context()` — per-project activity summary (from `github_activity`)
   - `_gather_github_semantic_context()` — semantic recall over the GitHub corpus (`github_documents` + `github_embeddings`)
   - `_gather_vault_context()` — semantic search (embed query → ANN)
   - `_gather_vault_activity()` — recently modified files
   - `_gather_calendar_context()` — upcoming + recent events from `calendar_events`
   - `_gather_temporal_context()` — day-of-week / weekend / holiday framing for the prompt
   - `_gather_hiqs_context()` — the persisted **HiQS** ranked verdict (see below). A cheap
     cached read (`load_ranked_next_actions()`); it never recomputes. This is how Sleuth,
     Gmail, and Figma reach `ask()`: they are already in the one ranked bundle, so `ask()`
     surfaces them via the shared ranking rather than a per-source gatherer.

2. **Assembles a prompt** with all context formatted into labeled sections — including a
   `## HiQS — ranked next actions` section carrying each action's receipts. The ranking is
   also returned first-class on `QueryResult.hiqs`.

3. **Synthesizes** via local Qwen3 LLM (mlx-lm). Returns both synthesis and raw context.

### The Next Actions engine ("what to do next")

A distinct read-side subsystem in [src/rebalance/ingest/next_actions.py](src/rebalance/ingest/next_actions.py) — structurally one of the larger clusters in the codebase. It is **HiQS**: the single, unified work-signal pipeline — **one bundle spanning all six sources (GitHub, vault, Calendar, Sleuth/Slack, Gmail, Figma), one ranked verdict, read by every surface**. `ask()` and the dashboard's what's-next view read the *same* persisted ranking, so they cannot drift. It also drives the fixed vault file `Dashboards/What To Do Next.md`.

Pipeline (real symbols):

1. **`assemble_day_bundle()`** gathers the operator's own day signal across all six sources into an `OperatorBundle`, plus teammate deltas (`_gather_teammate_delta()`). Candidates are built by **`_operator_candidates()`, which WALKS the collector registry** — each source owns its candidate shape via the `candidates=` provider on its `Collector` (the same registry seam as `semantic_docs=`). A new work signal reaches the ranked verdict by registering a collector, never by editing this dispatch (GUIDING-PRINCIPLES Principle 3).
2. **`build_rank_prompt()`** formats the candidates; **`rank_next_actions()`** synthesizes the ranking. **Primary path = Gemini** (`get_gemini_api_key()` → `gemini-2.5-flash`); a deterministic local fallback (Qwen) keeps it working offline. `_parse_ranked_synthesis()` rejects placeholder echoes.
3. Output is a **`RankedNextActions`** (list of `RankedAction`), **persisted** to a cache table via `persist_ranked_next_actions()` and read back by `load_ranked_next_actions()`.
4. **`render_next_actions_markdown()`** writes the ranked list to the fixed vault file (single-writer, generated).
5. **Consumers:** the `web.py` what's-next route (`whatsnext_page()`) is the single WRITER (its `?refresh` path ranks + persists); `ask()` is a READER that exposes the persisted ranking as the first-class `QueryResult.hiqs` field. Neither re-ranks inline, so the two surfaces are structurally incapable of drifting.

### Two-Layer LLM Architecture

```
User question
  │
  ▼
ask() tool ──▶ Local Qwen3-0.6B (Layer 1)
  │              - Sees all raw context
  │              - Fast first-pass synthesis
  │              - Runs on-device via MLX
  │
  ▼
Returns to host agent (Layer 2)
  │              - Claude, Copilot, Gemini, etc.
  │              - Reviews synthesis + raw context
  │              - Fact-checks against raw data
  │              - Adapts, refines, presents to user
  │
  ▼
User sees final answer
```

**Why two layers?** The local model is fast and private — it never sends vault content to the cloud. But it's small (0.6B) and makes mistakes. The host agent is larger, smarter, and can fact-check against the raw context that's returned alongside the synthesis. The user gets speed + accuracy + privacy.

**`skip_synthesis=True`** bypasses Layer 1 entirely and returns raw context only. Use this when the host agent is capable enough to do its own synthesis (e.g., Claude).

---

## Invocation Modes

Four ways the pipeline runs:

1. **Interactive CLI** — `rebalance <subcommand>` via the Typer package under `src/rebalance/cli/`. Ad-hoc and one-shot workflows (`calendar-create-event`, `github-release-readiness`, `sleuth-sync --json`, `profile-sync`, `raw`, etc.). `rebalance` invoked with no arguments launches the live dashboard (mode 4). `rebalance raw [--minutes N] [--watch S] [--json]` is a calibration probe: 1 GitHub API request per invocation, classifies recent events as captured / pending / unwatched against the local pipeline state, used to verify that commits/PRs/issues are making it into rebalanceOS.

2. **Unattended scheduled syncs** — a launchd fleet of ten jobs. [SCHEDULER.md](SCHEDULER.md) is the policy table (single source of truth for labels, cadences, scopes, prerequisites, and outputs; enforced by `tests/test_scheduler_policy.py`). The six data/render jobs, conceptually:

   - **Daily all-scope sync** ([scripts/daily_sync.sh](scripts/daily_sync.sh) / [scripts/com.rebalance-os.daily-sync.plist.template](scripts/com.rebalance-os.daily-sync.plist.template)) at 06:30 local time, plus on boot/login if 06:30 was missed. Calls `refresh_index()` with no scope (the **default recipe**): all raw sources (`vault`, `github`, `calendar`, `sleuth`, `email`) followed by the derived/projection/export stages (`code`, `semantic`, `sync`). Note: `scope=["all"]` is *not* the same as the default recipe — after Phase 1b, `all` expands to raw sources only; the default no-scope path runs the full recipe including follow-on stages. Opt-in scopes (`figma`, `focus5`, `ask_self`) are never included automatically. Per-scope failures are captured in `errors` rather than aborting the run.
   - **Hourly obsidian vault embeddings refresh** ([scripts/obsidian_vault_embeddings.sh](scripts/obsidian_vault_embeddings.sh) / [scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template](scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template)) at HH:15 from 06:15 to 23:15. Calls `refresh_index(scope=["vault", "semantic"])` — keeps notes edited mid-day visible in **both** the dashboard/pulse (vault ingest) and **semantic search** (semantic projection stage). Vault ingest with no changes is ~0.02s; the lightweight BGE-Small (384-dim, ~20MB) semantic stage embeds rows where content changed in milliseconds.
   - **Hourly pulse publish** ([scripts/pulse_sync.sh](scripts/pulse_sync.sh) / [scripts/com.rebalance-os.pulse-sync.plist.template](scripts/com.rebalance-os.pulse-sync.plist.template)) on the hour, 06:00 to 23:00. Renders the operator pulse markdown and pushes it to the configured private repo, but only when the rendered content actually changed since the previous run.
   - **30-minute pulse-web refresh** ([scripts/pulse_web_sync.sh](scripts/pulse_web_sync.sh) / [scripts/com.rebalance-os.pulse-web-sync.plist.template](scripts/com.rebalance-os.pulse-web-sync.plist.template)) every 30 minutes from 06:00 to 23:30. Calls [scripts/pulse_web.py](scripts/pulse_web.py) to regenerate the local `web/pulse.html` mirror of the dashboard. Atomic via tmp+replace (a crashed run leaves the previous HTML intact). No network, no git push — separate from the markdown→private-repo flow above.
   - **Hourly GitHub sync** ([scripts/github_sync.sh](scripts/github_sync.sh) / [scripts/com.rebalance-os.github-sync.plist.template](scripts/com.rebalance-os.github-sync.plist.template)) — a narrower github-only refresh independent of the daily full sync, for environments that want fresher GitHub data without paying the full multi-source cost.
   - **Pulse server (long-running, not scheduled)** ([scripts/pulse_server.sh](scripts/pulse_server.sh) / [scripts/com.rebalance-os.pulse-server.plist.template](scripts/com.rebalance-os.pulse-server.plist.template)) — a FastAPI/uvicorn server on `127.0.0.1:8767` with `RunAtLoad` + `KeepAlive` (autostart at login, restart on crash, `ThrottleInterval=30s`). Adds an interactive layer (real Refresh button + filter) on top of the static `web/pulse.html` the pulse-web job regenerates, **and is the always-on JSON backend for the macOS Focus 5 Float app** ([macOS/Apps/Focus5Float](macOS/Apps/Focus5Float)) — it serves `/focus-5.json` (roster), `/focus-5/goals`, and `/focus-5/note` so the app works without a separate `rebalance serve` on `:8787`. Loopback bind is enforced in [scripts/pulse_server.py](scripts/pulse_server.py). Unlike the five scheduled jobs above, it runs continuously rather than firing on a calendar interval.

     **Drift gotcha (has bitten the Focus 5 app twice):** [scripts/pulse_server.py](scripts/pulse_server.py) does *not* mount `rebalance.web`'s app — it hand-re-declares a chosen *subset* of its routes by importing the renderers. Two consequences: (1) a route added to `web.py` is invisible on `:8767` until a matching wrapper is added to `pulse_server.py` (this is how `/focus-5.json` was missed); (2) because it's a `KeepAlive` daemon, any route change requires `launchctl kickstart -k gui/$UID/com.rebalance-os.pulse-server` to take effect — a long-running process keeps serving its old route table otherwise (this is how a freshly-added `/focus-5/goals` still 404'd).

   The remaining four jobs (health-check hourly, health-check-triage 3×/day, pulse-warning-watch every 15 min, obsidian-rollover at midnight) plus **daily-synthesis** at 18:20 are operational/maintenance agents — see [SCHEDULER.md](SCHEDULER.md). The **daily-synthesis** job ([utils/daily_synthesis.sh](utils/daily_synthesis.sh) / [scripts/com.rebalance-os.daily-synthesis.plist.template](scripts/com.rebalance-os.daily-synthesis.plist.template), GH-74) does two syntheses in one process, in order: first a Gemini daily-activity summary from the structured `collect_pulse_snapshot()` output, then a Gemini synthesis of multi-device git commit logs aggregated via `experimental/git-pulse/view.sh --today`. Each lands in its own idempotent sentinel-bracketed block at the bottom of the vault's `0. Today's Notes.md`, pulse block first. (It replaces two formerly separate jobs, obsidian-daily-sync at 18:20 and git-pulse-daily-synthesis at 18:30, which existed as two launchd jobs only so the second could fire after the first — see `utils/daily_synthesis.py`'s module docstring.) Both syntheses use Gemini-or-skip logic (no Qwen fallback) and the merged job carries one late-run guard to prevent colliding with the 00:00 rollover.

   Wrapper scripts source [scripts/lib/scheduler_common.sh](scripts/lib/scheduler_common.sh) for env bootstrap (repo root, venv python, `PYTHONPATH`), per-day logs under `temp/logs/`, job-lifecycle events into `auth_activity.jsonl`, and log retention. Installers source [scripts/lib/install_common.sh](scripts/lib/install_common.sh) for one normalized flow: always-unload, render the `.plist.template` (`{{REBALANCE_DIR}}`, `{{PYTHON}}`, `{{HOME}}`), `plutil -lint`, load, poll-verify registration. The rendered plists in `~/Library/LaunchAgents/` are gitignored — the templates are the only checked-in form, so a clone on any machine installs cleanly with no per-user editing.

3. **MCP tool handlers** — [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py) registers the tools; [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) remains as the backward-compatibility shim for older launch commands. Host agents (Claude Code / Claude Desktop) call these on demand. `REBALANCE_DB` env var resolves the shared DB path.

4. **Live dashboard** — [scripts/dashboard.py](scripts/dashboard.py) is a Rich Live monitor that polls the local SQLite every 2 seconds (cheap; no network) and runs `refresh_index(scope=["github"])` in a background thread every 10 minutes so the underlying data actually changes. Launch via `rebalance` (no args) or `rebalance dashboard`. Press `r` to trigger an immediate GitHub refresh, `q` (or Ctrl+C) to quit. Theming and cadence are env-var controlled (`PULSE_INVERSE`, `PULSE_TICK`, `PULSE_AUTO_MIN`, `REBALANCE_TZ`). The dashboard is intentionally read-only against the same DB the MCP server and the launchd jobs write to.

---

## MCP Tool Surface

Tools are registered in [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py)::`create_server()`. [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) is a backward-compatibility shim so older launch commands still work. All tools share the same `database_path` resolved at server startup from `REBALANCE_DB`.

| Category | Tool | Purpose |
|----------|------|---------|
| Query | `ask` | Natural language query across all sources (with optional local LLM synthesis) |
| Query | `search_vault` | Vault keyword search (TF-IDF) |
| Query | `github_balance` | Per-project GitHub activity summary |
| Query | `github_release_readiness` | Infer milestone/release readiness from the local GitHub corpus |
| Query | `github_close_candidates` | Suggest open issues that likely map to merged PRs |
| Query | `semantic_query` | Unified vector search across indexed sources (single ranked result set; filter with `sources`) |
| Diagnostics | `index_status` | Snapshot of every source + semantic index freshness (read-only) |
| Diagnostics | `refresh_index` | Orchestrated refresh of the local knowledge base (single entry point) |
| Diagnostics | `list_watched_repos` | Show merged set of repos being monitored (project registry ∪ activity − ignored) |
| Diagnostics | `diagnose_repo` | Walk the watched-repos + sync funnel for a single repo (optionally a `sha` or `pr`) and explain coverage + freshness gaps; opt-in `live=True` distinguishes "we never synced" from "PAT can't see it" |
| Registry | `list_projects` | Query project registry |
| Onboarding | `onboarding_status` | Check setup completion |
| Onboarding | `setup_github_token` | Validate and store GitHub PAT |
| Onboarding | `run_preflight` | Discover project candidates (read-only) |
| Onboarding | `confirm_projects` | Write registry and sync |
| Onboarding | `ingest_gmail_messages` | Agent-pushed Gmail ingest path for installs using `gmail_ingest_method=mcp` |
| Calendar | `create_calendar_event` | Create a Google Calendar event via local OAuth |
| Calendar | `review_timesheet` | Surface unclassified calendar events that need a project decision |
| Calendar | `classify_event` | Persist an include/exclude/project classification for an event |
| Calendar | `snap_calendar_edges` | Detect and (optionally) fix slightly overlapping events |
| Sync | `sleuth_sync_reminders` | Pull Slack reminders from the Sleuth Web API and upsert to SQLite |
| Sync | `publish_pulse` | Render today+yesterday activity to markdown and push to private pulse repo |
| Hygiene | `audit_modules` | Run [scripts/audit_modules.py](scripts/audit_modules.py) and return the structured JSON result. Verifies that ingest collectors / render modules / scheduled-job infrastructure are documented in ARCHITECTURE.md and CHANGELOG.md, and that recent commits' file changes appear in the latest CHANGELOG version section. Supports `init=True` to snapshot the baseline lockfile and `include_uncommitted=True` for a pre-commit working-tree preview |

Tool specs (params, returns, dependencies): see [MCP.md](MCP.md).

---

## Module Map

```
src/rebalance/
  __init__.py              — package version
  __main__.py              — CLI entry point
  cli/                     — Typer command package split by domain
  mcp/                     — FastMCP server + tool modules
  mcp_server.py            — backward-compatibility shim to rebalance.mcp.server
  paths.py                 — centralized path resolver. `resolve_database_path()` and
                              `resolve_secret_path()` walk a layered chain (explicit
                              flag → env var → canonical app-data path → user
                              config → cwd walk-up for project marker). Single
                              source of truth for "where is the DB / secrets dir?"
                              `resolve_project_root(Path(__file__))` (walk-up) is the
                              stable repo-root resolver used throughout the codebase —
                              replaces all `parents[N]` hacks. `resolve_oauth_token_path(service)`
                              returns the canonical launchd-reachable token path for
                              Google OAuth services. Configure user defaults via
                              `rebalance config set-default-database` and `set-secrets-dir`.
  web.py                   — FastAPI local dashboard/web surfaces (`/`, `/focus-5`, `/auth-log`, etc.)
  ingest/health_log.py     — doctor check TRANSITIONS into the unified system log (GH-101)
  doctor.py                — installation health checks; backs `rebalance doctor`
  ingest/
    config.py              — secrets storage (temp/rbos.config)
    registry.py            — project registry sync (Markdown ↔ YAML ↔ SQLite);
                              read_registry (pure read) vs load_registry (write-path)
    preflight.py           — onboarding discovery (read-only, provenance-stamped)
                              + confirmation — the only curated registry write path
    lifecycle.py           — Phase 5/6 lifecycle contract: setup stage map with
                              done/now/next/blocked/skipped statuses, executor
                              hints, and remediation (backs onboarding_status and
                              the /welcome skill), plus the project-lifecycle
                              ownership table (write semantics per stage —
                              discovery read_only, confirmation gated, inference
                              machine-owned, prioritization read-time overlay)
    local_repos.py         — local checkout discovery (Phase 6.1): scan
                              local_repo_roots for git checkouts, GitHub identity
                              from origin, unpushed-commit counts; feeds
                              provenance=local-scan candidates + the doctor's
                              unpushed-work check
    github_scan.py         — GitHub Events API collector + per-project balance query
    github_knowledge.py    — per-repo artifact sync (issues/PRs/comments/commits/checks) + embedding
    github_watch.py        — watched/external repo reconciliation and repo-watch logic
    github_readiness.py    — release-readiness inference over the local GitHub corpus (read-only)
    github_reconciliation.py — issue ↔ PR close-candidate inference (read-only)
    db/                    — shared DB connection, schema, migrations, sqlite-vec loading
    md_parser.py           — pure markdown parsing (frontmatter, wikilinks, tags, chunking)
    note_ingester.py       — vault walker, delta detection, TF-IDF keywords
    embedder.py            — mlx-embeddings batch embed + ANN query
    semantic_index.py      — unified semantic index: backfill, embed, and query across
                              vault + GitHub + email, plus registry-provider sources
                              such as Figma (semantic_documents / semantic_embeddings)
    index_ops.py           — single entry point for refresh_index() and index_status();
                              orchestrates the full ingest pipeline so agents don't
                              need to know individual CLI command ordering
    calendar.py            — Google Calendar API collector + SQLite persistence
    calendar_config.py     — OAuth token storage, classification rules, review-decision persistence
    calendar_helpers.py    — duration/math utilities consumed by calendar tools
    calendar_snap.py       — edge-snapping logic for slightly overlapping calendar events
    sleuth_reminders.py    — Sleuth Web API collector (Bearer auth, urllib) + upsert
    gmail.py               — Gmail collector / MCP push-ingest write path into email_messages
    figma.py               — Figma comments collector + registry-provider semantic_docs
    ask_self_scan.py       — device-local ask_self index inventory collector
    focus5_scan.py         — Focus 5 repo-signal scan + roster builder
    slack_users.py         — Slack user-id → friendly-name lookup, file-mtime cached;
                              feeds the dashboard sleuth panel and the pulse markdown
    diagnose.py            — repo-level diagnostic that walks the watched-repos +
                              sync funnel for one repo (optionally sha/PR) — backs
                              the diagnose_repo MCP tool
    profile_sync.py        — daily-sync log parser that surfaces per-repo GitHub
                              timings; backs the rebalance profile-sync subcommand
    pulse.py               — pulse markdown renderer; backs publish_pulse MCP tool
    agent_tags.py          — source-tagging for pulse rows (claude-cloud, codex-cloud,
                              lovable, local-vscode, human)
    project_classifier.py  — calendar event → project matcher for timesheet reports
    project_inference.py   — project inference from note titles / calendar summaries
    note_builder.py        — dashboard markdown renderer / write-back for the vault note
    audit.py               — structured audit logging (append_audit_entry)
    querier.py             — multi-source context gathering + local LLM synthesis

scripts/                   — Operator entry points (not part of the importable package)
  dashboard.py             — Rich Live terminal dashboard (mode 4 above)
  pulse_web.py             — render module: regenerates web/pulse.html (the local
                              browser mirror of the dashboard) from the same SQLite
                              knowledge base; atomic via tmp+replace; supports --watch
  _bootstrap.py            — single sys.path shim for directly-run scripts (src/ + scripts/)
  lib/scheduler_common.sh  — shared launchd job runtime: env bootstrap, dated logs,
                              job-lifecycle events, retention (sourced by *_sync.sh)
  lib/install_common.sh    — shared installer flow: always-unload, render template,
                              plutil -lint, load, poll-verify (sourced by install_*.sh)
  daily_sync.sh            — daily_sync launchd entry (mode 2)
  vault_sync.sh            — hourly vault-only launchd entry (mode 2)
  pulse_sync.sh            — hourly pulse-publish (markdown→private repo) launchd entry (mode 2)
  pulse_web_sync.sh        — 30-minute pulse-web (web/pulse.html) launchd entry (mode 2)
  github_sync.sh           — github-only launchd entry (mode 2)
  install_*.sh             — one installer per launchd job (see SCHEDULER.md for the
                              job ↔ installer table; all delegate to lib/install_common.sh)
  setup_calendar_oauth.py  — interactive OAuth consent flow for Google Calendar
  build_extension.py       — native extension builder
  ask-self-ingest.sh       — self-ingest shell wrapper (portable mode, requires ASK_SELF_PATH)
  ask-self-query.sh        — self-query shell wrapper (portable mode, requires ASK_SELF_PATH)
  audit_modules.py         — repository hygiene audit (Approach A): verifies ingest
                              collectors / render modules / scheduled-job infrastructure
                              are documented in ARCHITECTURE.md + CHANGELOG.md; supports a
                              baseline lockfile (audit_modules.lock), recent-commit coverage
                              against the live CHANGELOG version section, and a pre-commit
                              working-tree preview (--include-uncommitted). JSON output for
                              orchestrating agents; also exposed as the audit_modules MCP tool
```

---

## License

Copyright 2025-2026 Hypercart DBA Neochrome, Inc.

rebalance is dual-licensed, matching the rest of the HiQS suite. **AGPL-3.0-only** is the
default and covers nearly every use — see [`LICENSE`](LICENSE). A commercial license is
available for use that AGPL-3.0 does not fit; see [`LICENSE-COMMERCIAL.md`](LICENSE-COMMERCIAL.md).


## Opt-in fleet Pulse delivery (GH-282)

Rebalance producers → device-owned files/exact local commits → existing Git Pulse collector →
private Git remote → each Mac's checkout/SQLite replica → combined human-readable views.
No Mac is a permanent hub. `git_ops.fleet_settings` validates the configured collector identity,
checkout and sync subdirectory. Generated live pulse, daily synthesis and digests use
`devices/<id>/`; calendar/email keep `sync/<source>/<id>.json`. Historical shared files are retained
for rollback and no longer written in fleet mode. `read_latest_snapshot` chooses validated payloads
on read; `pulse.fleet_view` derives delivered pages and is returned by fleet publishing through the
existing CLI/MCP result. These are readers of existing data, not new stores or writer daemons.

CLIO's capture UUID is independent of the friendly collector ID. Its canonical helper exports only
its owner snapshot to `devices/<UUID>/clio.jsonl`; the collector validates it before atomic publication.
Reconcile imports committed blobs into private SQLite without re-exporting foreign origins. Existing
semantic indexing, publishers and readonly XYZ ledger integrations retain their contracts. The same
Obsidian filename/header and five-minute renderer remain, backed by full history on every installed
Mac. Live fleet qualification remains tracked in the canonical GH-282 plan.

exec
/bin/zsh -lc 'cat SOP.md; cat ARCHITECTURE.md; nl -ba manifest.json; nl -ba tests/test_hiqs_work_activity_alias.py; rg --files TESTS-RESULTS/2026-10-03+GH-316' in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-52169-cm4lvxp9
 succeeded in 0ms:
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

Studio follow-through (0.97.2): source and package metadata can disagree in an editable install; confirm both after deployment. Restart only existing owned long-running consumers so they import the landed code. A manual named-source refresh proves the local consumer, not the guarded schedule. Read-only XYZ facts may be useful while explicitly partial; record errors and unchanged ledger bytes without repairing unrelated history.

1. Verify a clean runtime and retain a verified SQLite backup plus the affected local configuration before activation.
2. Fast-forward the runtime to the tested, independently reviewed landing; refresh its editable package metadata without changing dependencies.
3. Restart existing long-running consumers only; preserve the note identity, installed job plists and exporter/collector cadences.
4. Preview and run the existing named CLIO refresh and selected nonembedding semantic maintenance facade. Reconcile eligible keys and every origin reference, and compare prior consumer IDs and prompt payloads to the backup.
5. Verify Daily citations, same-note/header preservation and delivered transport. For the optional XYZ seam, use existing explicit roots and prove the ledger is unchanged; retain the partial flag.
6. Observe normal guarded jobs before declaring scheduled consumer readiness. On rollback, restore the previous approved runtime and package metadata; restore only the changed config keys. Additive provenance columns are compatible with the previous reader. Use the verified consumer backup only for an observed data regression, with consumer writers paused; never rewind canonical CLIO history to undo a projection change.
# rebalance OS — ARCHITECTURE.md

> **Before building anything, check whether it already exists.** The four prior-art checks (open PRs on *both* repos, `ROADMAP.md` → In progress, a cross-package grep including `HiQS/` and `utils/3-eyes/`, and the full suite including the parts CI skips) are in [ROUTER.md](ROUTER.md) — canonical there, deliberately not restated here.


> How data flows through the system. For execution decisions see the [PROJECT/](PROJECT) docs — canonical detail for a specific effort, governed by [PROJECT/PDDA.md](PROJECT/PDDA.md) — for tool specs see [MCP.md](MCP.md), for the *why* behind these decisions see [GUIDING-PRINCIPLES.md](GUIDING-PRINCIPLES.md).

> **New maintainer? Start with [Maintainer Orientation](#maintainer-orientation-start-here)** — the load-bearing symbols, the two hubs, where to start reading, and one end-to-end trace. **This doc is load-bearing, not decorative:** `audit_modules` (the `audit_modules` MCP tool / [scripts/audit_modules.py](scripts/audit_modules.py)) and the PDDA gate enforce that collectors, render modules, and scheduled jobs stay documented here — update ARCHITECTURE.md in the *same PR* as any structural change.

---

## Core Pipeline

**Opt-in historical projection (GH-230):** `src/rebalance/ingest/clio_journey.py` (run as `rebalance clio-journey-replay`) reads a frozen CLIO JSONL
prefix or canonical marker-backed Markdown export and existing GitHub snapshots via the read-only
DB gateway. It emits a new private run directory with two journey views, source evidence and coverage.
It is not an `all` collector, never updates the index, and does not call a model or publish into a vault.
Its opt-in `--explicit-links-only` policy joins outcomes only through typed qualified GitHub URLs;
other mentions are retained under `unresolved_refs` and excluded from grouping/event attachment.
The independent `--qualified-transitions` option adds a third candidate view for exact new-task
requests naming a different qualified issue. Its grouping and event joins use qualified URLs
regardless of legacy reference settings. Original views and start hints remain unchanged; a split
is not completion. The GH-232 retained-metadata composition recipe is campaign-only, not a new
runtime adapter or collector.
The independent `--issue-evidence` flag appends all qualified trial-issue mentions, including
unassigned prompts, with separate chat labels and visible coverage gaps. It does not alter original
grouping, start hints or evidence membership. Pull-request/foreign/bare-number mentions cannot
supply trial-issue identity; direct issue facts retain event and retrieval times separately.
The campaign-only retained-facts recipe can compose `closingIssuesReferences` via `--delivery-links`
and append three fixed A/B comparisons via `--review-cases`. Whole artifact URLs, typed identities,
merge state/window, retrieval chronology and conflicting records are checked before publication.
This is not the production `github_links` text-matching store or reconciliation scorer. Optional
renderer metadata adds observed relationship receipts, never chat causation or deployment proof.

**INVARIANT**: **Compose, don't mutate**. No new query surfaces (like `semantic_query` vs `ask`) or UI renderers (web server vs static HTML) may be introduced without a plan to deprecate and replace the old one. If extending an existing pipeline, build reusable primitives in `src/rebalance/lib/` instead of duplicating logic in the caller.

```
Signals (data sources)
  │
  ▼
Ingest Layer (source-specific collectors)
  │
  ▼
SQLite + sqlite-vec (unified local store)
  │
  ▼
Query Layer (context gathering + prompt assembly)
  │
  ▼
Two-Layer LLM
  ├── Layer 1: Local Qwen3 (fast first-pass synthesis)
  └── Layer 2: Host Agent (review, adapt, present)
  │
  ▼
User (via MCP host: VS Code, Claude Desktop, etc.)
```

Every raw incoming source follows the same pattern: **collect → normalize → store → query**. The collector registry in `index_ops.py` currently also includes derived local scans and post-ingest/export jobs (`code`, `semantic`, `sync`, `focus5`, `ask_self`), so not every registered scope is a raw upstream signal. The query layer and LLM layers are source-agnostic once data is in SQLite.

### Sync model (in plain English)

Every `refresh_index` run is **incremental** — nothing is re-downloaded from scratch. What "incremental" means depends on what the upstream API lets us ask for cheaply, but three patterns cover every source:

1. **Hash/ID delta** — only fetch or reprocess what actually changed. Used by: vault notes, GitHub artifacts, embeddings.
2. **Window refetch + upsert** — refetch a bounded time-or-count window every run and upsert by ID; nothing is auto-deleted. Used by: GitHub activity (last 30d events), calendar (30d back / 7d forward), email (newest 100 `in:inbox` messages).
3. **Full refetch + column-diff** — refetch the whole upstream set, compare row-by-row, and keep everything as history. Used by: sleuth reminders.

A few caps to know about up-front:

- **Email** is capped at the **newest 100 inbox messages per run** today (Phase 1, shipped 2026-05-12) — default filter `in:inbox`, overridable via `gmail_query_filter` in `temp/rbos.config`. Not "important and starred." See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).
- **Calendar** refetches a **30-day back / 7-day forward window** by default; a 365-day backfill is available on demand via the CLI.
- **GitHub activity** is bounded by the GitHub Events API's own ~30-day retention.
- **Vault, sleuth, embeddings** are unbounded — they cover everything they can see.

Detailed per-source mechanics live in [Storage Layer → Sync semantics per source](#sync-semantics-per-source).

---

## Maintainer Orientation (start here)

New to the codebase? Read this section first — it is the mental model the rest of the doc assumes.

### The two hubs (the model that prevents confusion)

The system has **two** central things with *opposite* roles. Conflating them is the most common newcomer mistake:

- **Orchestration spine — fan-OUT.** `refresh_index()` plus the `COLLECTORS` registry in
  [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py) reach **out** into every collector. This is the
  one intended write/refresh entry point. New ingestion work registers here (`register_collector(Collector(...))`).
- **Persistence base — fan-IN.** [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_database_path()` (answers *which* DB file)
  → `db_connection()` in [src/rebalance/ingest/db/](src/rebalance/ingest/db) (answers *how* to open it). Everything reaches **down** to these.

They compose in a single hop (`refresh_index() → db_connection()`). Keeping orchestration and persistence in
**separate** nodes is *why the codebase has no god-object* despite `db_connection()` being the single most-connected
symbol: it is a thin, stateless connection factory (a dependency *sink*), not a place where logic lives. **Read from it
freely; think twice before changing it** — its blast radius is the whole system.

### Load-bearing symbols (you will see these in almost every file)

| Symbol | Where | What it is / why it's everywhere |
|---|---|---|
| `db_connection()` | `ingest/db/connection.py` | SQLite factory (WAL, foreign keys, 30s busy-timeout, sqlite-vec). Every collector opens its connection here. **High fan-in, zero business logic.** |
| `resolve_database_path()` | `paths.py` | "Which DB file" — layered resolver (`--database` flag → `REBALANCE_DB` → canonical app-data path → user config). Single source of truth for the DB location. |
| `_read_config()` / `_write_config()` | `ingest/config.py` | Layered config + secrets (`temp/rbos.config` + keyring/secret-store). |
| `CalendarConfig` | `ingest/calendar_config.py` | Validated calendar settings (event filters, signal weights). |
| `normalize_github_repo_name()` | `ingest/github_scan.py` | Canonical `owner/repo` string used across every GitHub path. |
| `refresh_index()` | `ingest/index_ops.py` | The orchestrated ingest entry point (see "two hubs" above). |
| `rank_next_actions()` | `ingest/next_actions.py` | Entry point for the "what to do next" engine (see [Query Layer](#the-next-actions-engine-what-to-do-next)). |
| `run_doctor()` | `doctor.py` | Health-check orchestrator; backs `rebalance doctor` (run it before claiming a change works). |

### Where to start reading when touching X

| If you're working on… | Start in | Then read |
|---|---|---|
| A data source (add/fix ingest) | `ingest/index_ops.py` (the `COLLECTORS` registry) + that source's `ingest/<source>.py` | [Adding a New Source](#adding-a-new-source) |
| The read / query side | `ingest/semantic_index.py` (retrieval primitive) + `ingest/querier.py` (`ask()` orchestrator) | [Query Layer](#query-layer) |
| Focus 5 roster / ranking | `ingest/focus5_scan.py` | the `web.py` `/focus-5` route |
| Apple Reminders | `ingest/apple_reminders.py` (read) + `ingest/apple_reminders_write.py` (write, via signed helper) | — |
| "What to do next" | `ingest/next_actions.py` | [The Next Actions engine](#the-next-actions-engine-what-to-do-next) |
| Web dashboard surfaces | `web.py` + `web_components.py` | [Invocation Modes](#invocation-modes) |
| Config / secrets | `ingest/config.py` + `paths.py` | [Credentials](#credentials) |
| Scheduling / launchd jobs | [SCHEDULER.md](SCHEDULER.md) + `scripts/*_sync.sh` | [Invocation Modes](#invocation-modes) |
| The database itself (schema/migrations) | `ingest/db/` (connection, schema, migrations) | [Storage Layer](#storage-layer) |

### One request, end-to-end (worked trace)

A `rebalance refresh` (or the `refresh_index` MCP tool) flows through real symbols like this:

1. **`refresh_index()`** [`index_ops.py`] resolves the scope and iterates the `COLLECTORS` registry (each entry added via `register_collector(Collector(...))`).
2. Each collector's **`sync_*()`** runs fetch → normalize → upsert — e.g. `sync_apple_reminders()`, `github_scan()`, `sync_sleuth_reminders()`.
3. The collector opens storage via **`db_connection(path, ensure_<source>_schema)`** and upserts (e.g. `sync_apple_reminders()` → `upsert_apple_reminders()` → `db_connection()`).
4. **Derived stages** follow (`code`, `semantic`, `sync`): the unified semantic index is rebuilt by `backfill_semantic_documents()` and embedded.
5. **Read side:** `semantic_index.query()` (raw retrieval primitive; MCP `semantic_query`) and `querier.ask()` (broad synthesis orchestrator) read the *same* SQLite via `resolve_database_path()` → `db_connection()`.
6. **Surfaces:** the `web.py` routes (`/focus-5`, `/auth-log`, what's-next), the Typer CLI, and the MCP tools all read through that one persistence base.

---

## Signal Sources

Raw incoming sources have a priority, a collector module, and a target table. The table below is the canonical field spec; for per-effort execution detail see the [PROJECT/](PROJECT) docs, and for current status see [ROADMAP.md](ROADMAP.md).

| Priority | Source | Collector | Storage | Vectorized | Status |
|----------|--------|-----------|---------|------------|--------|
| P1 | GitHub | `github_scan.py` + `github_knowledge.py` + `github_readiness.py` + `github_reconciliation.py` | `github_activity`, `github_repo_meta`, `github_branches`, `github_items`, `github_comments`, `github_documents`, `github_embeddings` | Yes — structured repo signals plus semantic corpus for issues, PRs, comments, reviews, commit messages, and issue/PR reconciliation | Active |
| P1 | Obsidian Vault | `note_ingester.py` + `embedder.py` | `vault_files`, `chunks`, `keywords`, `links`, `embeddings` | **Yes** — Qwen3-Embedding-0.6B, 1024-dim, sqlite-vec | Active |
| P2 | Google Calendar | `calendar.py` | `calendar_events` table (default window 30d back / 7d forward; no auto-deletion) | No — structured event data | Active |
| P3 | Sleuth reminders (Slack) | `sleuth_reminders.py` | `sleuth_reminders` table | No — structured reminder rows | Active |
| P4 | Email (Gmail) | `gmail.py` + `semantic_index.py` | `email_messages` | Yes — subject + snippet participate in the unified semantic index | Active (Phase 1, shipped 2026-05-12): newest 100 `in:inbox` messages per run; metadata + snippet only, no body parsing yet |
| P4 | Figma comments | `figma.py` + `semantic_index.py` | `figma_comments` | Yes — registry-provider semantic docs for comments | Active (opt-in): requires a PAT plus explicit `figma_file_keys` allow-list |

### Other registered collector scopes

These are registered in `index_ops.py` and dispatch through the same `refresh_index()` orchestrator, but they are not raw upstream data sources:

| Scope | Kind | Purpose | Included in `all` |
|---|---|---|---|
| `code` | derived local scan | AST/code chunk collection into the unified semantic index | Yes |
| `semantic` | projection stage | Unified semantic backfill + embed maintenance | Yes |
| `sync` | export stage | Export calendar/email snapshots to the pulse sync repo | Yes |
| `focus5` | derived local scan | Build the device-local Focus 5 roster + signal cache | No |
| `ask_self` | derived local scan | Inventory ask_self indexes on this device | No |

### Source → Table fanout

```
EXTERNAL SOURCES                  INGESTORS (src/rebalance/ingest/)                  STORAGE
                                                                                     (SQLite @ $REBALANCE_DB
                                                                                      + sqlite-vec)

GitHub REST API ─────▶ github_scan.py            user events (last 30d)       ──▶ github_activity
  (api.github.com)   │                                                            github_repo_meta
                     ├▶ github_knowledge.py      per-repo artifacts:           ──▶ github_items (issues/PRs)
                     │                             issues, PRs, comments,          github_comments
                     │                             reviews, commits, checks,       github_commits
                     │                             branches, milestones,           github_check_runs
                     │                             releases                        github_branches
                     │                                                             github_milestones
                     │                                                             github_releases
                     │                                                             github_links
                     │                                                             github_documents
                     │                                                          ─ github_embeddings (vec0)
                     ├▶ github_readiness.py      release-state inference       ── (reads only)
                     └▶ github_reconciliation.py issue ↔ PR matching           ── (reads only)

Obsidian Vault ──────▶ note_ingester.py          walk *.md, chunk, TF-IDF,    ──▶ vault_files, chunks,
  (filesystem)       │                             wikilinks                       keywords, links
                     └▶ embedder.py              Qwen3-Embedding-0.6B         ──▶ embeddings (vec0, 1024-dim)
                                                   via mlx-embeddings

Google Calendar ─────▶ calendar.py               OAuth token (keyring+JSON),  ──▶ calendar_events
  (Calendar API)                                   30d back / 7d forward

Sleuth Web API ──────▶ sleuth_reminders.py       Bearer auth, stdlib urllib,  ──▶ sleuth_reminders
  (Vultr dev :2020)                                GET /workspace/<name>/
                                                   reminders?format=rebalance

Gmail API ───────────▶ gmail.py                  desktop OAuth (gmail.readonly), ──▶ email_messages
  (gmail.googleapis.com)                           filter in:inbox by default,
                                                   newest 100 messages/run

Gmail MCP connector ─▶ gmail.py                  agent-pushed message payloads ─▶ email_messages
  (opt-in push path)                               via ingest_email_messages()

Figma Comments API ───▶ figma.py                 file-key allow-list + PAT    ──▶ figma_comments
  (api.figma.com)                                                                        │
                                                                                         └─▶ semantic_documents
                                                                                             semantic_embeddings

Project Registry ────▶ registry.py +              MD registry → projects.yaml ──▶ project_registry
  (vault markdown)     preflight.py                → SQLite projection
```

### Invocation points

| Source | CLI | MCP tool(s) | Daily-sync step |
|---|---|---|---|
| GitHub activity | `rebalance github-scan` | `github_balance` | 3 |
| GitHub artifacts | `rebalance github-sync-artifacts`, `github-embed`, `github-query` | `semantic_query`, `github_release_readiness`, `github_close_candidates` | on demand |
| Obsidian vault | `rebalance ingest notes`, `ingest embed`, `query`, `search` | `semantic_query`, `search_vault` | 1 + 2 |
| Google Calendar | `rebalance calendar-sync`, `calendar-create-event`, `calendar-snap-edges`, `calendar-daily-report`, `calendar-weekly-report` | `create_calendar_event`, `review_timesheet`, `classify_event`, `snap_calendar_edges` | 4 |
| Sleuth reminders | `rebalance sleuth-sync` | `sleuth_sync_reminders` | 5 |
| Email (Gmail) | `rebalance refresh`, `semantic-backfill`, `semantic-query` | `refresh_index`, `semantic_query`, `ingest_gmail_messages` | 6 |
| Figma comments | `rebalance refresh` | `refresh_index` | opt-in |
| Focus 5 | `refresh_index(scope=["focus5"])`, `rebalance serve` / pulse server | web `/focus-5` route | opt-in |
| ask_self inventory | `refresh_index(scope=["ask_self"])` | `list_ask_self_repos` | opt-in |
| Project registry | `rebalance ingest preflight`, `ingest sync`, `onboard` | `list_projects`, `run_preflight`, `confirm_projects`, `onboarding_status` | on demand |

> Registry write discipline (Phase 5, `ingest/lifecycle.py`): discovery is
> read-only and stamps candidates with `provenance` (remote-activity /
> vault-note; local-scan reserved); `confirm_and_write` is the only curated
> write path; activity inference maintains only rows it created (marked
> `inference.generated_by`) and never touches curated rows; priority rules
> overlay at read time and are never persisted.

> Preferred write path: `refresh_index(scope=[...])` is the orchestrated entry
> point. Several source-specific CLI/MCP write commands still exist for
> historical/operator reasons, but some of them bypass the collector/orchestrator
> layer and call leaf ingest functions directly.

> **Sleuth production is read from a published file — no inbound access.** The
> Sleuth box pushes its reminders to a private git repo
> (`rebalance-git-pulse:sync/sleuth/reminders-<ws>.json`); rebalance-OS reads the
> local clone (`base_url` is a `file://`/local path). No SSH tunnel, no open port.
> See [SLEUTH_SYNC.md](SLEUTH_SYNC.md). (Dev still hits the API directly.)

### Source → Consumer fanout (report & synthesis surfaces)

The GH-150 contract: every surface that reads the activity signal — script entrypoint,
scheduled job, MCP tool — has a row here, so "is this new report needed, and what does
it read?" is answered in the diff instead of buried in a 400-line file.
`tests/test_consumer_catalog.py` enumerates entrypoints (`__main__` under `utils/` +
`scripts/`, minus the pdda tooling and the stood-down 3-Eyes tree), scheduled-job
scripts (the SCHEDULER.md policy table), and MCP tools (`@mcp.tool()` in
`src/rebalance/mcp/tools/`) and fails on any surface without a row
(`uncataloged consumer`). Column rules the test enforces: **LLM primitive** is `querier`,
`none`, or `own (R2-baseline: <path>)` — a private client may only exist by naming the
ratchet baseline that will shrink when it dies; **Input path** containing "own SQL"
must name its `R1-baseline:` file the same way; **Replaces** is `—` or an existing
Surface. When fe1's shared read layer lands, new rows must read `db/queries.py` and the
baseline references become violations.

| Surface | Entrypoint | Cadence | Input path | LLM primitive | Channel | Replaces |
|---|---|---|---|---|---|---|
| Daily full refresh | scripts/daily_sync.sh | daily 06:30 | orchestrator (`refresh_index`) | none | DB write | — |
| Hourly GitHub sync | scripts/github_sync.sh | hourly :45 | orchestrator (`refresh_index`, artifact window 7d) | none | DB write | — |
| Vault embeddings job | scripts/obsidian_vault_embeddings.sh | hourly :15 | orchestrator (`refresh_index` vault+semantic) | none | DB write | — |
| Pulse page | scripts/pulse_sync.sh | hourly :00 | pulse renderer (own SQL R1-baseline: src/rebalance/ingest/pulse.py) | none | pulse repo README | — |
| Pulse web render | scripts/pulse_web_sync.sh, scripts/pulse_web.py | 30 min | pulse renderer (same snapshot) | none | web/pulse.html | Pulse page |
| Pulse server | scripts/pulse_server.sh, scripts/pulse_server.py | daemon | DB read layer + pulse renderer | none | localhost:8767 | — |
| Pulse warning watch | scripts/pulse_warning_watch.py | 15 min | HTTP probe of pulse-server | none | temp JSONL | — |
| Daily work synthesis canary | scripts/daily_work_synthesis.sh, utils/daily_work_synthesis.py | 15 min, opt-in | existing CLIO/calendar/reminder read APIs + Daily repository/CPU scanners | own (R2-baseline: utils/daily_work_synthesis.py) | append-only temp Daily log + sanitized receipt JSONL | — |
| CLIO journey replay | src/rebalance/ingest/clio_journey.py (`rebalance clio-journey-replay`) | manual, opt-in | frozen CLIO export + bounded read-only GitHub snapshot (GH-230 exception) | none | new private replay directory | — |
| Health issue reporter | scripts/health_issue_reporter.py | hourly :10 + 3×/day triage | doctor subprocess + GitHub API | own (R2-baseline: scripts/health_issue_reporter.py) | GitHub issues | — |
| Daily note rollover | utils/obsidian_rollover.sh, utils/obsidian_daily_rollover.py | daily 00:40 | vault filesystem | none | Obsidian daily note | — |
| Progress digest | scripts/hiqs_digest.sh, utils/hiqs_digest.py | 2×/day 13:05/17:05 | own SQL (R1-baseline: utils/hiqs_digest.py) + doctor + semantic | querier | pulse repo digests/ → Slack relay | — |
| Daily synthesis | utils/daily_synthesis.sh, utils/daily_synthesis.py | daily 18:20 | pulse.collect_pulse_snapshot + git-pulse device files | querier | Obsidian note + CLIO log | — |
| Dashboard note | src/rebalance/ingest/note_builder.py | on refresh | own SQL (R1-baseline: src/rebalance/ingest/note_builder.py) + calendar | own (R2-baseline: src/rebalance/ingest/note_builder.py) | vault dashboard note | — |
| Claude Cloud signal grade | utils/claude_cloud_daily_grade.py | daily | ingest/claude_cloud sessions API | none | Obsidian block | — |
| Claude Cloud jobs POC | scripts/cc_cloud_jobs.py | manual | api.anthropic.com fetch (R2-baseline: scripts/cc_cloud_jobs.py) + gh | none | stdout + temp/ | Claude Cloud signal grade |
| Web dashboard data | scripts/dashboard.py | manual | own SQL (R1-baseline: scripts/dashboard.py) | none | dashboard payload | — |
| Chat eval | scripts/chat_eval.py | manual | eval corpus | none | stdout | — |
| Module audit | scripts/audit_modules.py | manual / MCP | repo tree + docs | none | audit report | — |
| Doc link check | scripts/check_doc_links.py | manual | repo docs | none | stdout | — |
| Extension build | scripts/build_extension.py | manual | capabilities tree | none | built artifacts | — |
| Capabilities index | scripts/generate_capabilities_index.py | manual | repo tree | none | capabilities index | — |
| Calendar OAuth setup | scripts/setup_calendar_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Gmail OAuth setup | scripts/setup_gmail_oauth.py | manual | OAuth flow | none | keyring/token | — |
| Cloud daily grade helpers | utils/job_guard.py | per job | process guard | none | job lifecycle | — |
| Vector store reclaim | utils/gh250/reclaim.py | manual (historical) | vector store | none | store maintenance | — |
| Releases ledger CLI | utils/py/releases_app.py | manual | releases.db | none | ledger + dump | — |
| Releases cycle rollup | utils/py/releases_cycle.py | on demand | releases.db (read-only) | none | rollup markdown/dashboard | — |
| MCP: index_status | src/rebalance/mcp/tools/index.py | on demand | status snapshot (coverage probe) | none | MCP | — |
| MCP: refresh_index | src/rebalance/mcp/tools/index.py | on demand | orchestrator | none | MCP | — |
| MCP: diagnose_repo | src/rebalance/mcp/tools/index.py | on demand | own SQL (R1-baseline: src/rebalance/ingest/diagnose.py) | none | MCP | — |
| MCP: list_watched_repos | src/rebalance/mcp/tools/index.py | on demand | watched-set view | none | MCP | — |
| MCP: list_ask_self_repos | src/rebalance/mcp/tools/index.py | on demand | ask_self index | none | MCP | — |
| MCP: publish_pulse | src/rebalance/mcp/tools/index.py | on demand | pulse renderer | none | MCP | — |
| MCP: peek_source | src/rebalance/mcp/tools/index.py | on demand | parameterized table peek | none | MCP | — |
| MCP: get_next_actions | src/rebalance/mcp/tools/index.py | on demand | next_actions engine (R1-baseline: src/rebalance/ingest/next_actions.py) | querier | MCP | — |
| MCP: semantic_query | src/rebalance/mcp/tools/index.py | on demand | semantic index | none | MCP | — |
| MCP: audit_modules | src/rebalance/mcp/tools/hygiene.py | on demand | repo tree + docs | none | MCP | — |
| MCP: calendar tools | src/rebalance/mcp/tools/calendar.py | on demand | calendar_events | none | MCP | — |
| MCP: onboarding tools | src/rebalance/mcp/tools/onboarding.py | on demand | registry/lifecycle + gmail push | none | MCP | — |
| MCP: projects tools | src/rebalance/mcp/tools/projects.py | on demand | registry; github_balance → own SQL (R1-baseline: src/rebalance/ingest/github_scan.py) | none | MCP | — |
| MCP: retrieval tools | src/rebalance/mcp/tools/retrieval.py | on demand | vault FTS; readiness → own SQL (R1-baseline: src/rebalance/ingest/github_readiness.py) | querier | MCP | — |
| MCP: sleuth tools | src/rebalance/mcp/tools/sleuth.py | on demand | sleuth source | none | MCP | — |

Grouped rows (one row covering several same-shape tools, e.g. "MCP: calendar tools")
name their module; the test resolves them. Two surfaced read paths have no entrypoint
of their own and are carried by the rows above: `pulse.collect_pulse_snapshot`
(daily synthesis) and the querier synthesis primitive itself.

### Credentials

| Source | Secret store | Mechanism |
|---|---|---|
| GitHub | OS keyring + out-of-repo secret store (`~/.config/rebalance-os/secrets`, `0600`) fallback; `gh` CLI as last-resort read fallback | PAT: classic `repo` scope, or fine-grained with All-repos read-only Contents/Metadata (public-only tokens hide private work); persisted to keyring + secret store for launchd reachability — no longer written to `temp/rbos.config` |
| Google Calendar | `google-calendar.env` (client credentials) via `resolve_secret_path()` + OAuth user-token in keyring with a JSON fallback at `~/.config/rebalance-os/secrets/google-calendar-oauth` (a legacy pickle migrates to JSON on read) | OAuth 2.0 user consent |
| Sleuth | OS keyring + secret store (`~/.config/rebalance-os/secrets/sleuth_web_api`); legacy `*.env` files still read for un-migrated devices | Bearer token, 64-hex |
| Gmail | Desktop OAuth token in keyring + JSON fallback at `~/.config/rebalance-os/secrets/google-gmail-oauth`, or MCP push-ingest mode | `gmail.readonly` desktop OAuth, or agent-pushed `ingest_gmail_messages` path when `gmail_ingest_method=mcp` |
| Figma | OS keyring + secret store for the PAT; `temp/rbos.config` holds only the (non-secret) file-key allow-list | Personal access token + explicit file selection |
| Obsidian vault | none | filesystem read only |

Env-file paths resolve via [src/rebalance/paths.py](src/rebalance/paths.py)::`resolve_secret_path(name)` — the layered chain is `REBALANCE_SECRETS_DIR` env var → `secrets_dir` field in `~/.config/rebalance-os/config.json` (set via `rebalance config set-secrets-dir`) → `~/secrets/` legacy default. The domain CLI loaders (for example, [src/rebalance/cli/calendar.py](src/rebalance/cli/calendar.py) and [src/rebalance/cli/sleuth.py](src/rebalance/cli/sleuth.py)) use this resolver, so the repo is portable across operator home directories without hardcoded env-file paths. Env files should sit at mode 600. Env files are parsed manually (no `python-dotenv`). Nothing with a secret value is committed.

### Adding a New Source

> **The current preferred way to add a source is the collector / `SourceModule`
> contract — see [src/rebalance/ingest/index_ops.py](src/rebalance/ingest/index_ops.py)
> and the developer guide [PLUGINS.md](PLUGINS.md).** It covers the registry
> descriptor, the optional `semantic_docs` provider, secrets/keyring, numbered
> migrations, and tests, with Figma as the worked example. The steps below are
> the practical recipe for the built-in sources.

1. **Collector** — write `src/rebalance/ingest/<source>.py` following the `sleuth_reminders.py` or `github_scan.py` shape: a dataclass for one record, a `sync_*()` function that fetches → normalizes → upserts, and a module-local `ensure_<source>_schema(conn)`. Use `db_connection(path, ensure_fn)` from the `ingest/db/` package.
2. **Schema** — keep the `CREATE TABLE` inside `ensure_<source>_schema`. Only promote to the shared `ingest/db/` package if more than one module needs it. Use existing tables for unstructured text that should be embedded.
3. **Registry** — register the source in `index_ops.py` with `register_collector(Collector(...))`. Add `requires=...`, `semantic_docs=...`, and/or `candidates=...` metadata if the source needs preconditions, participates in the unified semantic index, or contributes next-action candidates to the HiQS ranking. The `candidates=` provider is how a source reaches the ranked "what to do next" verdict — no edit to the ranker's dispatch.
4. **Credentials** — if the source uses env-style secret files, resolve them through `resolve_secret_path()` and a small domain loader (see `cli/calendar.py` / `cli/sleuth.py`). Never hardcode secrets in repo files.
5. **Next-action candidates** — to feed the HiQS ranking, supply a `candidates=` provider on the `Collector` (a function `bundle → list[candidate dict]`, each Attested with `source`/`evidence`/`why`). `_operator_candidates()` walks the registry, so no ranker edit is needed. A source participates in `ask()` automatically once it is in the ranked bundle — `ask()` reads the whole ranking via `_gather_hiqs_context()`.
6. **Prompt section** — the HiQS section in `_build_prompt()` already renders every ranked source; add a bespoke `_build_prompt()` block only for context that is NOT a ranked next-action.
7. **CLI + MCP** — add thin wrappers in `src/rebalance/cli/*` and `src/rebalance/mcp/tools/*` if the source needs direct user-facing operations beyond `refresh_index()`.
8. **Scheduled refresh** — ensure `included_in_all` and any explicit scheduler usage match the source's intended unattended behavior.
9. **Tests** — add `tests/test_<source>.py` that stubs the outbound call (patch `urlopen` for HTTP, filesystem for local sources). Verify insert / unchanged / update semantics.

No changes needed to the query layer, LLM synthesis, or MCP transport.

---

## Storage Layer

Single SQLite file resolved by `src/rebalance/paths.py::resolve_database_path()`. Default canonical location is `~/Library/Application Support/rebalance-os/rebalance.db` on macOS (or `$XDG_DATA_HOME/rebalance-os/rebalance.db` on Linux); `REBALANCE_DB` env var, an `--database` flag, or a user-config override all win against the canonical path when set. sqlite-vec extension loaded for vector operations.

### Write discipline (one writer per table)

The single most important invariant for a new maintainer to preserve:

- **Reads are unrestricted.** Anything may open `db_connection()` and `SELECT`. The "Tables by Domain" list below names the *writer* for each table — that ownership is about **writes**, not reads.
- **One writer per table.** Each table is written by exactly one module (e.g. `github_activity` ← `github_scan.py`, `sleuth_reminders` ← `sleuth_reminders.py`, `semantic_documents` ← the `semantic` stage only). Do not add a second writer; extend the owning collector instead.
- **Writes go through the orchestrator.** New ingestion/refresh writes register as a `Collector` in `index_ops.py` and run under `refresh_index()` — not as a fresh leaf that opens `db_connection()` and upserts on its own.
- **Known, accepted exceptions (direct `db_connection()` writers outside `refresh_index`).** A few interactive/operator commands write directly *by design* — they are human-in-the-loop mutations, not unattended ingest: `rebalance github-sync-artifacts` (`cli/github.py::github_sync_artifacts()`) and the `rebalance apple-reminders` write path (`cli/apple_reminders.py`). Most other direct `db_connection()` calls from `cli/*` (`onboard`, `config-doctor`, `raw`, `dashboard-render`) are **reads**, which are fine. If you add a new direct *writer*, document it here and say why it can't go through the registry.

### Tables by Domain

```
Project Registry (writer: registry.py::sync_db(), the single low-level upsert)
  project_registry          — canonical project metadata. Rows are either curated
                               (write_semantics="confirmation_gated", written only
                               via the onboarding confirm_projects()/confirm_and_write()
                               path — see lifecycle.py) or machine_owned (never
                               clobbers a curated row of the same name). Two
                               machine_owned producers currently call sync_db():
                               project_inference.py's activity/calendar inference
                               (generated_by "activity_inference_v1") and GH-124's
                               commit-threshold auto-promotion (generated_by
                               "commit_threshold_v1", wired into _refresh_github()
                               in index_ops.py, immediately after the watchlist
                               guard). _is_inference_owned() recognizes both markers.

GitHub activity (writer: github_scan.py)
  github_activity            — per-repo event counts, keyed by (login, repo, scan_date)

GitHub artifacts (writer: github_knowledge.py; schema in `ingest/db/`)
  github_repo_meta           — repo-level metadata (default branch, issue/project support)
  github_branches            — local branch inventory for promotion/release inference
  github_labels              — label dictionary per repo
  github_milestones          — open/closed milestones with due dates
  github_releases            — published tags/releases
  github_items               — issues and PRs (unified table, item_type discriminates)
  github_comments            — issue/PR/review comments
  github_commits             — PR commit history
  github_check_runs          — CI check results per head_sha
  github_links               — explicit and inferred issue↔PR cross-references
  github_documents           — per-artifact embeddable document rows
  github_embeddings          — sqlite-vec virtual table for artifact embeddings
  github_embedding_meta      — model name + dim for the GitHub corpus

Unified Semantic Index (single writer: the `semantic` collector stage in index_ops.py)
  semantic_documents         — canonical cross-source document rows (vault chunks +
                               GitHub issues/PRs/comments/commits, Gmail
                               messages, and registry-provider sources such as
                               Figma comments). Written exclusively by
                               _refresh_semantic_only() via
                               semantic_index.py::backfill_semantic_documents().
                               Consumed by semantic_query() and the LLM context layer.
  semantic_embeddings        — sqlite-vec virtual table, float[1024], keyed by
                               semantic_documents.id. Unified ANN search target.
  semantic_embedding_meta    — model name, dimension, embedder_version, last_embed_at

Vault Ingestion (writer: note_ingester.py)
  vault_files                — one row per .md file, with content_hash for delta detection
  chunks                     — heading-based chunks, FK to vault_files (CASCADE delete)
  keywords                   — TF-IDF top-K per chunk, FK to chunks (CASCADE delete)
  links                      — wikilinks and embeds, FK to vault_files (CASCADE delete)

Embeddings (writer: embedder.py)
  embeddings                 — sqlite-vec virtual table, float[1024], keyed by chunk_id
  embedding_meta             — model name, dimension, last embed timestamp

Email (writer: gmail.py)
  email_messages             — message metadata + snippet, keyed by Gmail message_id.
                               Upsert-only rolling window (newest matching messages);
                               also projected into semantic_documents.

Google Calendar (writer: calendar.py)
  calendar_events            — event id, summary, start/end, location, attendees, description
                               Keyed by Google event ID (INSERT OR REPLACE). Default sync window
                               is 30 days back + 7 days forward (365-day backfill available via
                               the CLI). No automatic deletion; manual cleanup if pruning is needed.

Sleuth reminders (writer: sleuth_reminders.py)
  sleuth_reminders           — one row per Slack reminder, keyed by reminder_id (TEXT PK).
                               Upsert with diff-based insert/update/unchanged counts;
                               first_seen_at preserved across syncs. Rows are never
                               deleted — state transitions (scheduled → posted → completed)
                               are mirrored as UPDATEs.

Figma (writer: figma.py)
  figma_comments             — comment rows keyed by Figma comment key, synced from
                               an explicit file-key allow-list. Also projected into
                               semantic_documents via the registry-provider path.

Device-local inventories / derived jobs
  ask_self_indexes           — per-device inventory of ask_self indexes found on disk
  focus5_repo_signals        — cached per-repo Focus 5 signals for the current device
  focus5_roster              — persisted top-5 Focus 5 roster snapshot
```

### Sync semantics per source

Every source is incremental, but the meaning of "incremental" depends on what the upstream API supports. The three patterns from [Sync model](#sync-model-in-plain-english) map cleanly onto the table below:

- **Vault notes** — *hash delta.* SHA-256 of raw file bytes stored in `vault_files.content_hash`. On re-ingest, unchanged-content files have their `last_modified` refreshed if the on-disk mtime moved forward (a "touch") but skip all parsing and embedding work — surfaced as `touched_files` in the ingest result. Changed-content files are deleted (CASCADE clears chunks/keywords/links) and re-inserted.
- **GitHub activity** — *window refetch.* Keyed by `(login, repo_full_name, scan_date)` with `ON CONFLICT REPLACE`. Each scan re-pulls the user's last ~30 days of events and overwrites *today's* row only; older days are left alone.
- **GitHub artifacts** — *hash/ID delta with window.* Keyed by `(repo_full_name, item_type, number)` for items; comments/commits/checks keyed by GitHub ID. `ON CONFLICT REPLACE` on every sync, with a `since_days` lookback to skip artifacts that haven't been touched in that window.
- **Embeddings** — *hash delta.* Chunks (vault) or documents (GitHub corpus) without a corresponding embeddings row get embedded. A model-version change recorded in `embedding_meta` / `github_embedding_meta` triggers a full re-embed of that corpus.
- **Calendar** — *window refetch.* Keyed by Google event ID with `INSERT OR REPLACE`. Re-sync overwrites existing events and adds new ones within the requested window (default 30d back / 7d forward; 365d on demand for backfill). No auto-deletion — events removed upstream stay in the local DB until manually pruned.
- **Sleuth reminders** — *full refetch + column-diff.* Keyed by `reminder_id`. Column-level diff against the stored row decides insert/update/unchanged; `first_seen_at` is set on insert and never overwritten; `last_seen_at` and `last_synced_at` refresh on every sync. Missing reminders are NOT deleted — terminal states (`completed`, `canceled`) remain as history.
- **Email (Gmail)** — *window refetch, count-bounded.* Keyed by Gmail `message_id` with upsert. Each run pulls the newest 100 messages matching the configured filter (default `in:inbox`, override via `gmail_query_filter` in `temp/rbos.config`). Phase 1 stores metadata + Gmail snippet only — no full body, no historical backfill, no auto-delete. See [PROJECT/1-INBOX/EMAIL-INGEST.md](PROJECT/4-MISC/ARCHIVED-PREDECESSOR/1-INBOX/EMAIL-INGEST.md).

---

## Query Layer

All consumers read from the same SQLite file. The query layer is source-agnostic.

**Read-side ownership model (Phase 3, Option C):**

| Surface | Role | Owner |
|---|---|---|
| `semantic_query()` MCP tool | Unified raw retrieval primitive | `semantic_index.query()` — owns source vocabulary, freshness, hybrid RRF |
| `chat_with_data()` | Citations-first interactive retrieval | `chat.py` — owns scope aliases (`work`/`code`/`all`), citation shaping; delegates retrieval to `semantic_index` |
| `ask()` | Broad mixed-context synthesis/orchestration | `querier.py` — owns project/calendar/temporal framing; not the canonical retrieval primitive |

```
SQLite @ $REBALANCE_DB
   │
   ├──▶ semantic_index.query()     ── unified raw retrieval primitive
   │    (MCP: semantic_query)          source vocab + hybrid RRF
   │         │
   │         ├──▶ chat_with_data() ── citations-first presentation layer
   │         │    (dashboard /api/chat)  scope aliases, citation shaping
   │         │
   │         └──▶ ask() (partial)  ── contributes to synthesis context
   │
   ├──▶ querier.py::ask()          ── broad orchestrator: gathers project,
   │    (MCP: ask, CLI: ask)           calendar, temporal + semantic signals;
   │                                   synthesizes via local Qwen3 (optional)
   │
   ├──▶ daily_report.py /          ── per-day / per-week calendar rollups
   │    weekly_report.py              with project classification
   │
   ├──▶ github_scan.py             ── per-project commit/PR/issue counts
   │    ::get_github_balance()        (surfaced as the github_balance MCP tool)
   │
   ├──▶ github_readiness.py /      ── release-state inference + issue↔PR
   │    github_reconciliation.py       close candidates
   │
   └──▶ mcp/server.py              ── exposes all of the above as MCP tools
                                       to Claude Code, Claude Desktop, etc.
```

`querier.py` is the synthesis orchestrator (not the retrieval primitive). A single `ask()` call:

1. **Gathers context** from all sources in parallel-ready functions:
   - `_gather_project_context()` — registry entries + repos map
   - `_gather_github_context()` — per-project activity summary (from `github_activity`)
   - `_gather_github_semantic_context()` — semantic recall over the GitHub corpus (`github_documents` + `github_embeddings`)
   - `_gather_vault_context()` — semantic search (embed query → ANN)
   - `_gather_vault_activity()` — recently modified files
   - `_gather_calendar_context()` — upcoming + recent events from `calendar_events`
   - `_gather_temporal_context()` — day-of-week / weekend / holiday framing for the prompt
   - `_gather_hiqs_context()` — the persisted **HiQS** ranked verdict (see below). A cheap
     cached read (`load_ranked_next_actions()`); it never recomputes. This is how Sleuth,
     Gmail, and Figma reach `ask()`: they are already in the one ranked bundle, so `ask()`
     surfaces them via the shared ranking rather than a per-source gatherer.

2. **Assembles a prompt** with all context formatted into labeled sections — including a
   `## HiQS — ranked next actions` section carrying each action's receipts. The ranking is
   also returned first-class on `QueryResult.hiqs`.

3. **Synthesizes** via local Qwen3 LLM (mlx-lm). Returns both synthesis and raw context.

### The Next Actions engine ("what to do next")

A distinct read-side subsystem in [src/rebalance/ingest/next_actions.py](src/rebalance/ingest/next_actions.py) — structurally one of the larger clusters in the codebase. It is **HiQS**: the single, unified work-signal pipeline — **one bundle spanning all six sources (GitHub, vault, Calendar, Sleuth/Slack, Gmail, Figma), one ranked verdict, read by every surface**. `ask()` and the dashboard's what's-next view read the *same* persisted ranking, so they cannot drift. It also drives the fixed vault file `Dashboards/What To Do Next.md`.

Pipeline (real symbols):

1. **`assemble_day_bundle()`** gathers the operator's own day signal across all six sources into an `OperatorBundle`, plus teammate deltas (`_gather_teammate_delta()`). Candidates are built by **`_operator_candidates()`, which WALKS the collector registry** — each source owns its candidate shape via the `candidates=` provider on its `Collector` (the same registry seam as `semantic_docs=`). A new work signal reaches the ranked verdict by registering a collector, never by editing this dispatch (GUIDING-PRINCIPLES Principle 3).
2. **`build_rank_prompt()`** formats the candidates; **`rank_next_actions()`** synthesizes the ranking. **Primary path = Gemini** (`get_gemini_api_key()` → `gemini-2.5-flash`); a deterministic local fallback (Qwen) keeps it working offline. `_parse_ranked_synthesis()` rejects placeholder echoes.
3. Output is a **`RankedNextActions`** (list of `RankedAction`), **persisted** to a cache table via `persist_ranked_next_actions()` and read back by `load_ranked_next_actions()`.
4. **`render_next_actions_markdown()`** writes the ranked list to the fixed vault file (single-writer, generated).
5. **Consumers:** the `web.py` what's-next route (`whatsnext_page()`) is the single WRITER (its `?refresh` path ranks + persists); `ask()` is a READER that exposes the persisted ranking as the first-class `QueryResult.hiqs` field. Neither re-ranks inline, so the two surfaces are structurally incapable of drifting.

### Two-Layer LLM Architecture

```
User question
  │
  ▼
ask() tool ──▶ Local Qwen3-0.6B (Layer 1)
  │              - Sees all raw context
  │              - Fast first-pass synthesis
  │              - Runs on-device via MLX
  │
  ▼
Returns to host agent (Layer 2)
  │              - Claude, Copilot, Gemini, etc.
  │              - Reviews synthesis + raw context
  │              - Fact-checks against raw data
  │              - Adapts, refines, presents to user
  │
  ▼
User sees final answer
```

**Why two layers?** The local model is fast and private — it never sends vault content to the cloud. But it's small (0.6B) and makes mistakes. The host agent is larger, smarter, and can fact-check against the raw context that's returned alongside the synthesis. The user gets speed + accuracy + privacy.

**`skip_synthesis=True`** bypasses Layer 1 entirely and returns raw context only. Use this when the host agent is capable enough to do its own synthesis (e.g., Claude).

---

## Invocation Modes

Four ways the pipeline runs:

1. **Interactive CLI** — `rebalance <subcommand>` via the Typer package under `src/rebalance/cli/`. Ad-hoc and one-shot workflows (`calendar-create-event`, `github-release-readiness`, `sleuth-sync --json`, `profile-sync`, `raw`, etc.). `rebalance` invoked with no arguments launches the live dashboard (mode 4). `rebalance raw [--minutes N] [--watch S] [--json]` is a calibration probe: 1 GitHub API request per invocation, classifies recent events as captured / pending / unwatched against the local pipeline state, used to verify that commits/PRs/issues are making it into rebalanceOS.

2. **Unattended scheduled syncs** — a launchd fleet of ten jobs. [SCHEDULER.md](SCHEDULER.md) is the policy table (single source of truth for labels, cadences, scopes, prerequisites, and outputs; enforced by `tests/test_scheduler_policy.py`). The six data/render jobs, conceptually:

   - **Daily all-scope sync** ([scripts/daily_sync.sh](scripts/daily_sync.sh) / [scripts/com.rebalance-os.daily-sync.plist.template](scripts/com.rebalance-os.daily-sync.plist.template)) at 06:30 local time, plus on boot/login if 06:30 was missed. Calls `refresh_index()` with no scope (the **default recipe**): all raw sources (`vault`, `github`, `calendar`, `sleuth`, `email`) followed by the derived/projection/export stages (`code`, `semantic`, `sync`). Note: `scope=["all"]` is *not* the same as the default recipe — after Phase 1b, `all` expands to raw sources only; the default no-scope path runs the full recipe including follow-on stages. Opt-in scopes (`figma`, `focus5`, `ask_self`) are never included automatically. Per-scope failures are captured in `errors` rather than aborting the run.
   - **Hourly obsidian vault embeddings refresh** ([scripts/obsidian_vault_embeddings.sh](scripts/obsidian_vault_embeddings.sh) / [scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template](scripts/com.rebalance-os.obsidian-vault-embeddings.plist.template)) at HH:15 from 06:15 to 23:15. Calls `refresh_index(scope=["vault", "semantic"])` — keeps notes edited mid-day visible in **both** the dashboard/pulse (vault ingest) and **semantic search** (semantic projection stage). Vault ingest with no changes is ~0.02s; the lightweight BGE-Small (384-dim, ~20MB) semantic stage embeds rows where content changed in milliseconds.
   - **Hourly pulse publish** ([scripts/pulse_sync.sh](scripts/pulse_sync.sh) / [scripts/com.rebalance-os.pulse-sync.plist.template](scripts/com.rebalance-os.pulse-sync.plist.template)) on the hour, 06:00 to 23:00. Renders the operator pulse markdown and pushes it to the configured private repo, but only when the rendered content actually changed since the previous run.
   - **30-minute pulse-web refresh** ([scripts/pulse_web_sync.sh](scripts/pulse_web_sync.sh) / [scripts/com.rebalance-os.pulse-web-sync.plist.template](scripts/com.rebalance-os.pulse-web-sync.plist.template)) every 30 minutes from 06:00 to 23:30. Calls [scripts/pulse_web.py](scripts/pulse_web.py) to regenerate the local `web/pulse.html` mirror of the dashboard. Atomic via tmp+replace (a crashed run leaves the previous HTML intact). No network, no git push — separate from the markdown→private-repo flow above.
   - **Hourly GitHub sync** ([scripts/github_sync.sh](scripts/github_sync.sh) / [scripts/com.rebalance-os.github-sync.plist.template](scripts/com.rebalance-os.github-sync.plist.template)) — a narrower github-only refresh independent of the daily full sync, for environments that want fresher GitHub data without paying the full multi-source cost.
   - **Pulse server (long-running, not scheduled)** ([scripts/pulse_server.sh](scripts/pulse_server.sh) / [scripts/com.rebalance-os.pulse-server.plist.template](scripts/com.rebalance-os.pulse-server.plist.template)) — a FastAPI/uvicorn server on `127.0.0.1:8767` with `RunAtLoad` + `KeepAlive` (autostart at login, restart on crash, `ThrottleInterval=30s`). Adds an interactive layer (real Refresh button + filter) on top of the static `web/pulse.html` the pulse-web job regenerates, **and is the always-on JSON backend for the macOS Focus 5 Float app** ([macOS/Apps/Focus5Float](macOS/Apps/Focus5Float)) — it serves `/focus-5.json` (roster), `/focus-5/goals`, and `/focus-5/note` so the app works without a separate `rebalance serve` on `:8787`. Loopback bind is enforced in [scripts/pulse_server.py](scripts/pulse_server.py). Unlike the five scheduled jobs above, it runs continuously rather than firing on a calendar interval.

     **Drift gotcha (has bitten the Focus 5 app twice):** [scripts/pulse_server.py](scripts/pulse_server.py) does *not* mount `rebalance.web`'s app — it hand-re-declares a chosen *subset* of its routes by importing the renderers. Two consequences: (1) a route added to `web.py` is invisible on `:8767` until a matching wrapper is added to `pulse_server.py` (this is how `/focus-5.json` was missed); (2) because it's a `KeepAlive` daemon, any route change requires `launchctl kickstart -k gui/$UID/com.rebalance-os.pulse-server` to take effect — a long-running process keeps serving its old route table otherwise (this is how a freshly-added `/focus-5/goals` still 404'd).

   The remaining four jobs (health-check hourly, health-check-triage 3×/day, pulse-warning-watch every 15 min, obsidian-rollover at midnight) plus **daily-synthesis** at 18:20 are operational/maintenance agents — see [SCHEDULER.md](SCHEDULER.md). The **daily-synthesis** job ([utils/daily_synthesis.sh](utils/daily_synthesis.sh) / [scripts/com.rebalance-os.daily-synthesis.plist.template](scripts/com.rebalance-os.daily-synthesis.plist.template), GH-74) does two syntheses in one process, in order: first a Gemini daily-activity summary from the structured `collect_pulse_snapshot()` output, then a Gemini synthesis of multi-device git commit logs aggregated via `experimental/git-pulse/view.sh --today`. Each lands in its own idempotent sentinel-bracketed block at the bottom of the vault's `0. Today's Notes.md`, pulse block first. (It replaces two formerly separate jobs, obsidian-daily-sync at 18:20 and git-pulse-daily-synthesis at 18:30, which existed as two launchd jobs only so the second could fire after the first — see `utils/daily_synthesis.py`'s module docstring.) Both syntheses use Gemini-or-skip logic (no Qwen fallback) and the merged job carries one late-run guard to prevent colliding with the 00:00 rollover.

   Wrapper scripts source [scripts/lib/scheduler_common.sh](scripts/lib/scheduler_common.sh) for env bootstrap (repo root, venv python, `PYTHONPATH`), per-day logs under `temp/logs/`, job-lifecycle events into `auth_activity.jsonl`, and log retention. Installers source [scripts/lib/install_common.sh](scripts/lib/install_common.sh) for one normalized flow: always-unload, render the `.plist.template` (`{{REBALANCE_DIR}}`, `{{PYTHON}}`, `{{HOME}}`), `plutil -lint`, load, poll-verify registration. The rendered plists in `~/Library/LaunchAgents/` are gitignored — the templates are the only checked-in form, so a clone on any machine installs cleanly with no per-user editing.

3. **MCP tool handlers** — [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py) registers the tools; [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) remains as the backward-compatibility shim for older launch commands. Host agents (Claude Code / Claude Desktop) call these on demand. `REBALANCE_DB` env var resolves the shared DB path.

4. **Live dashboard** — [scripts/dashboard.py](scripts/dashboard.py) is a Rich Live monitor that polls the local SQLite every 2 seconds (cheap; no network) and runs `refresh_index(scope=["github"])` in a background thread every 10 minutes so the underlying data actually changes. Launch via `rebalance` (no args) or `rebalance dashboard`. Press `r` to trigger an immediate GitHub refresh, `q` (or Ctrl+C) to quit. Theming and cadence are env-var controlled (`PULSE_INVERSE`, `PULSE_TICK`, `PULSE_AUTO_MIN`, `REBALANCE_TZ`). The dashboard is intentionally read-only against the same DB the MCP server and the launchd jobs write to.

---

## MCP Tool Surface

Tools are registered in [src/rebalance/mcp/server.py](src/rebalance/mcp/server.py)::`create_server()`. [src/rebalance/mcp_server.py](src/rebalance/mcp_server.py) is a backward-compatibility shim so older launch commands still work. All tools share the same `database_path` resolved at server startup from `REBALANCE_DB`.

| Category | Tool | Purpose |
|----------|------|---------|
| Query | `ask` | Natural language query across all sources (with optional local LLM synthesis) |
| Query | `search_vault` | Vault keyword search (TF-IDF) |
| Query | `github_balance` | Per-project GitHub activity summary |
| Query | `github_release_readiness` | Infer milestone/release readiness from the local GitHub corpus |
| Query | `github_close_candidates` | Suggest open issues that likely map to merged PRs |
| Query | `semantic_query` | Unified vector search across indexed sources (single ranked result set; filter with `sources`) |
| Diagnostics | `index_status` | Snapshot of every source + semantic index freshness (read-only) |
| Diagnostics | `refresh_index` | Orchestrated refresh of the local knowledge base (single entry point) |
| Diagnostics | `list_watched_repos` | Show merged set of repos being monitored (project registry ∪ activity − ignored) |
| Diagnostics | `diagnose_repo` | Walk the watched-repos + sync funnel for a single repo (optionally a `sha` or `pr`) and explain coverage + freshness gaps; opt-in `live=True` distinguishes "we never synced" from "PAT can't see it" |
| Registry | `list_projects` | Query project registry |
| Onboarding | `onboarding_status` | Check setup completion |
| Onboarding | `setup_github_token` | Validate and store GitHub PAT |
| Onboarding | `run_preflight` | Discover project candidates (read-only) |
| Onboarding | `confirm_projects` | Write registry and sync |
| Onboarding | `ingest_gmail_messages` | Agent-pushed Gmail ingest path for installs using `gmail_ingest_method=mcp` |
| Calendar | `create_calendar_event` | Create a Google Calendar event via local OAuth |
| Calendar | `review_timesheet` | Surface unclassified calendar events that need a project decision |
| Calendar | `classify_event` | Persist an include/exclude/project classification for an event |
| Calendar | `snap_calendar_edges` | Detect and (optionally) fix slightly overlapping events |
| Sync | `sleuth_sync_reminders` | Pull Slack reminders from the Sleuth Web API and upsert to SQLite |
| Sync | `publish_pulse` | Render today+yesterday activity to markdown and push to private pulse repo |
| Hygiene | `audit_modules` | Run [scripts/audit_modules.py](scripts/audit_modules.py) and return the structured JSON result. Verifies that ingest collectors / render modules / scheduled-job infrastructure are documented in ARCHITECTURE.md and CHANGELOG.md, and that recent commits' file changes appear in the latest CHANGELOG version section. Supports `init=True` to snapshot the baseline lockfile and `include_uncommitted=True` for a pre-commit working-tree preview |

Tool specs (params, returns, dependencies): see [MCP.md](MCP.md).

---

## Module Map

```
src/rebalance/
  __init__.py              — package version
  __main__.py              — CLI entry point
  cli/                     — Typer command package split by domain
  mcp/                     — FastMCP server + tool modules
  mcp_server.py            — backward-compatibility shim to rebalance.mcp.server
  paths.py                 — centralized path resolver. `resolve_database_path()` and
                              `resolve_secret_path()` walk a layered chain (explicit
                              flag → env var → canonical app-data path → user
                              config → cwd walk-up for project marker). Single
                              source of truth for "where is the DB / secrets dir?"
                              `resolve_project_root(Path(__file__))` (walk-up) is the
                              stable repo-root resolver used throughout the codebase —
                              replaces all `parents[N]` hacks. `resolve_oauth_token_path(service)`
                              returns the canonical launchd-reachable token path for
                              Google OAuth services. Configure user defaults via
                              `rebalance config set-default-database` and `set-secrets-dir`.
  web.py                   — FastAPI local dashboard/web surfaces (`/`, `/focus-5`, `/auth-log`, etc.)
  ingest/health_log.py     — doctor check TRANSITIONS into the unified system log (GH-101)
  doctor.py                — installation health checks; backs `rebalance doctor`
  ingest/
    config.py              — secrets storage (temp/rbos.config)
    registry.py            — project registry sync (Markdown ↔ YAML ↔ SQLite);
                              read_registry (pure read) vs load_registry (write-path)
    preflight.py           — onboarding discovery (read-only, provenance-stamped)
                              + confirmation — the only curated registry write path
    lifecycle.py           — Phase 5/6 lifecycle contract: setup stage map with
                              done/now/next/blocked/skipped statuses, executor
                              hints, and remediation (backs onboarding_status and
                              the /welcome skill), plus the project-lifecycle
                              ownership table (write semantics per stage —
                              discovery read_only, confirmation gated, inference
                              machine-owned, prioritization read-time overlay)
    local_repos.py         — local checkout discovery (Phase 6.1): scan
                              local_repo_roots for git checkouts, GitHub identity
                              from origin, unpushed-commit counts; feeds
                              provenance=local-scan candidates + the doctor's
                              unpushed-work check
    github_scan.py         — GitHub Events API collector + per-project balance query
    github_knowledge.py    — per-repo artifact sync (issues/PRs/comments/commits/checks) + embedding
    github_watch.py        — watched/external repo reconciliation and repo-watch logic
    github_readiness.py    — release-readiness inference over the local GitHub corpus (read-only)
    github_reconciliation.py — issue ↔ PR close-candidate inference (read-only)
    db/                    — shared DB connection, schema, migrations, sqlite-vec loading
    md_parser.py           — pure markdown parsing (frontmatter, wikilinks, tags, chunking)
    note_ingester.py       — vault walker, delta detection, TF-IDF keywords
    embedder.py            — mlx-embeddings batch embed + ANN query
    semantic_index.py      — unified semantic index: backfill, embed, and query across
                              vault + GitHub + email, plus registry-provider sources
                              such as Figma (semantic_documents / semantic_embeddings)
    index_ops.py           — single entry point for refresh_index() and index_status();
                              orchestrates the full ingest pipeline so agents don't
                              need to know individual CLI command ordering
    calendar.py            — Google Calendar API collector + SQLite persistence
    calendar_config.py     — OAuth token storage, classification rules, review-decision persistence
    calendar_helpers.py    — duration/math utilities consumed by calendar tools
    calendar_snap.py       — edge-snapping logic for slightly overlapping calendar events
    sleuth_reminders.py    — Sleuth Web API collector (Bearer auth, urllib) + upsert
    gmail.py               — Gmail collector / MCP push-ingest write path into email_messages
    figma.py               — Figma comments collector + registry-provider semantic_docs
    ask_self_scan.py       — device-local ask_self index inventory collector
    focus5_scan.py         — Focus 5 repo-signal scan + roster builder
    slack_users.py         — Slack user-id → friendly-name lookup, file-mtime cached;
                              feeds the dashboard sleuth panel and the pulse markdown
    diagnose.py            — repo-level diagnostic that walks the watched-repos +
                              sync funnel for one repo (optionally sha/PR) — backs
                              the diagnose_repo MCP tool
    profile_sync.py        — daily-sync log parser that surfaces per-repo GitHub
                              timings; backs the rebalance profile-sync subcommand
    pulse.py               — pulse markdown renderer; backs publish_pulse MCP tool
    agent_tags.py          — source-tagging for pulse rows (claude-cloud, codex-cloud,
                              lovable, local-vscode, human)
    project_classifier.py  — calendar event → project matcher for timesheet reports
    project_inference.py   — project inference from note titles / calendar summaries
    note_builder.py        — dashboard markdown renderer / write-back for the vault note
    audit.py               — structured audit logging (append_audit_entry)
    querier.py             — multi-source context gathering + local LLM synthesis

scripts/                   — Operator entry points (not part of the importable package)
  dashboard.py             — Rich Live terminal dashboard (mode 4 above)
  pulse_web.py             — render module: regenerates web/pulse.html (the local
                              browser mirror of the dashboard) from the same SQLite
                              knowledge base; atomic via tmp+replace; supports --watch
  _bootstrap.py            — single sys.path shim for directly-run scripts (src/ + scripts/)
  lib/scheduler_common.sh  — shared launchd job runtime: env bootstrap, dated logs,
                              job-lifecycle events, retention (sourced by *_sync.sh)
  lib/install_common.sh    — shared installer flow: always-unload, render template,
                              plutil -lint, load, poll-verify (sourced by install_*.sh)
  daily_sync.sh            — daily_sync launchd entry (mode 2)
  vault_sync.sh            — hourly vault-only launchd entry (mode 2)
  pulse_sync.sh            — hourly pulse-publish (markdown→private repo) launchd entry (mode 2)
  pulse_web_sync.sh        — 30-minute pulse-web (web/pulse.html) launchd entry (mode 2)
  github_sync.sh           — github-only launchd entry (mode 2)
  install_*.sh             — one installer per launchd job (see SCHEDULER.md for the
                              job ↔ installer table; all delegate to lib/install_common.sh)
  setup_calendar_oauth.py  — interactive OAuth consent flow for Google Calendar
  build_extension.py       — native extension builder
  ask-self-ingest.sh       — self-ingest shell wrapper (portable mode, requires ASK_SELF_PATH)
  ask-self-query.sh        — self-query shell wrapper (portable mode, requires ASK_SELF_PATH)
  audit_modules.py         — repository hygiene audit (Approach A): verifies ingest
                              collectors / render modules / scheduled-job infrastructure
                              are documented in ARCHITECTURE.md + CHANGELOG.md; supports a
                              baseline lockfile (audit_modules.lock), recent-commit coverage
                              against the live CHANGELOG version section, and a pre-commit
                              working-tree preview (--include-uncommitted). JSON output for
                              orchestrating agents; also exposed as the audit_modules MCP tool
```

---

## License

Copyright 2025-2026 Hypercart DBA Neochrome, Inc.

rebalance is dual-licensed, matching the rest of the HiQS suite. **AGPL-3.0-only** is the
default and covers nearly every use — see [`LICENSE`](LICENSE). A commercial license is
available for use that AGPL-3.0 does not fit; see [`LICENSE-COMMERCIAL.md`](LICENSE-COMMERCIAL.md).


## Opt-in fleet Pulse delivery (GH-282)

Rebalance producers → device-owned files/exact local commits → existing Git Pulse collector →
private Git remote → each Mac's checkout/SQLite replica → combined human-readable views.
No Mac is a permanent hub. `git_ops.fleet_settings` validates the configured collector identity,
checkout and sync subdirectory. Generated live pulse, daily synthesis and digests use
`devices/<id>/`; calendar/email keep `sync/<source>/<id>.json`. Historical shared files are retained
for rollback and no longer written in fleet mode. `read_latest_snapshot` chooses validated payloads
on read; `pulse.fleet_view` derives delivered pages and is returned by fleet publishing through the
existing CLI/MCP result. These are readers of existing data, not new stores or writer daemons.

CLIO's capture UUID is independent of the friendly collector ID. Its canonical helper exports only
its owner snapshot to `devices/<UUID>/clio.jsonl`; the collector validates it before atomic publication.
Reconcile imports committed blobs into private SQLite without re-exporting foreign origins. Existing
semantic indexing, publishers and readonly XYZ ledger integrations retain their contracts. The same
Obsidian filename/header and five-minute renderer remain, backed by full history on every installed
Mac. Live fleet qualification remains tracked in the canonical GH-282 plan.
     1	{
     2	  "mcpb_version": "0.1",
     3	  "name": "rebalance-os",
     4	  "display_name": "rebalance OS",
     5	  "version": "0.98.1",
     6	  "description": "Your workday OS \u2014 surfaces what matters, flags project imbalances, and answers questions about your own work using your Obsidian vault, GitHub activity, and Google Calendar. All local, all on your data.",
     7	  "long_description": "rebalance OS ingests your Obsidian vault, GitHub activity, and Google Calendar into a local SQLite database, then lets you ask natural language questions about your own work. It flags over-investment in low-priority projects, surfaces neglected high-priority work, and assembles context for meetings \u2014 all running locally on Apple Silicon via MLX.",
     8	  "author": {
     9	    "name": "Hypercart DBA Neochrome, Inc."
    10	  },
    11	  "repository": {
    12	    "type": "git",
    13	    "url": "https://github.com/HiQS-Labs/rebalanceOS"
    14	  },
    15	  "documentation": "https://github.com/HiQS-Labs/rebalanceOS/blob/main/README.md",
    16	  "server": {
    17	    "type": "python",
    18	    "entry_point": "server/mcp_server.py",
    19	    "mcp_config": {
    20	      "command": "python",
    21	      "args": [
    22	        "${__dirname}/server/mcp_server.py"
    23	      ],
    24	      "env": {
    25	        "REBALANCE_DB": "${user_config.database_path}",
    26	        "REBALANCE_VAULT": "${user_config.vault_path}"
    27	      },
    28	      "platforms": {
    29	        "win32": {
    30	          "command": "python.exe"
    31	        }
    32	      }
    33	    }
    34	  },
    35	  "user_config": {
    36	    "vault_path": {
    37	      "type": "directory",
    38	      "title": "Obsidian Vault Path",
    39	      "description": "The folder where your Obsidian vault lives (contains your .md files)",
    40	      "required": true
    41	    },
    42	    "database_path": {
    43	      "type": "string",
    44	      "title": "Database Path",
    45	      "description": "Where to store the rebalance SQLite database. Leave blank to use the platform default resolved by rebalance.paths (macOS: ~/Library/Application Support/rebalance-os/rebalance.db).",
    46	      "default": "${HOME}/Library/Application Support/rebalance-os/rebalance.db"
    47	    },
    48	    "github_token": {
    49	      "type": "string",
    50	      "title": "GitHub Personal Access Token",
    51	      "description": "A GitHub PAT with repo:read scope. Create one at github.com/settings/tokens",
    52	      "sensitive": true,
    53	      "required": false
    54	    }
    55	  },
    56	  "tools": [
    57	    {
    58	      "name": "ask",
    59	      "description": "General-purpose natural language query across all data sources"
    60	    },
    61	    {
    62	      "name": "search_vault",
    63	      "description": "Full-text keyword search over vault files via TF-IDF index"
    64	    },
    65	    {
    66	      "name": "semantic_query",
    67	      "description": "Vector search across the unified semantic index (vault chunks + GitHub corpus)"
    68	    },
    69	    {
    70	      "name": "get_next_actions",
    71	      "description": "Read the latest persisted 'what should we work on next' ranking without recomputing it"
    72	    },
    73	    {
    74	      "name": "list_projects",
    75	      "description": "List projects from the local project_registry table"
    76	    },
    77	    {
    78	      "name": "hiqs_work_activity",
    79	      "description": "Show HiQS work activity (commit/PR/issue) balance across active projects"
    80	    },
    81	    {
    82	      "name": "github_balance",
    83	      "description": "Deprecated alias of hiqs_work_activity; identical behavior"
    84	    },
    85	    {
    86	      "name": "github_release_readiness",
    87	      "description": "Infer current milestone/release readiness from the local GitHub corpus"
    88	    },
    89	    {
    90	      "name": "github_close_candidates",
    91	      "description": "Suggest open issues that likely map to merged PRs and may be ready to close"
    92	    },
    93	    {
    94	      "name": "diagnose_repo",
    95	      "description": "Walk the watched-repos + sync funnel for a single GitHub repo"
    96	    },
    97	    {
    98	      "name": "list_watched_repos",
    99	      "description": "Show which GitHub repos are currently being monitored, and where each came from"
   100	    },
   101	    {
   102	      "name": "list_ask_self_repos",
   103	      "description": "Inventory every repo on this device that has an ask_self RAG index"
   104	    },
   105	    {
   106	      "name": "index_status",
   107	      "description": "Snapshot the SQLite knowledge base: per-source counts and last-synced times"
   108	    },
   109	    {
   110	      "name": "refresh_index",
   111	      "description": "Orchestrated refresh of the local knowledge base"
   112	    },
   113	    {
   114	      "name": "peek_source",
   115	      "description": "Read the most-recent raw rows from one ingest source table (allowlisted, read-only)"
   116	    },
   117	    {
   118	      "name": "publish_pulse",
   119	      "description": "Render today's + yesterday's activity into a markdown status page"
   120	    },
   121	    {
   122	      "name": "audit_modules",
   123	      "description": "Audit ingest collectors, render modules, and scheduled-job infrastructure"
   124	    },
   125	    {
   126	      "name": "create_calendar_event",
   127	      "description": "Create a Google Calendar event using the local OAuth token"
   128	    },
   129	    {
   130	      "name": "review_timesheet",
   131	      "description": "Return unclassified calendar events for a given date that need review"
   132	    },
   133	    {
   134	      "name": "classify_event",
   135	      "description": "Persist a classification decision for an unmatched calendar event"
   136	    },
   137	    {
   138	      "name": "snap_calendar_edges",
   139	      "description": "Report slightly overlapping calendar events and a clean boundary"
   140	    },
   141	    {
   142	      "name": "ingest_gmail_messages",
   143	      "description": "Ingest pre-fetched Gmail messages into the local email_messages table"
   144	    },
   145	    {
   146	      "name": "sleuth_sync_reminders",
   147	      "description": "Pull Slack reminders from the Sleuth Web API and upsert them into SQLite"
   148	    },
   149	    {
   150	      "name": "onboarding_status",
   151	      "description": "Report the full setup lifecycle: every stage and what remains"
   152	    },
   153	    {
   154	      "name": "skip_onboarding_stage",
   155	      "description": "Mark (or unmark) an optional setup stage as deliberately skipped"
   156	    },
   157	    {
   158	      "name": "setup_github_token",
   159	      "description": "Validate a GitHub PAT against the /user endpoint and store it"
   160	    },
   161	    {
   162	      "name": "run_preflight",
   163	      "description": "Discover project candidates from vault note titles and GitHub"
   164	    },
   165	    {
   166	      "name": "confirm_projects",
   167	      "description": "Write confirmed projects to the canonical registry and run pull"
   168	    }
   169	  ],
   170	  "compatibility": {
   171	    "platforms": [
   172	      "darwin"
   173	    ],
   174	    "runtimes": {
   175	      "python": ">=3.12"
   176	    }
   177	  }
   178	}
     1	"""GH-316: `hiqs_work_activity` is canonical; `github_balance` stays as a deprecated alias.
     2	
     3	Both MCP tool names must resolve through the real FastMCP server and return
     4	identical, fully-populated rows — and the frozen output contract (all nine
     5	keys) must not drift while the naming changes.
     6	"""
     7	
     8	from __future__ import annotations
     9	
    10	import asyncio
    11	import json
    12	import tempfile
    13	import unittest
    14	from datetime import date, timedelta
    15	from pathlib import Path
    16	
    17	from rebalance.ingest.db import (
    18	    db_connection,
    19	    ensure_github_schema,
    20	    ensure_project_schema,
    21	    ensure_schema,
    22	)
    23	from rebalance.ingest.github_scan import get_github_balance, get_hiqs_work_activity
    24	from rebalance.mcp.server import create_server
    25	
    26	FROZEN_OUTPUT_KEYS = {
    27	    "project_name",
    28	    "repos_linked",
    29	    "repos_touched",
    30	    "total_commits",
    31	    "prs_opened",
    32	    "prs_merged",
    33	    "issues_opened",
    34	    "last_active_at",
    35	    "is_idle",
    36	}
    37	
    38	
    39	def _call(server, name: str, args: dict):
    40	    """Invoke an MCP tool; FastMCP emits one JSON text block per list item."""
    41	    content, _ = asyncio.run(server.call_tool(name, args))
    42	    return [json.loads(block.text) for block in content]
    43	
    44	
    45	class HiqsWorkActivityAliasTests(unittest.TestCase):
    46	    def setUp(self) -> None:
    47	        self._tmp = tempfile.TemporaryDirectory()
    48	        self.addCleanup(self._tmp.cleanup)
    49	        self.db = Path(self._tmp.name) / "rebalance.db"
    50	        with db_connection(self.db, ensure_schema) as conn:
    51	            ensure_project_schema(conn)
    52	            ensure_github_schema(conn)
    53	            conn.execute(
    54	                "INSERT INTO project_registry (name, status, repos_json, tags_json, custom_fields_json)"
    55	                " VALUES ('Alpha', 'active', '[\"a/one\"]', '[]', '{}')"
    56	            )
    57	            recent = (date.today() - timedelta(days=1)).isoformat()
    58	            conn.execute(
    59	                "INSERT INTO github_activity (login, repo_full_name, scan_date, commits, pushes,"
    60	                " prs_opened, prs_merged, issues_opened, issue_comments, reviews, last_active_at, scanned_at)"
    61	                " VALUES (?, 'a/one', ?, 7, 2, 3, 1, 0, 0, 0, ? || 'T12:00:00Z', ? || 'T12:00:00Z')",
    62	                (f"me@{recent}", recent, recent, recent),
    63	            )
    64	            conn.commit()
    65	
    66	    def test_python_alias_is_the_canonical_function(self) -> None:
    67	        self.assertIs(get_github_balance, get_hiqs_work_activity)
    68	
    69	    def test_both_mcp_tool_names_return_identical_populated_rows(self) -> None:
    70	        server = create_server(self.db)
    71	        canonical = _call(server, "hiqs_work_activity", {"since_days": 30})
    72	        alias = _call(server, "github_balance", {"since_days": 30})
    73	        self.assertEqual(canonical, alias)
    74	        self.assertEqual(len(canonical), 1)
    75	        row = canonical[0]
    76	        self.assertEqual(set(row), FROZEN_OUTPUT_KEYS)
    77	        self.assertEqual(row["project_name"], "Alpha")
    78	        self.assertEqual(row["total_commits"], 7)
    79	        self.assertEqual(row["prs_merged"], 1)
    80	        self.assertFalse(row["is_idle"])
    81	        self.assertEqual(row["repos_touched"], ["a/one"])
    82	
    83	
    84	if __name__ == "__main__":
    85	    unittest.main()
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md
TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md
TESTS-RESULTS/2026-10-03+GH-316/SUMMARY.md

exec
/bin/zsh -lc "nl -ba TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md | head -25; tail -5 TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md; nl -ba TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md | head -25; tail -5 TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md; nl -ba TESTS-RESULTS/2026-10-03+GH-316/SUMMARY.md; rg -n '"'````|/private/|/var/|worktree'"' TESTS-RESULTS/2026-10-03+GH-316/qa" in /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-52169-cm4lvxp9
 succeeded in 0ms:
     1	# GH-316 plan consult — round 1 (verbatim)
     2	
     3	Codex gpt-6-astra via relay-automation/consult.sh, read-only worktree, 2026-10-03.
     4	Verdict: CHANGES — approve after the small plan corrections (all accepted; see the QA log
     5	in PROJECT/2-WORKING/GH-316-HIQS-WORK-ACTIVITY-NAMING.md). Transcript fenced verbatim:
     6	its relative links belong to the advisor's throwaway worktree and must not be repointed
     7	(GH-88 rationale).
     8	
     9	## Prompt
    10	
    11	````
    12	# Plan review request — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter
    13	
    14	You are reviewing a PLAN (pre-implementation) for a small, operator-directed naming change in the rebalanceOS repo. Grade against the stated requirements and commensurate complexity — this is a labels-and-aliases change, not a schema migration; do not demand enterprise machinery.
    15	````
    16	
    17	## Advisor output
    18	
    19	````
    20	**NO FIRSTHAND VERIFICATION CITED** — treat conclusions as conditional (codex's answer carries an unsupported [Pass]/verified/confirmed-style claim with no quoted span or file:line citation nearby, despite the consult PREAMBLE asking advisors to cite evidence.)
    21	
    22	> **ATTESTATION**
    23	> Model: gpt-6-astra
    24	> Provider: openai
    25	> Sandbox: read-only
=== CONSULT QUESTION ===
# Plan review request — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter

You are reviewing a PLAN (pre-implementation) for a small, operator-directed naming change in the rebalanceOS repo. Grade against the stated requirements and commensurate complexity — this is a labels-and-aliases change, not a schema migration; do not demand enterprise machinery.
````
     1	# GH-316 final consult (verbatim)
     2	
     3	Codex review of HEAD 61c431f, 2026-10-03. Verdict: CHANGES with two small omissions
     4	(manifest tool metadata; date-sensitive parity fixture) — fixed in the follow-up commit.
     5	Transcript fenced verbatim (GH-88 rationale).
     6	
     7	## Prompt
     8	
     9	````
    10	# FINAL implementation review — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter
    11	
    12	You are reviewing the COMMITTED implementation on branch `feat/hiqs-work-activity-naming` (HEAD). This is the final QA after plan round 1 (CHANGES) whose corrections were accepted. Grade against the stated requirements and commensurate complexity — labels-and-aliases change; do not demand enterprise machinery.
    13	````
    14	
    15	## Advisor output
    16	
    17	````
    18	**NO FIRSTHAND VERIFICATION CITED** — treat conclusions as conditional (codex's answer carries an unsupported [Pass]/verified/confirmed-style claim with no quoted span or file:line citation nearby, despite the consult PREAMBLE asking advisors to cite evidence.)
    19	
    20	> **ATTESTATION**
    21	> Model: gpt-6-astra
    22	> Provider: openai
    23	> Sandbox: read-only
    24	
    25	Reading additional input from stdin...
=== CONSULT QUESTION ===
# FINAL implementation review — GH-316: "HiQS work activity" naming with a backwards-compatibility adapter

You are reviewing the COMMITTED implementation on branch `feat/hiqs-work-activity-naming` (HEAD). This is the final QA after plan round 1 (CHANGES) whose corrections were accepted. Grade against the stated requirements and commensurate complexity — labels-and-aliases change; do not demand enterprise machinery.
````
     1	# GH-316 — QA evidence
     2	
     3	Not a measurement campaign: this folder retains the plan-consult transcript
     4	(qa/plan-consult-r1.md, verbatim, fenced) for the naming/adapter change.
     5	Verdict and per-finding dispositions live in the working doc's QA log.
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:3:Codex gpt-6-astra via relay-automation/consult.sh, read-only worktree, 2026-10-03.
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:6:its relative links belong to the advisor's throwaway worktree and must not be repointed
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:11:````
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:15:````
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:19:````
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:30:workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-94700-mqndjfe3
TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:46:````
TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md:9:````
TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md:13:````
TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md:17:````
TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md:28:workdir: /private/var/folders/69/3l_82qtj7fzglnt_jjg07jh40000gn/T/consult-wt-20842-3h6lhlfy
TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md:44:````

codex
**ANSWER: APPROVE** — HEAD `d3ccc2f` satisfies both round-2 conditions.

- **[Pass] Manifest metadata:** `hiqs_work_activity` has the exact canonical description; `github_balance` explicitly remains a deprecated alias with identical behavior (`manifest.json:78–83`).
- **[Pass] Date-sensitive fixture:** yesterday’s date is computed dynamically and supplied through SQL parameters (`tests/test_hiqs_work_activity_alias.py:57–62`). The 30-day calls retain populated, nonzero assertions (`tests/test_hiqs_work_activity_alias.py:71–81`).
- **[Pass] Transcript packaging:** both transcripts reside under the requested campaign’s `qa/` directory, with four-backtick fences enclosing their original worktree references (`TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:19–46`; `TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md:17–44`).

The 15 passing tests and clean ruff/mypy results are supplied evidence; I did not independently rerun them.

**RECOMMENDATION:** Approve GH-316; no further changes required within this confirmation scope.
tokens used
35,697
**ANSWER: APPROVE** — HEAD `d3ccc2f` satisfies both round-2 conditions.

- **[Pass] Manifest metadata:** `hiqs_work_activity` has the exact canonical description; `github_balance` explicitly remains a deprecated alias with identical behavior (`manifest.json:78–83`).
- **[Pass] Date-sensitive fixture:** yesterday’s date is computed dynamically and supplied through SQL parameters (`tests/test_hiqs_work_activity_alias.py:57–62`). The 30-day calls retain populated, nonzero assertions (`tests/test_hiqs_work_activity_alias.py:71–81`).
- **[Pass] Transcript packaging:** both transcripts reside under the requested campaign’s `qa/` directory, with four-backtick fences enclosing their original worktree references (`TESTS-RESULTS/2026-10-03+GH-316/qa/plan-consult-r1.md:19–46`; `TESTS-RESULTS/2026-10-03+GH-316/qa/final-consult.md:17–44`).

The 15 passing tests and clean ruff/mypy results are supplied evidence; I did not independently rerun them.

**RECOMMENDATION:** Approve GH-316; no further changes required within this confirmation scope.

````
