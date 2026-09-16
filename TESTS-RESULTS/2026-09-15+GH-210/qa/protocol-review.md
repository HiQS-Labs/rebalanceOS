# Independent pre-run protocol review

Reviewer: `gpt-6-astra` Low via Codex CLI 0.153.4  
Session: `01a0a7f8-3f50-7b62-8160-2aac84c5da48`  
Mode: read-only static review; no comparison arm was run

**CHANGES REQUIRED**

Static review only; no files edited or model arms run.

- **BLOCKER — Strict-exact ground truth is underspecified.** `run_comparison.py:40–50` requests the most recent relevant evidence but supplies no priority rule for competing repositories. I04 expects older source edits over a newer documentation commit; B03 similarly selects an older blocker (`battery.json:70–75`, `126–131`). Citation completeness is also ambiguous: C01 requires both checks and merge evidence, although the merge alone establishes completion (`battery.json:142–147`). Reasonable answers can therefore lose the primary metric. Specify focus precedence and citation inclusion rules, or predeclare acceptable evidence sets.

- **BLOCKER — Malformed responses can abort execution instead of becoming failed attempts.** In `run_comparison.py:65`, a list/dict `state` raises `TypeError` during set membership; validation happens outside the exception handler at line 172. A JSON array envelope also raises uncaught `AttributeError` in either parser. Separately, `score_comparison.py:129–140` assumes object output and iterable `evidence_ids`, so malformed rows can prevent publication. Guard types throughout, checkpoint every failure, and add malformed-response controls.

- **BLOCKER — Implemented winner eligibility contradicts the frozen rule.** The protocol requires the winning arm to be eligible; only operational leadership requires both arms eligible. `score_comparison.py:227` requires both for a quality winner too. One opponent safety violation would suppress an otherwise qualifying winner. Align implementation and protocol before inference; test this scenario.

- **SHOULD — “Schema validity” uses a different contract from the supplied schema.** `schema.json:12–14` permits duplicate IDs and restricts digits to ASCII. `run_comparison.py:74–80` rejects duplicates but accepts Unicode digits through `isdigit()`. Because schema validity determines eligibility, use one authoritative validator or explicitly separate schema and semantic checks.

- **SHOULD — Published receipts cannot fully audit parsing or frozen-input identity.** Successful stdout/stderr are discarded (`run_comparison.py:150–166`); the console contains progress summaries. The scorer loads today’s battery without checking recorded hashes (`score_comparison.py:100–114`). Retain safely sanitized raw receipts and reject mismatched input hashes.

- **SHOULD — Consistency can reward failures and penalize equivalent citations.** `score_comparison.py:163–164` counts two missing outputs as consistent, while reversed evidence-ID order counts as inconsistent despite strict scoring treating order as irrelevant. Normalize valid outputs and report paired failures separately.
