# Three candidate histories: facts versus coverage gaps

Assistant diagnostic inspection only. Saved public GitHub metadata was retrieved at
2026-09-16T14:37:54Z; replay cutoff is 2026-09-16T04:25:38Z. No new API fetch or human
usefulness approval. Private prompt text and identifiers are not reproduced.

| Qualified issue | Prompt mentions | Assigned to a chat journey | Still unassigned |
|---|---:|---:|---:|
| XYZ Forge #508 | 1 | 1 | 0 |
| XYZ Forge #568 | 3 | 1 | 2 |
| XYZ Forge #623 | 3 | 3 | 0 |

Twelve retained events match explicit references anywhere in the eligible prompts; only **eight
unique events attach to the original chat journeys**. Four matching facts therefore do not appear
in those task timelines. These are distinct coverage measures, not confirmed causal connections.
The candidate view has unchanged membership on this sample. More linked facts does not resolve
the 212 unassigned prompts, including two explicit mentions of #568.

The two missing mentions have no earlier detected start in their same-chat eligible window.
One is in a different agent/chat with no detected starts; the other precedes two later starts in
the same chat that eventually has an assigned #568 mention. This is expected conservative grouping,
not a lost qualified reference. It does not establish that no task began before the frozen window.
Backfilling the latter from a later start would introduce lookahead; merging the former would
erase separate attempts. An explicit issue-evidence grouping could show both while keeping their
unassigned status, but that view has not been implemented or validated in this run.

## Candidate stories from public evidence

1. Portable skill projection experiment: [PR #535](https://github.com/HiQS-Labs/XYZ-forge/pull/535)
   was created September 10 at 00:57:51Z and merged at 01:32:30Z;
   [issue #508](https://github.com/HiQS-Labs/XYZ-forge/issues/508) closed at 01:32:31Z.
   Saved PR metadata explicitly names #508 as a closing issue. The earlier success verdict was
   later superseded by [#536](https://github.com/HiQS-Labs/XYZ-forge/issues/536), with follow-up
   [#556](https://github.com/HiQS-Labs/XYZ-forge/issues/556). Closure is not the full evolving goal.
   The strict automated composition attaches the referenced issue's closure; it does not infer
   PR #535 from the issue URL. That chain remains separately inspected evidence.
2. Release-ledger retirement: [#568](https://github.com/HiQS-Labs/XYZ-forge/issues/568) was created
   September 11 at 02:56:41Z. [PR #581](https://github.com/HiQS-Labs/XYZ-forge/pull/581) was created
   September 12 at 09:38:38Z and merged September 13 at 02:57:32Z; #568 closed one second later.
   Saved PR metadata explicitly closes #568. The sample includes explicit URLs for both artifacts,
   but two issue mentions remain outside any chat journey. Do not silently absorb those mentions
   into the assigned attempt or claim complete coverage.
3. More resilient cleanup runs: [#623](https://github.com/HiQS-Labs/XYZ-forge/issues/623) was created
   September 15 at 04:30:57Z. [PR #640](https://github.com/HiQS-Labs/XYZ-forge/pull/640) was created
   at 11:32:46Z and merged at 18:44:25Z; #623 closed at 18:44:27Z. Saved PR metadata explicitly
   closes #623. All three issue mentions are assigned, but the strict replay does not infer the
   PR #640 chain merely from an issue mention.

All three have unknown deployment. PR closing-issue metadata supports delivery relationships,
not proof that a particular chat caused delivery. A merged document's title is not independent
proof of its acceptance claims. No issue creation outside the frozen window is added to its fact set.

## Current implementation review and smallest next move

The conservative implementation passes its bounded checks, but is not yet a complete journey tool:
candidate sections show intent IDs rather than full intent timelines; each event's retrieval time
is in evidence JSON rather than beside the Markdown event; most prompts remain unassigned; issue
references do not automatically import attested PR relationships. Legacy mode is still ambiguous.

Next, inspect the two unassigned #568 mentions to explain the missing start/chat boundaries before
adding a rule. If there is an explicit shared issue identity, offer a separate issue-evidence view
that preserves unassigned status and child attempts; do not relabel them as a single continuous
task. If evidence is insufficient, keep the gap visible. Improve display only where it prevents
usefulness review. No broad semantic detector, new collector or model call is justified by this run.
