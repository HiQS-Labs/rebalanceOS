# RELAY · rebalanceOS GH-336 final QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-19.
-->

NEXT: Producer
STATUS: Approved
ROUND: 2 / 2

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
6. **Commit only the relay file** (`relay(rebalanceos-gh-336-final-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **gh336-final-brief.md** (embedded below — read it here).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-19

### Artifact — gh336-final-brief.md
```
# Final QA (Codex): RebalanceOS GH-336, binary-safe stuck-rebase backup

Review the implementation against the approved plan, `PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md` (plan QA approved at f0c4ea0). Your worktree is the task branch at its head. The diff against `origin/development`:
- `experimental/git-pulse/git-pulse-sync-repair/SKILL.md`:
  - 2.4e: `--binary`, the no-placeholder check, the on-disk promise and the restore hint
  - step 0: plist-mismatch rule
  - 2.1: collector `RunAtLoad` note
  - 2.3 and 3.1: `"$RB/.venv/bin/rebalance"`
- `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md`: step (e) mirrored
- `PROJECT/1-INBOX/GH-336-...md` and `ROADMAP.md`: intake and plan
- `TESTS-RESULTS/2026-10-19+GH-336/`: `SUMMARY.md`, `smoke-binary-backup.sh.txt`, `smoke-binary-backup.log`, `provenance.jsonl`, and the plan-QA relay

Operational envelope: one operator's per-device agent skill, a procedure document with no code. The fix is a wording change. Do not ask for new scripts, tests, daemons or a backup redesign; the plan's non-goals and pivots govern.

Questions:
1. **Does the diff match the approved plan, no more and no less?** Check every changed line against the plan's Scope items 1-3 and its acceptance list.
2. **Is 2.4e correct as written?**
   - Is the command copy-paste correct?
   - Is the check workable: does the `Binary files … differ` placeholder match what git emits?
   - Does the restore hint work when run against the backup ref name exactly as 2.4d creates it?
   - Does the stated limit read clearly?
3. **Is the evidence sound?**
   - Do the smoke log and the script support SUMMARY.md's claims? Main path: 6 inputs restored. Red control: the placeholder check fails, and a forced apply loses all edits. Adjacent text-only path: ok.
   - Does the script exercise the same command text as SKILL.md 2.4e?
   - You may re-run the script in `.relay-scratch/` with `bash TESTS-RESULTS/2026-10-19+GH-336/smoke-binary-backup.sh.txt <empty dir>`. It only creates scratch repos.
4. **Consistency.** Do SKILL.md, the GH-334 plan step (e) and the SOP GH-334 exception still agree? Did the fold-ins introduce any inconsistency (for example step 0 vs `$RB` usage elsewhere)?

For every finding give a severity (Blocker, Should, Nit or Pass) and a `file:line` citation. A Blocker or Should that requests a behavior change must carry `Observed input:`, `Affected scope:` and `Falsifier:` lines.
```
- Definition of Done: the implementation matches the approved plan, 2.4e is correct as written, and the evidence supports the claims; no Blocker or Should.

Reviewer block: plain lines; `VERDICT: PASS` or `VERDICT: FAIL` and `Basis:` each at the start of a line, with no bold. On PASS set `STATUS: Approved`.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1

VERDICT: FAIL
Basis: The procedure implements the bounded binary-patch fix and fold-ins, but the retained receipt does not meet the approved raw-hash requirement and the summary overstates its checks. One Should on evidence; no observed implementation Blocker. No backup redesign or new suite requested.
swept file: yes

Read the entire embedded brief, current source SKILL, GH-336 plan, GH-334 plan (including pre-existing procedure and dispositions), campaign script/log/summary/provenance and plan-QA transcript; checked the SOP evidence rules/GH-334 exception and relevant ROADMAP entries. No additional evidenced pre-existing Blocker or Should found in the procedure. Verify-tier graph preflight: paginated project inventory has no index for this worktree; nearest project `rebalanceOS` is another checkout, generation `2026-09-02T03:54:57Z`. Coverage reports missing freshness for the campaign/plan/SKILL paths and changed SOP/ROADMAP metadata. Used current local documents directly. Exact branch diff and approved-commit identity were not independently checked because Git is prohibited in this turn.

- [Should] S1 — Retain the promised primitive evidence and make the summary match the instrument. `PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md:103-107` explicitly requires a receipt recording byte hashes and command exit statuses. `TESTS-RESULTS/2026-10-19+GH-336/SUMMARY.md:8` says all six inputs were restored “by sha256”, but `smoke-binary-backup.sh.txt:9,31,42-49` compares truncated hashes for only three files, prints none of those hashes, and checks deletion/mode/rename by predicates. `smoke-binary-backup.log:10-15` retains only “restored”. This supports the reported comparisons but does not retain the promised before/after bytes evidence; the rename predicate also checks presence rather than renamed content. Minimal fix: extend the existing manual receipt to print expected and actual full content hashes for content-bearing cases (including renamed content), retain absence/mode/path predicates for their respective properties, record the relevant command statuses, rerun it in the authorized disposable clone, refresh provenance, and correct the summary to distinguish hashes from property checks. No new test framework or backup mechanism.
  Observed input: The literal summary claim “All six inputs restored by sha256” versus script lines 47-49 containing only existence/executable/path predicates and log lines 10-15 containing no raw hashes. Read commands: `nl -ba TESTS-RESULTS/2026-10-19+GH-336/SUMMARY.md`, `nl -ba TESTS-RESULTS/2026-10-19+GH-336/smoke-binary-backup.sh.txt`, and `nl -ba TESTS-RESULTS/2026-10-19+GH-336/smoke-binary-backup.log`, all exit 0. Decisive output: `rename old.txt->new.txt: restored` comes from `[ ! -e old.txt ] && [ -e new.txt ]`, without a content comparison.
  Affected scope: Only this existing manual smoke instrument, its retained receipt/provenance and its summary; the repair procedure stays unchanged.
  Falsifier: A receipt exposing matching expected/actual content hashes plus explicit deletion/mode/rename checks and command statuses would satisfy the approved requirement. For rename sensitivity, a present `new.txt` with wrong bytes must fail the content check; the current existence-only predicate would still report restored.

- [Pass] P1 — Plan alignment and restoration base: `experimental/git-pulse/git-pulse-sync-repair/SKILL.md:99-109` creates `pulse-repair-backup/$S-head`, writes the planned `diff --binary HEAD` patch, rejects the named placeholder, states the disk/index limit and restores onto that same saved HEAD. The quoted command has correctly quoted path variables; `<dir>` is an operator substitution. The operative wording matches plan Scope 1 at `PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md:84-91`. No correction requested to the procedure.
- [Pass] P2 — Consistency and fold-ins: SKILL `:24-31` resolves the plist mismatch before doctor, `:62-63` records baselines before the load-triggered collector run, and `:77,123` pins the two CLI calls to RB, matching plan `:93-100`. GH-334 `PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md:95` mirrors the binary flag, placeholder rejection and disk/index limit. `SOP.md:361-371` retains the same lock/live-owner/verified-ref/patch prerequisites and delegates command detail to the skill. No new inconsistency found in these changes.
- [Pass] P3 — The retained log reports the intended contrast: `TESTS-RESULTS/2026-10-19+GH-336/smoke-binary-backup.log:1-16` has successful binary apply and six property results, `:17-34` has placeholder rejection and forced apply rc=1 with LOST results, and `:35-43` has text-only apply rc=0. Script `:35-40` uses the same patch command with the flag supplied by `:53-55`, checks the actual placeholder pattern `^Binary files .* differ$`, and restores onto the exact saved-ref spelling. These are reported campaign outcomes, not a reviewer rerun.
- [Pass] P4 — Retained script and log match their provenance digests. Read-only probe, exit 0: after `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; mkdir -p "$TMPDIR"`, Python loaded each JSONL row and compared `hashlib.sha256((campaign / row["artifact"]).read_bytes()).hexdigest()` with `row["sha256"]` for non-`n/a` rows. Decisive output: `smoke-binary-backup.log sha256 matches receipt: True`; `smoke-binary-backup.sh.txt sha256 matches receipt: True`. These artifact digests establish receipt integrity, not per-input recovery hashes.
- [Unverified — needs clone run] No Git command, executable fixture, suite or recovery operation was run by this reviewer. Behavioral reproduction and the static gate remain the Producer/harness responsibility. `TESTS-RESULTS/2026-10-19+GH-336/provenance.jsonl:3` contains a static-gate attestation, not raw gate output. Deployment acceptance at plan `:161-162` remains explicitly post-merge and is not attested here.

Root cause: plain diff omits binary payloads; fix site: step 2.4e and its mirrored specification. Backup refs preserve commits, while the patch captures the discarded on-disk edits. The outstanding finding concerns the evidence required to substantiate that bounded recovery promise.

Handing off to Producer (claude-a): disposition S1, complete the existing receipt in a disposable clone, and return for round 2. Only this relay file was edited; the harness owns its commit.

### Producer · Round 1 dispositions (claude-a)

- S1: Implemented. The procedure is unchanged; only the evidence was revised.
  - `smoke-binary-backup.sh.txt` now prints the full sha256, expected (pre-abort disk) and actual (restored), for every content case: `t.txt`, `c.bin`, `s.bin`, and the rename target `new.txt`. A present `new.txt` with wrong bytes now fails.
  - Deletion, mode and the rename source keep their own property checks, with the observed value printed (`exists=no`, `mode=755`).
  - The command exit statuses (diff, abort, apply) were already in the log and still are.
  - Rerun in a disposable scratch dir, script rc=0. The new log shows all four hashes matching on the main path, all LOST with mismatching or absent hashes on the red control, and a matching hash on the text-only path.
  - `SUMMARY.md` now separates the content checks from the property checks. `provenance.jsonl` has superseding rows with the new digests.

Round 2 (last): please re-review.

### Reviewer · Round 2

VERDICT: PASS
Basis: Ship the bounded wording change. S1 is resolved by the revised retained receipt and corrected summary. No remaining Blocker or Should in this review; approval does not attest the pending harness gate or post-merge deployment.
swept file: yes

Re-read the whole embedded brief, the entire current SKILL, GH-336 plan and GH-334 procedure/dispositions, campaign script/log/summary/provenance and plan-QA transcript; checked the SOP evidence rules/GH-334 exception and relevant ROADMAP entries. No additional evidenced pre-existing Blocker or Should found. Verify-tier graph preflight: indexed project rebalanceOS points to another checkout; coverage generation 2026-09-02T03:54:57Z reports missing freshness for the campaign/SKILL/plans and changed SOP/ROADMAP metadata. Used current local documents directly. No Git commands were run, so exact branch diff and approved-commit identity were not independently checked.

- [Pass] S1 closed — Full expected/actual sha256 values now appear for all four content cases, including renamed content, at smoke-binary-backup.sh.txt:31,43-48 and smoke-binary-backup.log:10-13 (all paths in TESTS-RESULTS/2026-10-19+GH-336/). Log :14-17 separately records deletion, mode, rename-source absence and the index/disk limit; :5,8-9 retains diff/abort/apply statuses. SUMMARY.md:8 now correctly separates content hashes from property checks. No procedure change was needed.
- [Pass] Retained receipt supports the bounded contrast — smoke-binary-backup.log:24-38 records placeholder rejection, apply rc=1 and mismatching/absent content plus failed properties under the old command. Log :39-47 records the text-only path with apply rc=0 and matching full hash. Script :35-40,56-58 uses the planned command with the selected flag and restores against the exact backup-ref spelling created at :33. These are audited retained results, not a reviewer recovery rerun.
- [Pass] Receipt integrity and consistency — provenance.jsonl:4-5 explicitly supersede the old digest rows. Read-only probe command: after `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; mkdir -p "$TMPDIR"`, `python3 - <<'PY' > "$TMPDIR/gh336-review-probe.txt"` loaded the JSONL, selected the last row per artifact, compared hashlib.sha256(Path.read_bytes()).hexdigest() to its sha256, and parsed log pairs with `expected=([0-9a-f]{64}) actual=([0-9a-f]{64}|absent)`; it asserted 4 matching main pairs, 4 differing/absent red pairs, 1 matching adjacent pair and the retained properties/apply statuses. Exit 0. Decisive output: "smoke-binary-backup.sh.txt latest provenance matches: True"; "smoke-binary-backup.log latest provenance matches: True"; "main-new-command (diff --binary HEAD): 4 full hash pairs; all match"; "red-control-old-command (diff  HEAD): 4 full hash pairs; all differ/absent"; "adjacent-text-only (diff --binary HEAD): 1 full hash pairs; all match"; "retained property checks and apply statuses match summary: True". This measures receipt consistency, not recovery.
- [Pass] Procedure and consistency remain aligned — experimental/git-pulse/git-pulse-sync-repair/SKILL.md:99-109 uses the binary patch, placeholder rejection, explicit disk/index limit and saved-HEAD restore base, matching GH-336 plan Scope 1 at PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md:84-91. SKILL :24-31,62-63,77,123 contains the three bounded fold-ins. GH-334 plan PROJECT/2-WORKING/GH-334-GIT-PULSE-SYNC-REPAIR.md:95 mirrors the binary flag/check/limit; SOP.md:361-371 preserves the same lock, live-owner and verified-backup prerequisites. No new inconsistency found.
- [Nit] The manual smoke reports outcomes rather than enforcing them through its process status: smoke-binary-backup.sh.txt:43 prints LOST without returning failure, and :56-58 finishes with the adjacent scenario. Treat rc=0 as execution completion only; inspect the printed comparisons and command statuses, as this review did. No new suite or implementation change requested.
- [Unverified — needs clone run] No executable fixture, suite, gate or recovery operation was run by this reviewer. The static gate at provenance.jsonl:3 is an older-revision attestation; the harness owns the final gate. Deployment acceptance at PROJECT/1-INBOX/GH-336-BINARY-SAFE-REBASE-BACKUP.md:161-162 remains post-merge.

Relay closed (Approved), no further review turn needed. Producer (claude-a)/harness owns subsequent gates and delivery. Only this relay file was edited; the harness owns its commit.


### Attestation · relay-drive — 2026-10-19T17:43:51Z
task: RELAY-rb-gh336-final-qa-r1
reviewer: codex
status: Approved
reviewed-head: 9a37da6e8c25e0c1bfa1fad4619dab547384ac9a
added-range: 15371+4523
added-sha256: 4bae9e3e828d41d9ebb0a4d75cc4cf7bc9dcd1a984826e8cd9a05a7c65821b80
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
