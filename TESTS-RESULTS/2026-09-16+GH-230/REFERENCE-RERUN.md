# Frozen-sample reference rerun

Date: 2026-09-16. Parser revision: `f8a2078`; baseline: original campaign replay.
Same frozen capture and cutoff `2026-09-16T04:25:38Z`. Source manifest, window, prompt identities,
text, timestamps, start decisions and session/device metadata were asserted unchanged.

`reference-rerun.jsonl` contains one non-identifying delta per changed prompt. It totals 24 changed
prompts, 33 added reference tuples and five removed tuples. These are extraction changes, not correct
match counts. Coverage remains 288 prompts, nine journeys, nine parents and 212 unassigned prompts;
the original coverage primitive remains in `measurements.jsonl`.

Spot inspection against the retained private GitHub snapshot confirms the intended issue-reference
and typed-PR examples now parse. However, the same replay exposes wrong-repository assignments when
a prompt discusses another project, and false literal PR IDs from numbered implementation steps.
At least four added associations are wrong across three inspected prompts. This is a lower-bound
finding from partial semantic review, not an exhaustive label set or an accuracy estimate.

No automatic-linking graduation. No model calls, source/index writes, updated task boundaries,
new confirmed-outcome attachment, or parser changes during this evaluation. Detailed private examples
are retained beside the new preview in ignored local scratch. Original results were not overwritten.

Next: synthetic regression cases for the observed cross-project and ordinal ambiguities, then the
smallest abstention guard. Re-run the identical frozen sample after that change; do not promote a
reference solely because its number exists on GitHub.
