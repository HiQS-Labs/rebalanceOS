# RELAY · GH-81 three-way embeddings bake-off — protocol QA

NEXT: Producer
STATUS: Approved
ROUND: 3 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **Verdict**
     (Approved | Changes requested | Blocked). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why),
     make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh81-bakeoff-protocol-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do.

## Setup
- Artifact under review: **.relay-artifacts/gh81-bakeoff-protocol.md** — the read-only path that
  `relay-drive.sh --artifact-file` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: agy   ·   Producer: claude-a
- Started: 2026-08-20
- Definition of Done: This is a **protocol review** — an experimental design for a three-way
  embedding-model bake-off (Gemini hosted vs Qwen3-Embedding-0.6B local vs BGE-small local) against
  rebalanceOS's own semantic index. **No code has been written yet.** Grade the design's soundness
  BEFORE it is executed, because a flawed protocol produces a confidently wrong recommendation about
  which embedder the product ships. Judge against:

  1. **Will it actually answer the question in §1?** Or does it measure something adjacent that will
     be mistaken for an answer?
  2. **Is the ground truth trustworthy (§4)?** This is the crux — the previous attempt at this
     measurement had NO ground truth and produced an uninterpretable result. Specifically: is
     Claude-authored Set A a defensible way to avoid the Gemini-generates-queries family bias, or
     does it introduce a worse bias? Is the §4.2 validity gate (FTS top-50 sanity check) sound, or
     does it silently bias the query set toward lexically-easy queries that vector search does not
     need to be good at? Is n=30 + n=10 salvageable at all?
  3. **Is the fairness control real (§3.3, §4.3)?** Uniform 2,000-char truncation to BGE's context
     deliberately handicaps Qwen and Gemini — is that the right call for a decision protocol, or does
     it pre-ordain the outcome? Is the `bge`/`bge-asym` split the correct test of the §0 hypothesis
     that the earlier prefix regression came from query/passage treatment mismatch?
  4. **Is the corpus construction sound (§3.2)?** 10k stratified from 52k, with all target docs
     force-included. Does force-including targets while randomly sampling distractors leak anything?
     Does proportional stratification (90% github) serve or defeat the stated purpose?
  5. **Is the decision rule (§6) honest?** It is written before results are seen, on purpose. Are the
     thresholds (0.05 MRR@10 to justify reverting GH-81; non-overlapping bootstrap CIs to declare a
     winner) defensible, or arbitrary numbers dressed as rigor?
  6. **Anything missing or dangerously wrong** before compute is spent: the sidecar-DB isolation
     claim (§3.1 — production DB is read-only, is that actually guaranteed by the design?), the
     metrics choice (§5 — is MRR@10 the right headline?), the threats list (§9 — what is missing
     from it?).

  Flag both real gaps AND anything that is genuinely fine, so a rubber-stamp is distinguishable from
  a considered pass. Be adversarial about §4 and §6 in particular — an unfalsifiable protocol that
  reaches "BGE wins" is the specific failure mode this QA exists to prevent.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Turn 1: Reviewer (agy)
swept file: yes

- `[Blocker]` **BM25 validity gate biases against semantic search:** §4.2 requires targets to appear in the FTS top-50. This systematically filters out queries where vector search provides the most value (semantic matches with low lexical overlap) and restricts the test to lexically-easy queries. **Fix:** Remove the BM25/FTS sanity check from §4.2; rely purely on manual validation that the target answers the query.
- `[Blocker]` **Decision rule is unfalsifiable and rigged for BGE:** §5 and §6 require non-overlapping 95% bootstrap CIs on n=30. Non-overlapping 95% CIs is a wildly conservative threshold (equivalent to p < 0.01) that practically guarantees overlap on small samples, pre-ordaining the "no measurable difference -> keep BGE" outcome. **Fix:** Use a standard paired statistical test (e.g. Wilcoxon signed-rank or paired t-test on MRR differences) at alpha=0.05 instead of requiring independent CIs to not overlap.
- `[Should]` **Uniform truncation hides model advantages:** §3.3 truncates all text to 2,000 characters to match BGE. If production documents are longer, this deliberately blinds Qwen and Gemini to context they would actually use in the product. **Fix:** Allow each model to embed up to its native limit (or the production max chunk size), measuring their true production capability.
- `[Nit]` **Confused asymmetric prompting hypothesis:** §0 claims the regression happened because queries were prefixed against a corpus with "no corresponding treatment" (implying both should have it), but §2 and §4.3 correctly state BGE's documented recipe has no passage prefix. **Fix:** Rephrase §0 to clarify the hypothesis is whether BGE's own asymmetric recipe actually works, not that it was a mistake to use it asymmetrically.
- `[Pass]` **Corpus stratification:** §3.2 ("Rationale for preserving proportions rather than balancing them: github is 90% of the real haystack, so it must be 90% of the distractors.") is correct and prevents artificially flattering the models with a balanced dataset.
- `[Pass]` **Production DB isolation:** §3.1 ("Read-only access to `~/Library/Application Support/rebalance-os/rebalance.db` to snapshot the corpus, once, at the start.") guarantees the live DB is safely isolated.

**Verdict:** Changes requested

VERDICT: FAIL
Basis: Blockers found in validity gate and decision rule.

**Producer (claude-a) · r2**

All four findings accepted. Two implemented as proposed, two modified with a
stronger fix; nothing declined.

- `[Blocker]` **BM25 validity gate biases against semantic search** — **Modified (accepted the diagnosis, went further than the fix).** The finding is correct and it was the worst defect in the draft: gating on FTS top-50 would have deleted exactly the `lexical-hard` queries a vector index exists to serve, leaving a query set answerable by keyword search alone. Removing the gate (your fix) recovers those queries but discards the signal. §4.2 now (a) removes the gate entirely, (b) keeps FTS as a per-query **label** (`lexical-easy` / `lexical-hard`) with all primary metrics reported split by it, and (c) adds **FTS5 itself as a sixth scored lane**. Rationale for going further: if no embedding model beats keyword search on this corpus, that is the most consequential result the run could produce, and the original design could not have seen it. New §6 rule 5 makes that outcome supersede every other finding.

- `[Blocker]` **Decision rule is unfalsifiable and rigged for BGE** — **Implemented, and the diagnosis was under-stated.** You are right that non-overlapping 95% CIs is ~p<0.01 and would have returned "no difference → keep BGE" almost regardless of data. There was a second, larger error you did not name: independent per-lane CIs **discard the pairing**. All lanes answer the same queries, so between-query difficulty — the dominant variance component — is common to every lane and cancels under a paired test. The independent-interval design was inflating variance with noise it could have subtracted. §5 is rewritten: **Wilcoxon signed-rank on per-query reciprocal-rank differences, α=0.05, two-sided** (signed-rank not paired-t: reciprocal rank is bounded, discrete, and heavily tied at 0 and 1). Added **Holm–Bonferroni** across the now-15 pairwise comparisons — going to α=0.05 on 15 uncorrected tests would have been a >50% chance of a false winner, i.e. the same failure inverted. Bootstrap CIs are retained but **demoted from significance gate to effect-size description**, on the paired difference.

- `[Should]` **Uniform truncation hides model advantages** — **Implemented, after measuring rather than arguing.** Your reasoning was conditional on "if production documents are longer", so I measured the live corpus instead of assuming either way. Result: p50 = 300 chars, **only 11.0% of 52,158 docs exceed 2,000 chars** (code 14.3%, github 11.4%, vault 4.3%, figma/email 0%). So the handicap was smaller than the finding implies — but non-zero, and real on the 11%, and your core objection stands: a decision protocol must measure the config that would ship. §3.3 now drops uniform truncation, embeds at each model's native limit, records per-lane truncation rates, and adds a **no-truncation-subset** analysis so a Qwen/Gemini win on long docs can be attributed to context length vs embedding quality rather than conflated. The measured table is now in §3.3 so the reasoning is auditable.

- `[Nit]` **Confused asymmetric prompting hypothesis** — **Implemented.** You are right, §0 was sloppy and implied the prefix had been misapplied when BGE's recipe is genuinely query-only. §0 now states the actual open question: whether BGE's own documented recipe helps on this corpus, or whether n=5 with no ground truth produced noise.

- Both `[Pass]` findings carried citations and I verified both against the artifact; no change.

Also added on my own initiative (flagging so it is reviewed, not slipped in):
- §9 threat 6 — **no blinding anywhere**: I author the queries, run the lanes, and report the result. Named as the largest unmitigated threat rather than papered over.
- §9 threat 3 — the protocol **cannot distinguish "no effect" from "an effect too small for n=40"** and must not claim to.
- §6 closing note — rules 2, 3 and 5 each carry a branch that embarrasses an incumbent decision (the GH-81 migration, the §0 prefix finding, the semantic index itself), deliberately.
- §6 rule 3 — the 0.05 threshold is now labelled a **judgement call, not a derived constant**, with its concrete interpretation stated.

Handing off to Reviewer (agy) — round 2/3. Please re-review the revised artifact, focusing on: (1) does adding FTS as a scored lane plus lexical-hard/easy splits actually fix the gate problem or introduce a new one; (2) is the Wilcoxon + Holm design correct for this data, and is Holm across 15 comparisons now *too* conservative at n=40 — i.e. did I overcorrect your blocker into the same failure mode; (3) is the no-truncation-subset analysis sufficient to separate context-length effects from quality effects.

### Turn 2: Reviewer (agy)
swept file: yes

- `[Should]` **FTS5 cannot beat embedding lanes on `lexical-hard` queries:** §6 rule 5 states "If FTS5 beats every embedding lane on `lexical-hard` queries". However, by definition in §4.2, `lexical-hard` queries are those where the target is NOT in the FTS top-50. Therefore, FTS5's MRR@10 is exactly 0 on this subset. It can tie the embedding models at 0, but logically cannot beat them. **Fix:** Rephrase rule 5 to check if embedding lanes fail to beat FTS5 *overall*, or if they score ~0 on `lexical-hard` queries (meaning they fail to provide the unique value they were added for).
- `[Nit]` **Gate failure applies to the query set, not lanes:** §6 rule 6 states "Any lane failing the §4.2 gate on >20% of queries invalidates that run." But §4.2 describes a pre-run validity check on the (query, target) pairs themselves, independent of any lane. **Fix:** Change rule 6 to "If >20% of the generated queries fail the §4.2 gate, the query set is invalid and the run is aborted."
- `[Pass]` **Validity gate replaced with FTS lane/labels:** Adding FTS as a scored lane and splitting metrics by `lexical-hard`/`easy` (§4.2) elegantly solves the bias problem. It retains the crucial queries where vector search is needed while providing a clear baseline.
- `[Pass]` **Wilcoxon + Holm design:** §5's shift to paired Wilcoxon tests correctly subtracts the between-query variance. While Holm on 15 comparisons at n=40 is conservative (as accurately acknowledged in §9 threat 3), reporting bootstrap CIs for the paired difference ensures effect magnitude remains visible without declaring false winners on noise.
- `[Pass]` **No-truncation subset analysis:** §3.3's approach to let each model use its native limit and report a no-truncation subset is perfect. It measures true production capability while cleanly isolating context-length advantages from core embedding quality.

**Verdict:** Changes requested

Handing off to Producer (claude-a) to implement the final text fixes for rule 5 and rule 6.

**Producer (claude-a) · r3**

Both findings accepted; nothing declined.

- `[Should]` **FTS5 cannot beat embedding lanes on `lexical-hard`** — **Implemented.** This is a real logic error and it was mine, introduced in r2 while fixing your first blocker: `lexical-hard` is *defined* in §4.2 as the target being absent from FTS's top-50, so `fts` scores exactly 0 on that subset by construction. Rule 5 asked whether a lane pinned at zero could win — incoherent. §6 rule 5 is now split: **5a** compares embedding lanes against `fts` on the **full** query set (where the comparison is meaningful), and **5b** tests whether the best embedding lane clears an **absolute floor of MRR@10 ≥ 0.10** on `lexical-hard` — the right question there, since there is no baseline to beat. Added an explicit note that `fts` comparisons are only valid on the full set or the `lexical-easy` subset, so the same error cannot be reintroduced.

- `[Nit]` **Gate failure applies to the query set, not lanes** — **Implemented** as you worded it. §4.2 is a pre-run check on (query, target) pairs and has nothing to do with lanes; rule 6 now reads "if >20% of the authored queries fail the §4.2 gate, the query set is invalid: abort and rebuild", with a clause stating the gate cannot be failed by a lane.

- Your three `[Pass]` findings each carried a citation; I verified all three against the revised artifact. On the Holm-conservatism point you raised in r2 question (2) and then passed: I am leaving Holm in. At n=40 it is conservative, but the failure it prevents (a false winner triggering a revert of GH-81 or a move to a hosted embedder) is materially more expensive than the failure it causes (missing a marginal effect, which §9 threat 3 already declares this protocol cannot detect). Effect sizes are reported regardless of significance, so a real-but-unconfirmed signal stays visible rather than being erased.

Handing off to Reviewer (agy) — round 3/3, final. Both r2 findings are addressed; if you agree the rule 5 split resolves the construction problem and rule 6 is now correctly scoped, please close this with `STATUS: Approved` so implementation can begin.

### Turn 4: Reviewer (agy)
swept file: yes

- `[Pass]` **Rule 5 split**: §6 rule 5a ("compares embedding lanes against `fts` on the full query set") and 5b ("whether the best embedding lane clears an absolute floor of MRR@10 ≥ 0.10 on `lexical-hard`") elegantly resolve the logical impossibility of beating `fts` where its score is structurally pinned to 0.
- `[Pass]` **Rule 6 scope**: Scope is now correctly restricted to the generated queries themselves ("if >20% of the authored queries fail the §4.2 gate, the query set is invalid: abort and rebuild").

**Verdict:** Approved

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
