# RELAY · rebalanceOS GH-358 final QA (codex)
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-10-23.
-->

NEXT: Reviewer
STATUS: Open
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
6. **Commit only the relay file** (`relay(rebalanceos-gh-358-final-qa-codex): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: the change on this branch vs base `1994133`:
  `git diff 1994133..HEAD -- vscode-extensions/clio/package.json` (one devDependency range) and the lockfile
  `vscode-extensions/clio/package-lock.json`. Read it with `python3 -c` / `jq`, not line by line; the diff is a
  regenerated npm lockfile.
- Spec: issue #358 (body summarized in `PROJECT/1-INBOX/GH-358-CLIO-NPM-AUDIT.md`, including its "Result" section and
  the recorded deviation).
- Evidence: `TESTS-RESULTS/2026-10-23+GH-358/`: `audit-before.txt`, `audit-after.txt`, `audit-after-runtime.txt`,
  `gates-before.txt`, `gates-after.txt`, `smoke.txt`.
- Extension policy: `vscode-extensions/clio/README.md` (the "Pinned to / Why not latest" table, and the line saying
  tools with no runtime presence track latest).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-10-23
- **Operational envelope:** a local, single-user VS Code extension built by hand on the operator's Mac. No CI builds
  it. Grade against the issue's acceptance list with commensurate complexity; do not ask for new test machinery.
- Definition of Done (issue #358 acceptance):
  1. `npm audit --omit=dev` = 0, and `markdown-it` resolves above 14.3.2.
  2. `npm audit` = 0, or the remainder is justified.
  3. The extension still compiles, lints, tests and packages.
  4. No other directory changes beyond the plan doc, the ledger row (`releases.db`/`releases.sql`) and evidence.

### Questions for the Reviewer
1. Does the lockfile actually resolve `markdown-it` >= 14.3.3 everywhere it appears (top level and under `@vscode/vsce`)?
   Do any remaining copies sit inside an advisory range? Check `packages["node_modules/..."]` entries.
2. Is the `@vscode/vsce` ^3 → ^4 bump (semver-major, devDependency only) justified by the README policy and the
   `braces` chain (the latest `braces` 3.0.3 is itself in the GHSA-vfj7-8cjw-p6xm range)? Is anything shipped in the
   `.vsix` affected? The bundle is esbuild output of `src/extension.ts` with `vscode` external.
3. Are the `@types/vscode`, `@types/node` and `typescript` pins from the README table still honored in `package.json`?
4. Is the smoke receipt honest? Its red control did not reproduce the slowdown, and it says so. Is version-based evidence
   enough here?
5. Is anything missing or over-built? Cite file:line or lockfile keys.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
