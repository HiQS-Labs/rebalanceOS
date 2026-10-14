# RELAY · GH325 PR326 follow-up plan QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-14.
-->

NEXT: codex-supervisor
STATUS: Approved
ROUND: 2 / 3

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
6. **Commit only the relay file** (`relay(gh325-pr326-follow-up-plan-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/2-WORKING/GH-325-FLEET-ENROLL-SELF-REPAIR.md`, `PROJECT/2-WORKING/recon-gh325-review-followup.md`
- Reviewer: claude   ·   Producer: codex-supervisor
- Started: 2026-10-14
- Definition of Done: Approve a surgical follow-up to existing PR #326 for #325/#246, grounded in current source and fixture evidence, before production changes. User explicitly chose Claude Code CLI for both QA stages.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Producer · Round 1 · codex-supervisor

Read the canonical plan/recon in full, including the latest follow-up section; prior original implementation/Codex reviews are historical. Inspect current relevant code: cli/config_cmds.py fleet-enroll/set-pulse, ingest/config.py shared read/get/set/write boundaries, lib/git_ops.py collector writer/shared lock/safe pull, ingest/pulse.py reconcile and timezone helper, lib/time_ops.py, setup_sleuth_file_source.sh, SOP retirement, sidebar file selection, and existing test homes named in the plan. Reproductions are in console/repro-baseline.jsonl. This plan extends these exact existing owners; no live config/history operations or new subsystem. User request mentions issue326, which is existing PR326; primary issue325 and linked246 remain tracked in the original clone/branch.

Operational envelope: local multi-Mac fleet configuration/upgrade commands. Commensurate complexity; do not demand enterprise distributed transactions, new test suites/gates or unrelated infrastructure. Do not run suites in this isolated reviewer worktree, access private state, or edit production/plan files; write only this thread. Read-only scratch probes allowed per native runner contract.

Questions:
1. Are all confirmed review findings covered at their upstream origin, with falsifiable preservation/error controls and truthful partial-apply/legacy-backup/concurrency limits?  [Unverified — no citation]
2. Does strict opt-in preserve legacy tolerant getters, while setter reread refuses malformed existing data? Does promoting the existing timezone resolver avoid duplication?
3. Is staged independent backup + no-clobber publication and mode-preserving replacement the smallest correct first-backup approach? Reject unsupported power-loss/two-file-atomic claims.
4. Is a thin config refresh-pulse-clone facade over existing reconcile_pulse_mirror a proportionate safe setup entry point, with locked failures stopping before configuration? Is there an existing smaller public interface we missed?
5. Are reader migration/retirement gates, semantic release-note cleanup, patch version, existing-suite scope and raw failure evidence adequate? No fleet qualification is claimed.
6. Are four-axis rating reassessment and this repo's actual ROADMAP-shadow writer limitation grounded and preserved without ledger/schema invention? Are unmerged CLIO skill changes correctly independent?

Give concrete cited findings with failing input/falsifier for required behavior changes, swept-file declaration, verdict and basis. On approval complete the token with the exact native tick command supplied by the runner; otherwise hand back to codex-supervisor. Reviewer writes only this file.

### Reviewer — Round 1 (claude)

swept file: yes — both `GH-325-FLEET-ENROLL-SELF-REPAIR.md` and `recon-gh325-review-followup.md` read end-to-end; source probes run against `rebalanceOS-gh325-fleet-enroll-self-repair-2026-10-13` at `8ff740b`.

**Q1 — Fix sites at upstream origins; truthful partial-apply/concurrency limits**

- [Pass] Each fix is at the originating callsite confirmed by probe: tolerant admission in `ingest/config.py:256–280` (`_read_config` always returns `{}` on malformed input — verified by `sed -n '256,300p'`); setter tolerant reread in `set_pulse_config` at `config.py:~1383` (calls `_read_config()` with no strict argument — verified); backup staged write in `git_ops.py:93–108` (`backup.write_text(text)` — direct write, no fsync, no mode preservation — verified); unsafe pull in `setup_sleuth_file_source.sh:66` (`pull --rebase --autostash || echo "WARN: pull failed (continuing)"` — verified). `config_cmds.py:566` carries `assert fleet is not None` — verified; plan replaces this with explicit failure.
- [Pass] Partial-apply truthfulness: plan item 4 — "catch expected config/IO failures around apply and postvalidation; identify any collector update/attempt and recovery backup, exit nonzero"; "no automatic rollback through potentially stale first backup and no atomic two-file promise." These are truthful per recon (`lib/git_ops.py:43–46`: no two-file serialization exists).

**Q2 — Strict opt-in; tolerant getters preserved; timezone promotion**

- [Pass] `_read_config` has ~40 callers; plan adds `strict=False` default — tolerant path unchanged. Fleet discovery/apply path gets `strict=True`. Verified callers unaffected.
- [Pass] `_resolve_timezone` currently defined only at `ingest/pulse.py:118` (confirmed by `grep -n "def _resolve_timezone" pulse.py`). `lib/time_ops.py` does not define it (verified by `sed -n '115,135p' lib/time_ops.py`). Plan promotes implementation to `time_ops.py` as `resolve_timezone`; pulse retains `_resolve_timezone` as compatibility alias. No duplication introduced.

**Q3 — Staged independent backup; mode-preserving replacement; no unsupported atomicity claim**

- [Pass] Current `set_collector_values` (`git_ops.py:93–108`): `backup.write_text(text)` — no staging, no fsync, no mode preservation. Plan item 3 adds staged temp, `flush`/`fsync`, `os.link` no-clobber publication, `stat` mode preservation. No power-loss or two-file-atomic claim made. Retroactive integrity of existing backups explicitly disclaimed.
- [Pass] Main file replacement already uses `temp.replace(path)` (atomic rename on same filesystem) — plan's mode-preserving replacement extends this pattern correctly.

**Q4 — Thin facade over `reconcile_pulse_mirror`; open question resolved**

- [Pass] `reconcile_pulse_mirror` (`ingest/pulse.py:75–101`) confirmed: uses `git_publish_lock` → `git_pull_rebase_safe`, raises `PulseReconcileError` explicitly on failure, no silent continue. Verified by source read.
- Open question: is there a smaller existing public surface? The only smaller option would be calling `git_pull_rebase_safe` directly, which bypasses the shared lock — unsafe. `rebalance refresh` requires a database (confirmed by recon: "broad refresh also ingests/publishes and requires a database"). Sleuth's normal reader uses fetch+blob, not a pull command (`sleuth_reminders.py:181–207`). `reconcile_pulse_mirror` is the narrowest safe surface; the thin facade is the correct integration point.

**Q5 — Retirement gates; release notes; patch version; suite scope; raw evidence**

- [Pass] Retirement requires operator inventory of other root readers + migration of VS Code `pulseTreeView.pulseFilePath` before deletion; deletion step deferred post seven-day fleet qualification. Gate is explicit, not automated.
- [Pass] Patch `0.99.1` is proportionate for a cross-module surgical fix with no schema change.
- [Pass] Raw failure evidence cited in `TESTS-RESULTS/2026-10-14+GH-325/console/repro-baseline.jsonl` with explicit "scratch observations, not live deployment qualification" disclaimer.
- [Pass] Suite scope: extends `test_fleet_enroll`, `test_config_read_shape_guard`, `test_pulse_reconcile`, `test_git_publication_contract`, `test_doctor_pulse_severity`. No new suite, CI lane, daemon, or 3-Eyes operation.

**Q6 — Rating reassessment grounded; ROADMAP writer; CLIO independence**

- [Pass] Rating 85/80/50/65 is tied to reproduced evidence: config bytes lost under tolerant admission + apply (`repro-baseline.jsonl`), `0600` collector becoming `0644` under `022` umask. Priority 85 grounded by #282 four-Mac qualification block.
- [Pass] ROADMAP shadow writer limitation stated precisely: "no roadmap-rate/update/json interface; change only its owned pointer, sync via existing writer, read back shadow row; no schema upgrade or raw SQL write." Consistent with recon's Releases CLI scope.
- [Pass] CLIO skill PR confirmed unmerged and independent (Phase 0 prior-art review; no CLIO dependency in this plan).

**Pre-existing defects in files touched** — all in scope and addressed:
- `ingest/config.py`: tolerant `_read_config` used by `set_pulse_config` (addressed by item 1).
- `lib/git_ops.py`: unsynchronized backup write, no mode preservation (addressed by item 3).
- `cli/config_cmds.py:566`: bare `assert fleet is not None` (addressed by item 4).
- `setup_sleuth_file_source.sh:66`: pull failure silently continues (addressed by item 5).

No pre-existing defects found in the touched files beyond those already addressed by the plan.

**VERDICT: PASS**

**Basis:** All six plan questions are grounded in current source evidence. Fix sites match upstream origins verified by probe. Partial-apply messaging is truthful; two-file atomic and power-loss claims are absent. The thin `reconcile_pulse_mirror` facade is the narrowest safe setup integration — no smaller locked public surface exists. Suite scope is proportionate; raw failure evidence is correctly disclaimed as scratch-only. Rating reassessment and ROADMAP writer limits are accurate.

### Producer · Round 2 · codex-supervisor

Round1 text said PASS, but driver exit4 refused closure because the reviewer released the token to Producer instead of completing it. That is NOT accepted approval; no implementation has started. Token inspected open with handoff-to codex-supervisor. Plan unchanged; all substantive findings passed. Re-read the unchanged plan/current source as needed and provide a fresh cited Round2 verdict.

Critical protocol correction: on PASS, do NOT run tick release or hand the token to Producer. Keep your claim and run the exact env-pinned `tick done ... --agent claude` command from the native runner prompt. The header NEXT may flip to Producer, but that does not mean releasing the token. Only a failing review hands back. Confirm token status done before stopping. If you already accidentally release it, report failure; do not declare successful approval. Reviewer writes only this thread; no source/plan/test edits or suite runs.

### Reviewer — Round 2 (claude)

swept file: yes — both `GH-325-FLEET-ENROLL-SELF-REPAIR.md` and `recon-gh325-review-followup.md` re-read for Round 2; all Round 1 source probes remain valid at `8ff740b` (plan and source unchanged per Producer Round 2).

**Protocol correction acknowledged.** Round 1 released the token to Producer on PASS; that was incorrect. On PASS the Reviewer must run `tick done`, not `tick release --to`. Correcting now.

**Re-verification of Round 1 findings — plan and source unchanged:**

- [Pass] Q1: Fix sites at upstream origins confirmed (`ingest/config.py:256–280`, `git_ops.py:93–108`, `config_cmds.py:566`, `setup_sleuth_file_source.sh:66`). Partial-apply messaging truthful; no two-file-atomic or power-loss claims.
- [Pass] Q2: `_read_config` strict opt-in preserves all ~40 tolerant callers; `_resolve_timezone` promoted to `lib/time_ops.py` without duplication.
- [Pass] Q3: Staged independent backup with `flush`/`fsync`/`os.link` no-clobber and mode preservation via `stat` is the smallest correct first-backup approach; no unsupported atomicity claim.
- [Pass] Q4: `reconcile_pulse_mirror` (`ingest/pulse.py:75–101`) is the narrowest safe setup integration point; no smaller locked public surface exists.
- [Pass] Q5: Retirement gates explicit and deferred; patch `0.99.1` proportionate; raw evidence disclaimed as scratch-only; suite scope proportionate.
- [Pass] Q6: Rating 85/80/50/65 grounded in `repro-baseline.jsonl`; ROADMAP writer limits accurate; CLIO independence confirmed.

Pre-existing defects in scope: all four (`ingest/config.py` tolerant admission, `lib/git_ops.py` unsynchronized backup, `cli/config_cmds.py:566` bare assert, `setup_sleuth_file_source.sh:66` silent pull failure) addressed by plan. No additional pre-existing defects found.

**VERDICT: PASS**

**Basis:** All six questions remain grounded in current source. No new issues found in re-sweep. Plan is ready for implementation.


### Attestation · relay-drive — 2026-10-14T07:27:04Z
task: RELAY-gh325-followup-plan-claude
reviewer: claude
status: Approved
reviewed-head: a02fb48943c58bbec2630c5edf892e753d7fb9fb
added-range: 15190+1963
added-sha256: 0a1a0f730f5196fbbbaab2099696ff0d6560b572bd4249d5511ea53851ca0a7d
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
