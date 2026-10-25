---
gh_issue: 364
source: https://github.com/HiQS-Labs/rebalanceOS/issues/364
title: "GH-364 CLIO runtime installer (clio-capture skill)"
status: "Working — final QA"
created: 2026-10-25
updated: 2026-10-25
owner: noel
doc_type: feature
related: "noelsaw1/noels-cross-project-tasks#52, HiQS-Labs/rebalanceOS#362, HiQS-Labs/XYZ-CLIO#16"
goal: >
  Install, repair, upgrade and remove CLIO capture on any Mac with one command that runs from the
  Skills Army–deployed copy, traces to a source revision, and needs no hand copies or edits.
roadmap_exempt: false
---

# GH-364 — CLIO runtime installer

## Status

| What was just completed | What's next |
|---|---|
| Implemented (rename `9ba7283`, installer `b1f21ec`) and verified (receipt `TESTS-RESULTS/2026-10-25+GH-364/`). | Final Codex QA, PR. |

Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/364 · Base `origin/development` e4a7abb · Clone/branch `rebalanceOS-gh364-clio-runtime-installer-2026-10-25` / `feat/<same>`.

**Rating** `rated 70/60/50/55` (calc 235), 2026-10-25:
- **Severity:** every Mac is installed by hand and drifts. The MBP 14" ran stale capture until 2026-10-24, and a drifted device silently loses or mis-filters prompt history until someone notices.
- **Priority:** the operator's next step after the upstream flip; it unblocks the #52 per-device redo.
- **Appeal:** neutral.
- **Effort:** a mechanical rename plus a new ~150-line installer and suite.
- **Recurrence:** one observed drift incident (2026-10-24); trend unknown.

## Context and decisions
The source plan is the operator-reviewed `temp/clio-runtime-installer-plan.md` (tracked on #52). These decisions are settled:
- **A. Hooks are symlinks into the deployed copy**, so a Pulse pull upgrades capture.
- **B. Skills Army HQ records a prerequisite text only.** HQ never runs the installer, and HQ is not changed.
- **C. Fleet `CLIO_MIN_PROMPT_CHARS` is 20.** It is already the writer default since XYZ-CLIO #15 / rebalanceOS #363, so the installer needs no environment management.
- **D. rebalanceOS is upstream** (done in #362/#363; XYZ-CLIO #16/#17 added the publisher).

**Folder-name constraint (traced 2026-10-25).** Skills Army HQ `intake.py` deploys a folder only when its name equals the `SKILL.md` `name` (`skill_info`/`package_info`; `NAME = [a-z0-9]+(-[a-z0-9]+)*`), and `add` has no name override. `utils/CLIO` cannot be intaken, and lowercasing it to `clio` would collide with the deployed `clio` lookup skill. **Operator choice (2026-10-25): rename `utils/CLIO` → `utils/clio-capture`**, rather than changing HQ or merging the lookup skill.

## Recon
- **Manual install today** (`utils/CLIO/INSTALL.md` "Install", "Optional: Codex/Agy capture", "Auto-sync", "Uninstall"):
  - The writer `clio-capture.sh` and the Claude shim `log-prompt.sh` are written into `~/.claude/hooks` from heredocs.
  - `clio-store.py` and `prompt-log-to-md.sh` are `install`ed there, and so are the two tailers.
  - The Claude `UserPromptSubmit` registration for `$HOME/.claude/hooks/log-prompt.sh` is added with jq.
  - A ZCode registration is added only when `~/.zcode` exists.
  - Three `com.claude.*` plists exist, all pointing at `~/.claude/hooks/<script>`.
- **The writer finds its helper via `$(dirname "$0")/clio-store.py`**, and the exporter does the same. All hook files must therefore sit together in `~/.claude/hooks`. A symlink placed there satisfies this, because `dirname "$0"` is the link's directory.
- **This Mac (live, read-only):**
  - all six hook files are regular files, plus a stray `log-prompt.sh.bak-20261001`;
  - the Claude registration is present, the ZCode registration is present with `enabled: true`;
  - the tailer plists carry `CLIO_MIN_PROMPT_CHARS=20`;
  - the exporter plist uses a device-specific note path and a **300 s** interval;
  - all three jobs are loaded.

  INSTALL.md says an existing exporter job's plist must not be rewritten. So **the installer never writes the exporter plist**; `status` only reports it.
- **Tests extract the writer and shim by marker:** `awk '/^cat > ~\/\.claude\/hooks\/clio-capture\.sh << .EOF.$/{f=1;next} f&&/^EOF$/{exit} f'`, in `test/clio-capture.sh` L18-20. The installer reuses exactly that extraction, so it creates no second copy of the writer.
- **Collection:** `${XYZ_SKILLS_ROOT:-$HOME/git-pulse-sync/Deployed Skills}`. Its tracked tree must stay clean, and only `intake.py`/`sync.py` write there. So **generated files are not written into the collection**: the writer and shim are generated straight into `~/.claude/hooks` and tracked by checksum. (This refines the plan's "runtime/ under the collection", which would dirty the Pulse tree.)
- **HQ provenance** is readable from `<collection>/.deploy-skills.json` → `skills["clio-capture"].commit`. It is read only, for the receipt.
- **Live references to `utils/CLIO`** that move with the rename:
  - `utils/CLIO/*` itself (`INSTALL.md`'s resolver candidates, `README.md`);
  - `test/clio-{capture,exporter,codex-tail,agy-tail}.sh`, `test/clio-store.py` (`ROOT/utils/CLIO/...`);
  - `AGENTS.md`, `ARCHITECTURE.md` (catalog row), `pyproject.toml` (ruff exclude);
  - `utils/pdda/check_banned_imports.py` (gateway dir), `tests/test_sqlite_gateway_ratchet.py` (docstring);
  - `utils/pdda/script_inventory_baseline.json` (via `--update-baseline`);
  - `src/rebalance/ingest/clio_journey.py` (docstring), the two Focus5 Swift comments, `.agents`/`.claude` `skills/clio/SKILL.md`.

  **Not changed:** history (`CHANGELOG.md`, `releases.sql`, `PROJECT/**` plan docs, `TESTS-RESULTS`, relay threads), and `tests/test_github_direct_commits.py` / `tests/test_github_commit_backfill.py`, whose `utils/CLIO/...` strings are fixture data from a real historical commit, not paths (plan QA R1).

## Changes
1. **Rename** with `git mv utils/CLIO utils/clio-capture` and update the live references listed above.
   - INSTALL.md's `CLIO_SRC` resolver candidates gain `utils/clio-capture` and `~/.claude/skills/clio-capture`, and `utils/CLIO` is dropped.
   - The CLIO skill copies drop the XYZ-CLIO path link (that path moves in XYZ-CLIO's follow-up) and keep the plain "also published in HiQS-Labs/XYZ-CLIO" note.
   - `--update-baseline` refreshes the inventory baseline; its diff is exactly the renamed paths plus the new `clio-runtime.sh`.
2. **`utils/clio-capture/SKILL.md`**: `name: clio-capture`, with a description ("install, repair, upgrade, check or remove CLIO prompt capture on this device"). The body covers:
   - run `status`, then `install`, then `install --apply` from the deployed folder;
   - `uninstall --apply`;
   - prerequisites (`jq`, `python3`, macOS for launchd);
   - what the installer never touches (app skill links, SQLite activation, fleet config, the exporter schedule).
3. **`utils/clio-capture/clio-runtime.sh`** (bash 3.2-compatible, `set -euo pipefail`):
   - **Commands:** `status` (default, read-only); `install` (`repair` and `upgrade` are the same idempotent converge); `uninstall`. `install`/`uninstall` preview unless `--apply`.
   - **Source guard:** the script's own resolved directory must be `<collection>/clio-capture`. Anything else (a repo checkout, a task clone) is refused with exit 2.
   - **Desired state**, where `H=~/.claude/hooks`:
     - **Links:** `H/{clio-store.py, prompt-log-to-md.sh, clio-codex-tail.sh, clio-agy-tail.sh}` → `<src>/<file>`.
     - **Generated:** `H/clio-capture.sh` and `H/log-prompt.sh`, extracted from `<src>/INSTALL.md` by the tests' marker, mode 755.
     - **Registrations:** Claude `UserPromptSubmit` → `$HOME/.claude/hooks/log-prompt.sh`; ZCode → `$HOME/.claude/hooks/clio-capture.sh --agent zcode`, only when `~/.zcode` exists. Both use INSTALL.md's own jq expressions.
     - **Plists** (macOS only): the `com.claude.clio-codex-tail` and `com.claude.clio-agy-tail` plists, created from INSTALL.md's template **only when absent**, then loaded. An existing plist is left byte-identical. The exporter plist is never created or rewritten; `status` reports whether it exists.
   - **Replacing an existing file:** a regular file or foreign symlink at an owned hook path that differs from the desired state is shown in preview. Under `--apply` it is moved to `~/.claude/clio-runtime-backups/<UTC stamp>/` before replacement, and the backup is recorded.
   - **Receipt `~/.claude/clio-runtime.json`:** source dir, HQ-recorded commit (if any), a source digest (sha256 of INSTALL.md + the four scripts), installed time, the owned paths with kind and sha, the registrations it added, the plists it created, and the backups.
   - **`status`:** one line per owned item (`ok` / `missing` / `foreign` / `stale` / `wrong-target`), plus registrations, plists (present / loaded via `launchctl list`), the exporter plist, and whether the receipt digest matches the deployed copy. Exit 0 when nothing needs install, exit 1 otherwise.
   - **`uninstall --apply`** (drift-safe, plan QA R2):
     - removes a receipt-owned path only while it still matches the receipt: a link still pointing at `<src>/<file>`, or a generated file whose sha equals the recorded sha. Only then is its backup restored;
     - a path changed since install (edited, replaced, retargeted) is left untouched and reported as `drifted`, and so is its backup. The receipt is kept with just those paths, and the run exits 1 so the operator can decide; there is no force flag;
     - removes only the registrations the receipt says it added;
     - unloads and removes only the plists it created;
     - never touches the DB, state, logs, config or the exporter plist;
     - deletes the receipt only when nothing drifted.
4. **`test/clio-runtime.sh`** (new suite; the README Tests block lists it).
   - **Setup:** a throwaway HOME and a fake collection (`XYZ_SKILLS_ROOT=<tmp>/col`) holding a copy of `utils/clio-capture`; `launchctl` is stubbed on PATH and logs its calls. Every temp dir uses guarded `mktemp` with `${VAR:?}` on cleanup.
   - **Cases, each with an observed assertion:**
     1. A fresh install: preview writes nothing; `--apply` → `status` exit 0; a prompt piped through `log-prompt.sh` lands a row; both tailer plists are created and loaded via the stub; the exporter plist is untouched and absent; with no `~/.zcode` in the throwaway HOME, none is created and no ZCode registration is written (plan QA R1).
     2. A deleted link → `status` exit 1 `missing`; `repair --apply` restores only it (all other files keep their inode/mtime).
     3. An edit to the collection copy's writer heredoc → `status` `stale`; `upgrade --apply` regenerates it; `status` 0.
     4. A pre-existing hand-made `log-prompt.sh` (red control): `install` preview names it and changes nothing; `--apply` backs it up and replaces it.
     5. `uninstall --apply` restores the hand-made file and leaves a pre-existing foreign registration and a pre-existing tailer plist in place. Only receipt-owned items are removed.
     6. Running the script from a repo path (not `<collection>/clio-capture`) → exit 2, nothing written.
     7. Rerunning `install --apply` on a converged HOME → "nothing to do", and no file changes.
     8. A drift-safe uninstall (red control for R2): after install, edit the installed `log-prompt.sh`; `uninstall --apply` exits 1, leaves the edited file and its backup in place, reports it as drifted, keeps the receipt, and still removes the unchanged items.
5. **Gates and docs:**
   - script-inventory `--update-baseline`; ruff exclude and SQLite gateway dir renamed; ARCHITECTURE catalog row path updated;
   - `utils/clio-capture/README.md` gets an "Install on a device" pointer to `clio-runtime.sh`;
   - INSTALL.md "Install" gets a one-paragraph note that `clio-runtime.sh` automates this block from a Skills Army deployment, and that the manual block remains the reference;
   - `CHANGELOG.md` and version bump (0.105.0).

## Non-goals
- No HQ change, and HQ never runs the installer.
- No intake or per-device rollout in this PR; those are #52's checklist after merge.
- No exporter-plist management; no SQLite activation, migration or fleet config.
- No XYZ-CLIO change here. A follow-up there renames its published path and updates the publisher scope.
- No scheduler and no environment management (C is satisfied by the writer default).

## Risks / rollback
- **The rename breaks a device whose hooks were installed by `CLIO_SRC` resolution from `utils/CLIO`.** Installed hooks are copies in `~/.claude/hooks`, so nothing that is running breaks. Only a future manual run of the old resolver from a checkout is affected, and the resolver gains the new candidates.
- **Symlinked hooks mean a bad publish reaches every Mac at the next Pulse pull.** This is accepted in decision A and contained by the single publisher plus reviewed PRs.
- **Rollback:** `clio-runtime.sh uninstall --apply` restores the backups. For the code, revert the PR.

## Verification
- `bash test/clio-runtime.sh`, plus the existing CLIO suites (capture, exporter, codex-tail, agy-tail, `test/clio-store.py`), run in a disposable full clone after the rename.
- **Repo gates:** ruff check/format, `check_script_inventory.py --check`, `check_banned_imports.py --check`, `pytest tests/test_consumer_catalog.py tests/test_sqlite_gateway_ratchet.py`, `pdda.sh run` (no new errors versus base), and the pre-push gate. Hosted CI on the PR.
- **Smoke (main path + rerun):** a real `install` preview and `status` on this Mac, read-only (it adopts nothing), against a temporary collection copy via `XYZ_SKILLS_ROOT`. This shows what an adoption would back up and replace. Nothing is applied to the live HOME in this PR.
- **Red controls:** suite case 4 (a hand-made file is refused without `--apply`) and case 6 (a non-collection source is refused); the inventory ratchet before `--update-baseline`.
