# Independent review receipts

Read-only reviewer feedback, with machine paths and fixture output omitted from the public packet.
This is a sub-agent review, not an Agy relay approval or a clean full-application gate.

Initial review: FAIL. Formatted AgentChorus IDs still became issues; qualified URL decimal/suffix
inputs could become a different positive integer artifact. Remediation independently verified PASS.

Transition review: FAIL. Without explicit-links-only, a legacy guessed Catalog PR 8 could carry a
wrong merge into the candidate view. Remediation independently verified PASS:

> All 70 journey tests pass. Independent checks confirm candidate timelines exclude guessed
> Catalog PR8 outcomes even without the explicit-links flag, retain the qualified issue20 outcome,
> preserve original rows/grouping, and abstain when the prior task has only a bare issue number.

Campaign composition review: PASS:

> Synthetic checks verified the seven-day cutoff, repository filtering and artifact-number mismatch
> rejection. The script verifies capture metadata, keeps retrieval time separate from event time,
> and uses the existing private publisher without source, API or database writes.
> Its output supports histories from retained metadata. It does not establish deployment, chat
> causation, exhaustive history or live automatic ingestion.

The producer independently ran 77 combined checks, both transition controls against pre-remediation
e6170d6 (expected red), and a cutoff mutation (expected red). Review acceptance is confined to this
bounded implementation/campaign scope. Missing app dependencies keep the PR draft.
