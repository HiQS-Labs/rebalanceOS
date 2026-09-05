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
