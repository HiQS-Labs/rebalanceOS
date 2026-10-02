# RELAY · gh282-config-fable-r1
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-02.
-->

NEXT: Producer
STATUS: Open
ROUND: 1 / 4

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
6. **Commit only the relay file** (`relay(gh282-config-fable-r1): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Approval token rule (overrides generic handoff instructions)
On approval call task done with the exact absolute env-pinned tick command provided in your native turn prompt. Never release an Approved task to Producer. On findings only, release is valid.

## Setup
- Artifact under review: **config-packet.md** (embedded below — read it here).
- Reviewer: claude   ·   Producer: producer
- Started: 2026-10-02

### Artifact — config-packet.md
```
Review GH-282 post-landing hardening and deployment documentation. PR303/CLIO5 are merged; Studio was actually activated at runtime bb84cd0 with verified backups and unchanged capture/note/collector schedules. No private prompt text/UUID/path is in the public receipt. Late CodeRabbit findings are reproduced by config-red.log: missing None target TypeError, publication mismatch ValueError, sync invalid identity ValueError, scheduler doctor ValueError, fleet doctor OSError. Five same probes now green. Review touched functions and direct callers in git_ops.fleet_settings/publish_git_paths, index_ops._refresh_sync, doctor scheduler/fleet checks; target validation before writes, structured refusals, no valid-flow regression. Collector deadline assignment now fails before export on Python failure. Version 0.97.1 is consistent. Verification: followup-source-manifest.json pins source16582d2; 492 affected tests/28subtests and43check real-Git probe passed, type/static gates clean. Original 2807fullsuite applies to preceding implementation only, not claimed rerun here. Read public deployment.json/plan/SOP/CHANGELOG for honest operational qualification boundaries; initial unmarked heartbeat used legacy classification until first marker delivery, then real queue-to-delivered verified. Other3Macs remainoff; real scheduled/offline/7dayqualification pending. Do not execute suites in reviewer worktree; source/reasoning and harmless pure probes only. Provide bounded findings with Observed input/Affected scope/Falsifier; approve through native task done.  [Unverified — no citation]
```
- Definition of Done: _<fill in the acceptance criteria the Reviewer grades against>_

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Producer · Round 1

Committed candidate ready for independent review; no installed changes.

VERDICT: PASS
Basis: Ready for QA.

### Reviewer · Round 1 (claude)

swept file: yes — read the full diff `bb84cd0..HEAD` plus the whole of `fleet_settings`, `publish_git_paths`,
`_refresh_sync`, `_check_scheduler_liveness`, `_check_pulse_collectors`, `_local_device_id`, `get_device_id`,
`publish_pulse`/`_publish_pulse`, the collector deadline block, and every caller of `fleet_settings` /
`get_device_id` / `publish_git_paths` under `src/`. No suites, fixtures or repo code were executed; probes were
pure reads (regex over CHANGELOG.md, `shasum`). Pre-existing defects found in touched files: F2, F5, F6 below.

**F1 [Blocker] The 0.97.1 CHANGELOG entry is spliced into the maintainer blockquote; there is no 0.97.1 version
heading and the template sentence is destroyed.** The packet's "Version 0.97.1 is consistent" is false for the
changelog.
- Observed input: `CHANGELOG.md:9` now reads ``> MINOR = feature · PATCH = fix) under a `## 0.97.1 — 2026-10-02``
  (heading text opened inside a backtick span on a `>` line), the entry body is `CHANGELOG.md:11`, and
  `CHANGELOG.md:13` is the orphaned tail ``## [x.y.z] - YYYY-MM-DD` heading. Do``. Probe (rc=0), using the
  repo's own parser regex from `scripts/audit_modules.py:192` (`^## \[([^\]]+)\]`):
  `python3 -c 'import re;c=open("CHANGELOG.md").read();print([x.group(1) for x in re.finditer(r"^## \[([^\]]+)\]",c,re.M)][:3])'`
  → `['x.y.z', '0.97.0', '0.96.1']`. The "most recent version" is now the literal placeholder `x.y.z` with no
  date; `0.97.1` is not a heading at all.
- Affected scope: `CHANGELOG.md` lines 7–15 only (docs; no runtime behaviour), and anything that reads the first
  `## [..]` heading (`parse_most_recent_changelog_version`, `scripts/audit_modules.py:196-217`).
- Falsifier: after the fix the same probe must print `['0.97.1', '0.97.0', '0.96.1']` and lines 7–11 must be
  byte-identical to `bb84cd0`'s blockquote. If it already printed that, this finding would be wrong — it does not.
- Fix: restore the blockquote exactly as at `bb84cd0`; add `## [0.97.1] - 2026-10-02` with a `### Fixed` list
  directly above `## [0.97.0] - 2026-10-02`, in the existing bracket/hyphen format.

**F2 [Should] Invalid fleet identity makes the scheduler doctor drop every scheduler row.**
`doctor.py:816-819` returns `[Check("fleet configuration", FAIL, …)]` alone, so "installed on this device but
NOT loaded in launchd" FAILs (`doctor.py:834-846`) are suppressed exactly when configuration is also broken.
Better than the old crash, but it hides the GH-59 signal.
- Observed input: the candidate's own probe case (`config-contract-probe.py:28-31`): jobs `['pulse-sync']`,
  `launchctl_output=''`, `_local_device_id` raising `ValueError('identity mismatch')` → result is one
  `fleet configuration` check and no `scheduler:pulse-sync` row.
- Affected scope: `_check_scheduler_liveness` when `current_device_id` is not passed and `_local_device_id()`
  raises `ValueError`/`OSError`; valid configuration is untouched.
- Falsifier: a fixture with that same input plus a present `com.rebalance-os.pulse-sync.plist` in `agents_dir`;
  expected today: no `scheduler:pulse-sync` FAIL (confirms the finding). If product intent is "configuration
  failure supersedes job liveness", say so in the docstring and decline.
- Fix: append the configuration FAIL and keep evaluating jobs that have no `_DEVICE_SCOPE_REGISTRY` entry
  (device-scoped jobs can be skipped, since ownership is unknowable without an identity).

**F3 [Should] `deadline-control.log` is prose, not a witnessed control.** Its two lines
("Baseline bb84cd0: … masked by export, exit 0." / "Fixed 16582d2: … exits 1 …") carry no command, no captured
output and no exit status, unlike `config-red.log`/`config-green.log`. SOP requires cited measurements to be
reproducible. The red/green claim is graded `[Unverified — needs clone run]`. Fix: record the forcing command
(e.g. a `python3` shim on `PATH` that exits 1), stdout/stderr and `rc` for both heads. No behaviour change asked.

**F4 [Should] Four of the five "configuration" probes do not exercise configuration.**
`config-contract-probe.py:21,26,29,33` inject the exception with `patch(..., side_effect=ValueError/OSError)`,
so they prove only that the new `except` clauses exist; only case 1 (`:14-18`) drives real validation
(`pulse_target_path=None`). The packet's "sync invalid identity", "publication mismatch", "fleet doctor OSError"
read as end-to-end and are not. Fix: either describe them as catch-clause controls in SUMMARY.md, or drive them
from a real `config.sh` (mismatched `device_id`; missing file) as case 1 does. No behaviour change asked.

**F5 [Nit] Duplicate check name.** With a broken identity, doctor emits `fleet configuration` twice
(`doctor.py:2533` and `doctor.py:2538` each return one). Harmless; folds away if F2 is implemented by emitting
it from one place.

**F6 [Nit] Pre-existing: fleet dry-run text still promises latest pointers.** `index_ops.py:2113` prints
"publish this device calendar/email files and latest pointers" even when `fleet` is set, while the real path
(`index_ops.py:2123-2127`) omits `latest` in fleet mode.

**F7 [Nit] `followup-tests.log:10-14` embeds an absolute home path** (`/Users/<user>/rebalance-runtime/.venv/…`).
Same pattern already exists in this campaign's `pytest.log`/`static.log`, and `deployment.json` itself is clean
(no path/UUID/prompt text in its 44 lines), so the packet's "public receipt" claim holds for the receipt only.

**[Pass] Target validation precedes every write.** `git_ops.py:44-46` raises before `config.sh` is read;
`git_ops.py:511-521` returns `{"committed": False, "pushed": False, "git_error": "fleet configuration invalid: …"}`
before `publication_state_error`/`run_git` (`git_ops.py:524-529`); `index_ops.py:2100-2104` returns before
`git_publish_lock` (`index_ops.py:2122`); `pulse.py:1055-1058` returns `{"ok": False, "error": …}` before
`_publish_pulse`.

**[Pass] No valid-flow regression by reading.** Non-fleet config short-circuits at `git_ops.py:42-43` and at the
`cfg.get("pulse_fleet_enabled") and …` guards (`git_ops.py:512,516`); the valid fleet path differs only in
`target_path` being read once (`git_ops.py:75`). Remaining unguarded `fleet_settings()` calls
(`pulse.py:860`, `sync_snapshot.py:243,294`) are reached only after the guarded entry points or inside
`_refresh_sync`'s `except (GitPublishLockBusy, ValueError, OSError)` (`index_ops.py:2151`).

**[Pass] Collector deadline fix is correct by reading.** `collect.sh:5` is `set -euo pipefail`;
`collect.sh:386-387` now assigns with `|| exit 1` and exports separately, so a failed `python3` no longer hides
behind `export`'s exit status, and it precedes the lock/exec block (`collect.sh:393`). No other
`export VAR="$(…)"` remains in the file (`rg -n 'export [A-Z_]+="\$\(' experimental/git-pulse/collect.sh` → 0
matches, rg-native flags only).

**[Pass] Source manifest pins the reviewed tree.** `shasum -a 256` of all seven files in
`followup-source-manifest.json` matches (e.g. `git_ops.py` `cc186596…fcc371a`, `doctor.py` `795e6fc7…6e5e1e1`,
`collect.sh` `7751f461…1369b5`). Version string is `0.97.1` in `manifest.json:5`, `pyproject.toml:7`,
`src/rebalance/__init__.py:31` — consistent across code; not across CHANGELOG (F1).

**[Unverified — needs clone run]** "492 passed, 28 subtests" (`followup-tests.log:18`), the 43-check probe
(`followup-fleet-probe.log`), `config-green.log`, and mypy "117 source files" are taken as recorded; not rerun here.

**[Pass] Honesty boundaries are stated.** `deployment.json:3` `"live_fleet_qualification": false`,
`:41` `"other_macs_enabled": false`; `SUMMARY.md:33` says the earlier full-suite manifest is unchanged and Studio
activation "is not fleet qualification"; the legacy-heartbeat caveat is in `SOP.md:379-381`.

VERDICT: FAIL
Basis: Code changes are sound by reading and hashes match the manifest, but the shipped CHANGELOG is corrupted
(F1, observed and probe-confirmed): 0.97.1 has no heading and the maintainer template is broken. F1 must be
fixed; F2–F4 need a disposition; F5–F7 are optional.

Handing off to Producer — go to the Producer window and say "take your turn".

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
