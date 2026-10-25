# RELAY · gh364-plan-codex
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-25.
-->

NEXT: Closed
STATUS: Approved
ROUND: 3 / 3

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
6. **Commit only the relay file** (`relay(gh364-plan-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/2-WORKING/GH-364-CLIO-RUNTIME-INSTALLER.md` (plan only; no code written yet)
- Evidence (read-only, seeded): `.relay-artifacts/gh364-evidence.txt`. It holds Skills Army HQ's name rule and `add` arguments (outside this repo), the collection `.gitignore`, and this Mac's live CLIO install (hooks, plists, registrations, loaded jobs; private paths anonymised).
- Source to read for grounding: `utils/CLIO/INSTALL.md` (Install ~L27-305, Auto-sync ~L618-670, Codex/Agy ~L673-758, Uninstall ~L760-810), `test/clio-capture.sh` (heredoc extraction L18-20), `utils/CLIO/README.md`, `AGENTS.md`, `ARCHITECTURE.md` (catalog row), `pyproject.toml` (ruff exclude), `utils/pdda/check_banned_imports.py`, `utils/pdda/check_script_inventory.py`, `.agents/skills/clio/SKILL.md`, `PROJECT/PDDA.md`.
- Requirements (issue #364 and the operator-reviewed installer plan, decisions A–D settled, folder rename chosen by the operator): one installer, run from the Skills Army–deployed copy, that installs, repairs, upgrades, checks and removes CLIO capture on a Mac. Hooks are symlinks into the deployed copy (decision A); HQ is unchanged and only records a prerequisite (B); `CLIO_MIN_PROMPT_CHARS` 20 is already the default (C); the installer traces to a source revision, makes no hand copies, backs up and adopts an existing hand install, never rewrites the exporter schedule, and never runs from a task clone. Acceptance is listed in the plan's suite cases.
- Operational envelope: one operator, about four Macs, bash 3.2 + jq + python3, launchd. Grade against commensurate complexity: no daemon, no HQ changes, no multi-user threat model, no generic installer framework.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-25
- Definition of Done: the plan meets every requirement with the least machinery; the rename is complete and leaves history alone; the desired state matches what INSTALL.md installs today (without rewriting the exporter plist); adopting a hand install is safe and reversible; the checks are falsifiable with red controls; and the gates are handled. Answer explicitly:
  1. Is renaming to `utils/clio-capture` the right fix for the HQ name rule, and is the reference list complete and correct (including what is deliberately left as history or fixture data)?
  2. Does generating the writer and shim into `~/.claude/hooks` (tracked by checksum), instead of into the collection, respect decision A and the "never dirty the Pulse tree" rule? Is the `stale` status, plus `upgrade`, an adequate refresh for them?
  3. Do the symlinked helpers work with the writer's `$(dirname "$0")/clio-store.py` lookup and the plists' `~/.claude/hooks/<script>` paths?
  4. Are the backup-before-replace, receipt-scoped uninstall, and "create tailer plists only when absent; never the exporter" rules safe for this Mac's live state, as shown in the evidence?
  5. Is collapsing repair/upgrade into an idempotent `install` acceptable against the plan's four verbs?
  6. Are suite cases 1–7 sufficient and bounded, and is anything missing (e.g. Linux without launchd, a missing `~/.zcode`)?
  7. Anything over-engineered?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1

swept file: yes

- [Should] The rename inventory is not complete: the plan deliberately exempts only `tests/test_github_direct_commits.py` as historical fixture data (plan L70), but `tests/test_github_commit_backfill.py` also embeds the old paths as the historical CLIO commit fixture (L29-35, L67-69, L133, L147). Add it to the explicit history/fixture exemption so implementation neither rewrites provenance nor leaves the reference audit inaccurate.
  Probe: `rg -n 'utils/CLIO' --glob '!CHANGELOG.md' --glob '!releases.sql' --glob '!PROJECT/**' --glob '!TESTS-RESULTS/**' --glob '!relay-system/**' .`; exit 0; decisive output included `tests/test_github_commit_backfill.py:34`, `:67-69`, `:133`, and `:147`.

- [Should] The suite does not make the stated ZCode absence boundary falsifiable. Desired state says ZCode registration is created only when `~/.zcode` exists (plan L88), while the seven enumerated cases contain no assertion that an initially absent `~/.zcode` remains absent/unmodified (L100-108). Add that assertion to the fresh-install case (or a bounded separate case).
  Observed input: a throwaway HOME with no `~/.zcode` (the suite setup in plan L100) and the requirement at plan L88.
  Affected scope: installs where `$HOME/.zcode` does not exist before `install --apply`.
  Falsifier: run fresh install with no `.zcode`; expected result is no `.zcode/cli/config.json` creation and no ZCode registration.
  Probe: `awk 'NR>=82 && NR<=108 {print NR ":" $0}' PROJECT/2-WORKING/GH-364-CLIO-RUNTIME-INSTALLER.md`; exit 0; decisive output contains L88's conditional and L102-108's seven cases without that assertion.

- [Pass] The generated writer/shim plus symlinked helpers is compatible with decision A and the existing path contracts: links land in `~/.claude/hooks` (plan L86), generated files also land there (L87), and the shim resolves the writer relative to that directory (`utils/CLIO/INSTALL.md:239-245`); the exporter resolves `clio-store.py` the same way (`utils/CLIO/prompt-log-to-md.sh:25-29`). Existing tailer/exporter plists therefore retain their required hook paths.

- [Pass] The backup/receipt boundaries are appropriately narrow for the observed live state: the plan leaves existing tailer plists byte-identical and never creates or rewrites the exporter plist (plan L89, L96-98), matching INSTALL.md's explicit warning to preserve an existing exporter's bytes, arguments, and interval (`utils/CLIO/INSTALL.md:618-623`).

- [Unverified — no citation] Collapsing repair and upgrade onto idempotent install is proportionate, provided the implementation accepts those names as aliases as exercised by suite cases 2–3 (plan L83, L103-104). Linux-without-launchd is not required by the Mac-only operational envelope; no unrelated pre-existing defect was found in the swept plan.

VERDICT: FAIL
Basis: The core approach is minimal and sound, but the reference audit must distinguish both historical fixtures and the suite must prove its explicit no-ZCode-side-effect condition before approval. No over-engineering finding.

handing off to Producer — go to the Producer window and say 'take your turn'

### Producer · Round 1

- [Should] incomplete fixture exemption → **Implemented**: `tests/test_github_commit_backfill.py` is added beside `test_github_direct_commits.py` as historical fixture data that the rename leaves unchanged.
- [Should] ZCode-absent boundary → **Implemented**: suite case 1 now asserts that with no `~/.zcode`, the install creates no `~/.zcode` and writes no ZCode registration.
- [Unverified] repair/upgrade aliases: the implementation accepts both names as the same converge, and suite cases 2 and 3 invoke them by those names.

### Reviewer · Round 2

swept file: yes

- [Should] Receipt-scoped uninstall is not yet safe against a user edit made *after* installation: the receipt records checksums and `status` can report `stale` (plan L91-92), but `uninstall --apply` unconditionally removes the recorded generated files/links and restores the old backup (L93-98). That silently deletes the newer user content before restoring the pre-install copy. Require uninstall to remove/restore a receipt path only when its current target/checksum still matches the receipt; otherwise preserve it, report drift, and retain an actionable receipt (or require an explicit force operation). Add a red-control suite case.
  Observed input: an installed `~/.claude/hooks/log-prompt.sh` whose bytes no longer match the receipt's recorded `sha` (the plan explicitly models this as `stale` at L91-92), with a pre-adoption hand-made backup recorded at L90-91.
  Affected scope: every receipt-owned generated file or link changed after `install --apply` and before `uninstall --apply`.
  Falsifier: a receipt-owned file/link that remains byte-identical / points at the recorded target; expected result is removal and restoration of its recorded backup. A changed `log-prompt.sh` must remain intact without an explicit override.
  Probe: `awk 'NR>=90 && NR<=108 {print NR ":" $0}' PROJECT/2-WORKING/GH-364-CLIO-RUNTIME-INSTALLER.md`; exit 0; decisive output says `status` reports `stale` (L92) while uninstall `removes owned links and generated files, then restores their backups` (L94), with no current-state match condition or drift test.

- [Pass] The producer resolved both Round 1 defects with cited plan changes: the second historical fixture is expressly exempted at plan L70, and suite case 1 asserts that an absent `.zcode` remains absent at L102. The live-reference sweep found no additional unclassified current path: the complete non-history matches are covered by plan L62-70, while the two excluded test files are named fixture data.

VERDICT: FAIL
Basis: The desired-state design remains minimal and all previous findings are addressed, but an uninstall must not silently overwrite a post-install user modification with an older adopted backup. No unrelated pre-existing defect was found in the swept plan.

handing off to Producer — go to the Producer window and say 'take your turn'

### Producer · Round 2

- [Should] uninstall vs post-install edits → **Implemented**:
  - Uninstall removes and restores a receipt-owned path only while it still matches the receipt (a link to `<src>/<file>`, or a generated file with the recorded sha).
  - A drifted path stays untouched along with its backup and is reported as `drifted`. The receipt keeps only those paths, and the run exits 1 for an operator decision; there is no force flag.
  - New suite case 8 is the red control: an edited installed `log-prompt.sh` survives uninstall, exit 1, receipt kept, while unchanged items are still removed.

### Reviewer · Round 3

swept file: yes

- [Pass] The receipt now makes uninstall safe against a post-install edit: it removes/restores only a still-matching recorded link or generated-file checksum, otherwise retains both the drifted path and its backup and exits 1 (plan L93-99). Suite case 8 supplies the requested red control (plan L109). This resolves the only open Round 2 finding.

- [Pass] The rename inventory is complete for current references: plan L62-68 covers the live paths returned by `rg`, and plan L70 explicitly preserves both historical test fixtures. Probe: `rg -n 'utils/CLIO' --glob '!CHANGELOG.md' --glob '!releases.sql' --glob '!PROJECT/**' --glob '!TESTS-RESULTS/**' --glob '!relay-system/**' . | head -120`; exit 0; decisive output included the two named historical fixture files, live test/source/docs references enumerated in L62-68, and `utils/pdda/script_inventory_baseline.json`, covered by L67/L76.

- [Pass] Decision A and the existing runtime contracts remain compatible: helpers are links in `~/.claude/hooks` and the writer/shim are generated there (plan L85-87); the shim resolves its writer through `$(dirname "$0")` (`utils/CLIO/INSTALL.md:239-245`) and the exporter resolves `clio-store.py` identically (`utils/CLIO/prompt-log-to-md.sh:25-29`). The tailer plist paths are consequently preserved (`utils/CLIO/INSTALL.md:713-737`).

- [Pass] The plan explicitly provides all required operator verbs without extra machinery: read-only `status`, idempotent `install` with `repair`/`upgrade` aliases, and preview-gated `uninstall` (plan L82-84); the suite exercises the aliases and Mac-only launchd boundary, including absent-ZCode non-creation (plan L101-110). Linux is outside the stated Mac/launchd operational envelope. No unrelated pre-existing defect was found in the swept plan.

- [Nit] Cases 8 and 7 are displayed out of numerical order (plan L109-110). Reorder them when implementing for readability; this does not affect coverage or the verdict.

VERDICT: PASS
Basis: The plan now meets the settled installer, rename, deployment, safety, and bounded-verification requirements with proportionate machinery. The only remaining note is presentational.

relay closed (Approved), no further turn needed

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
