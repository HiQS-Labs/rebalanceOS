# GH-300 corrected held-out Luna High trial

## Result

One separately registered, frozen follow-up to [GH-232](https://github.com/HiQS-Labs/rebalanceOS/issues/232) ran on three cases Luna had not seen: XYZ Forge #589, #605 and #567. It used the recovered September 16 CLIO capture and a single September 30 read-only GitHub observation. The [private Git Pulse Sync experiment folder](https://github.com/Hypercart-Dev-Tools/rebalance-git-pulse/tree/f348a780/experiments/gh300-luna-heldout-2026-09-30) holds the matched A/B controls, minimized packets, six unedited Luna outputs, raw run events, blinded review views and independent source audit. The dataset was committed before inference at `84dda605`; outputs and audit landed at `f348a780`. No old-versus-new score comparison was performed.

| Held-out case | Matched packet | Both-repeat factual audit |
|---|---|---|
| #589 | Three qualified prompts in two captured agent attempts; later observed issue closure; no returned native closing PR | Both preserve distinct attempts and uncertain delivery/deployment, with supported citations. |
| #605 → PR #607 | One qualified review prompt; native closing relationship; PR body has older “not merged” wording conflicting with later API merge observation | Both distinguish the stale body from the observed merge, and avoid chat causation/deployment inference. |
| #567 | One qualified prompt plus two bare-number mentions that remain unresolved; later observed closure; no returned native closing PR | Both refuse to attach the bare mentions. **Both omit the `U*` source IDs** when describing details of those messages; the gap ID alone does not support their agent attribution or exact quote. |

All six candidate outputs are under 350 words and all printed `[[ID]]` citations resolve to supplied IDs. The independent manual audit found no fabricated join, unsupported completion/deployment or re-prompt/restart conflation. The two #567 narratives still fail the preregistered requirement that **every material factual claim cite its supporting IDs**. The factual promotion gate therefore **does not pass**, irrespective of later prose preference. No output was edited, retried for quality or rescored. Operator preference for this held-out set is pending.

## Protocol and measured execution

- [Protocol](PROTOCOL.md) and [working plan](../../PROJECT/2-WORKING/GH-300-LUNA-HELDOUT-TRIAL.md) committed before inference at `893ffb6`. Source capture cutoff `2026-09-16T04:25:38Z`, SHA-256 `27a4dad7eb843a13e4e2727180a6cd3e5d07464192e5fa14d2f27057d5d02eaf`. Packet SHA-256: #589 `e13209b9d2a1e77a203f6b0441258312933c6c8e2312c8eab16d7492d03179b8`; #605 `124c926d34ca343c80103e0e9b12cac0989d528a62b804c8dce8d4d10af4f52c`; #567 `c23ffdfb8ff82eadc3e9aa3d95d2cb1df067078e6e26bc595976613cdbaae9b9`.
- Three nonempty packet/controls validated with stable prompt/fact/gap IDs and a path/secret scan. An unknown output citation, removed #605 closing relationship and removed #567 identity gap were rejected by pre-inference negative controls. The source GitHub observation time and response hashes are in the private manifest.
- One synthetic probe preserved **re-prompt** versus **restart**, rejected a same-number wrong-repository join, avoided merge-to-deployment inference and ignored embedded completion instructions. It used 25,758 reported input/356 output tokens in 14.31 seconds, with zero tool events.
- Six real samples: two fresh sessions per case, no transport retry or tool event; 98.51 seconds aggregate call wall time. Reported per-call input 26,457–26,595 tokens, output 409–771 tokens. API-equivalent estimate $0.009633 for real calls, $0.011396 including probe, using [official Luna standard rates](https://developers.openai.com/api/docs/models/gpt-6-luna). **Not billed cost.** All calls remained within attempt, time, reported-token and estimated-cost envelopes. Codex CLI `0.155.0-alpha.16` was invoked with exact `gpt-6-luna` high in fresh isolated read-only sessions; its model catalog lists that combination, but JSON run events do not return a server model identifier, so returned identity is unverified.
- Deployment and chat causation remain unknown; a later issue closure was not attributed to earlier chats. No source status write, model default switch, Daily scheduling, vault publication or production deployment occurred.

## Decision and operator review

The private `review-589.md`, `review-605.md` and `review-567.md` show all three views and both candidate repeats, with method identities withheld pending feedback. Ask which view best explains and resumes each case and what, if anything, is misleading. A preference cannot override this run's citation failure. Another prompt revision would require a new registered experiment; this run does not authorize Daily integration or a general Luna superiority claim.

Fresh repository verification and limitations are in [QA.md](QA.md). [Issue #300](https://github.com/HiQS-Labs/rebalanceOS/issues/300) holds the detailed plan and progress.
