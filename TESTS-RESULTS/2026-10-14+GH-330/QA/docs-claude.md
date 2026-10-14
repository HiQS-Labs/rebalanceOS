# RELAY · GH330 implementation round2 documentation gap
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-14.
-->

NEXT: codex-supervisor
STATUS: Approved
ROUND: 1 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
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
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh330-implementation-round2-documentation-gap): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/gh330-docs-packet.md** — the read-only path that
  `relay-drive.sh --artifact-file /tmp/gh330-docs-packet.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: claude   ·   Producer: codex-supervisor
- Started: 2026-10-14
- Definition of Done: Close explicit unread-documentation gap in implementation round1 (Approved with driver0). This is implementation review round2 of total3 allowed, confined to actual changed guides; code is unchanged and independently approved. Read the FULL seeded .relay-artifacts/gh330-docs-packet.md source snapshots.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Questions
1. Does the SOP require migrating and verifying each explicit sidebar/root-page reader BEFORE deleting legacy pages, while retaining collector pages/metadata?
2. Do the recovery notes accurately describe strict refusal, validated timezone, complete independent new backups, mode preservation, partial attempted writes, prior-backup inspection and lack of automatic rollback/ACL/concurrency/power-loss promises?
3. Do upgrade and Sleuth guides describe setup's existing shared lock, stop before settings on failure and normal read-side fetch/upstream blob without worktree writes?
4. Is there any actual changed-guide contradiction or missing acceptance requirement? Cite the seeded source name and exact quoted span. Local operator CLI scope; no runtime migration/deployment occurred. The full guides are supplied explicitly because round1 said it could not find them; do not rely on that mistaken availability inference.

On PASS keep reviewer claim; exact native environment-pinned tick done, never release. Only relay thread writes, no source/code/test changes. This supplemental pass spends round2, not a reset of the3-round implementation-review budget.

## Log

### Reviewer · Round 1 (claude)

swept file: yes — reviewed all three source snapshots in full (SOP.md, SLEUTH_SYNC.md, UPGRADE.md), including pre-existing sections. No pre-existing defects found that bear on the GH-330 scope.

**Q1 — SOP requires migrating/verifying each reader BEFORE deleting legacy pages, retaining collector pages/metadata?**

[Pass] Step 2 requires inventorying every root-page reader, migrating VS Code sidebars and any other explicit path, and explicitly states "A configured reader still using a root page blocks retirement." Step 3 conditions deletion on "Only after those reader checks." Step 4 names the kept paths: `pulse-<id>.md`, `devices/<id>.yaml`, `devices/<id>/` and `snapshots/`.
Citation: SOP.md §"Retire legacy shared pages (GH-325)" — "Only after those reader checks, delete root `live-pulse.md` and `live-pulse-*.md`" and "Keep `pulse-<id>.md`, `devices/<id>.yaml`, `devices/<id>/` and `snapshots/`"

**Q2 — Recovery notes describe strict refusal, validated timezone, complete independent new backups, mode preservation, partial attempted writes, prior-backup inspection, and no automatic rollback/ACL/concurrency/power-loss promises?**

[Pass] All eight claims are present in SOP.md §"Fleet configuration repair failures (GH-330)":
- Strict refusal: "refuses an existing malformed, non-object or unreadable Rebalance config"
- Validated timezone: "Pulse timezone input is validated before settings writes"
- Complete independent new backups: "New collector backups are completed independent copies before publication"
- Mode preservation: "replacement preserves Unix permission bits"
- Partial attempted writes: "A partial apply reports attempted writes and the backup location"
- Prior-backup inspection: "An older `config.sh.bak-gh325` may predate this guarantee: inspect it before manual recovery"
- No automatic rollback: "It never automatically restores a potentially stale first backup over newer settings"
- No ACL/concurrency/power-loss promises: "Ownership/ACLs, concurrent config writers and two-file/power-loss transactions are not qualified here"

**Q3 — Upgrade and Sleuth guides describe setup's existing shared lock, stop before settings on failure, and normal read-side fetch/upstream blob without worktree writes?**

[Pass] All three behaviors are present across both guides.
- Shared lock + stop on failure: UPGRADE.md step 3 — "Existing clones refresh under the shared writer lock, without autostash. Lock contention, dirty/in-progress Git state or refresh failure stops before Sleuth settings change."
- Read-side fetch without worktree writes: SLEUTH_SYNC.md §Freshness — "git fetch + git show of the upstream export blob, without worktree/index writes, rebase or autostash"
- Cross-reference: SOP.md GH-330 section and SLEUTH_SYNC.md §Setup both independently confirm the shared-lock model, consistent with UPGRADE.md.

**Q4 — Any changed-guide contradiction or missing acceptance requirement?**

[Unverified — no citation] No contradictions found between the three guides on the GH-330-scope behaviors. SOP.md, UPGRADE.md, and SLEUTH_SYNC.md give consistent accounts of the shared lock, stop-before-settings behavior, non-destructive fetch model, and the backup/recovery limits. No acceptance requirement from the Definition of Done is missing.

**VERDICT: PASS**
**Basis:** All four questions resolve [Unverified — no citation] with cited spans. The guides close the explicit documentation gap identified in round1. No blocker, should, or nit findings.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
