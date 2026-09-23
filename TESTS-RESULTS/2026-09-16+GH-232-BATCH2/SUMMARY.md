# Separate clear fixes and conservative reference handling

Formatting/chat-ID fix committed independently at 3b2b6fb: five synthetic cases failed before
the fix; 47 focused tests passed afterward. Explicitly typed large issue IDs remain valid.
An optional --explicit-links-only replay uses typed qualified GitHub URLs as join keys.
Other recognized mentions remain under unresolved_refs with no assigned repository; their kind
is only a hint. They cannot group tasks or attach lifecycle events. Legacy context mode remains
available for comparison and still has its documented ambiguity limitations.

Current focused suite: 50 passed, including a deliberate wrong join that demonstrates the event
exclusion check constrains behavior. The same frozen source/window, all prompt/start identities
and child journey memberships were checked against GH-230 replay-1. Counts: 288 prompts, nine
journeys, 212 unassigned, 21 explicit URL-reference occurrences, 71 unresolved candidates.
These are extraction/coverage counts, not accuracy. The live index supplies zero target events.

Retained GitHub snapshots and explicit prompt URLs support three assistant-reviewed issue histories:
#508 → PR #535, #568 → PR #581, #623 → PR #640. outcomes.jsonl records public artifact event
timestamps and retrieval time; private prompt references are retained only in the ignored preview.
All three PRs explicitly close the respective issue. #508's verdict was subsequently superseded
by #536; its closure does not represent fulfillment of the changing overall goal. Deployment unknown.
This is a source-linked assistant preview, not a new automated snapshot ingestion adapter.

The extended eight-step plan tracks evidence coverage, explicit-case reconstruction, task transition
trial, current review and publication. Broader inference and human usefulness remain outstanding.
Full application gates remain dependency-blocked as documented in the prior campaign. Current
implementation has no new independent approval; PR #231 stays draft. No model synthesis call.

Threats: one frozen week/device, assistant diagnostic inspection, no human labels or blinded holdout.
Explicit-links mode intentionally reduces linking coverage. Bare shorthand lacks an authoritative
artifact type and stays unresolved. This mode does not resolve project nicknames or prove causation.
