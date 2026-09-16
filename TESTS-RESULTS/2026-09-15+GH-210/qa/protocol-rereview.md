# Independent pre-run protocol re-review

Reviewer: `gpt-6-astra` Low via Codex CLI 0.153.4  
Session: `01a0a7fc-3c20-7ba3-a97f-c91ae9eefbda`  
Mode: read-only static review; no comparison arm was run

**CHANGES REQUIRED**

Static review only; no files edited, tests executed, or model arms run.

Prior findings:

- **Ground truth: closed.** Explicit focus precedence addresses I04/B03; predeclared acceptable evidence sets address C01 and causal-chain alternatives.
- **Malformed attempts: partially closed; BLOCKER remains.** Output arrays, non-string states, and malformed evidence IDs are guarded. However, both parsers preserve arbitrary `usage` values, while `score_comparison.py` unconditionally calls `.items()`. An envelope containing `"usage":[1]` or `"usage":"bad"` therefore reaches a checkpointed row but aborts publication—even when its output correctly fails contract validation. Validate usage as an object and retain malformed metadata without aborting scoring. The instrument must exercise parser → runner → scorer handling; its current malformed control constructs a row manually and never tests either parser.
- **Winner eligibility: closed through protocol revision.** Revision 2 explicitly requires both arms eligible for either comparative outcome, matching implementation. This changes the original policy rather than changing the scorer.
- **Schema contract: partially closed; SHOULD remains.** ASCII matching is fixed and duplicate rejection is explicitly a stricter contract check. However, `run_comparison.py` labels any output from exit code zero `provider_schema_valid`, including an array or invalid state. Validate against the supplied schema, or rename this metric to accurately describe provider acceptance.
- **Receipts/input identity: partially closed; SHOULD remains.** Battery/schema hashes are checked and parsed receipts retained. Successful stderr and non-JSON stdout are still discarded; parse failures retain only a tail, and an early Terra parsing exception prevents receipt assignment. No sanitization is implemented. Retain sanitized complete stdout/stderr for every attempt so parsing failures remain auditable.
- **Consistency: closed.** Citation order is normalized, invalid pairs cannot count as agreement, and pairs containing failures are reported separately.

**Additional SHOULD — baseline scoring uses a different citation contract.** `score_comparison.py` compares only canonical `evidence_ids`, ignoring acceptable alternatives used for model arms. For example, V01's baseline cites the permitted terminal evidence but loses strict credit. Use `evidence_correct()` for baseline scoring too.

The runner/scorer cannot yet publish all malformed attempts.
