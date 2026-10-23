---
gh_issue: 358
source: https://github.com/HiQS-Labs/rebalanceOS/issues/358
title: "CLIO VS Code extension: npm audit — markdown-it ReDoS (runtime) + 11 build-tool advisories"
status: "Implemented — awaiting final QA and PR"
created: 2026-10-23
updated: 2026-10-23
owner: noel
doc_type: bugfix
goal: >
  Clear the 12 npm audit findings in vscode-extensions/clio with non-breaking upgrades, so the one
  runtime dependency (markdown-it) is no longer exploitable by crafted markdown.
---

# GH-358 — CLIO extension npm audit

## Why

`npm audit` in `vscode-extensions/clio` reports 12 findings (11 high, 1 moderate). Only `markdown-it`
<= 14.3.2 ships in the extension: four quadratic-time DoS advisories, where crafted markdown can stall
the extension host. The rest are packaging and lint tooling. Every finding reports a fix as available.

## Rating rationale (2026-10-23)

`rated 45/35/50/85`. Severity 35: a local, single-user extension, and the worst case is a stalled editor
on crafted markdown, with no data loss. Priority 45: the user requested it alongside the
GithubCLIExtractor scan fix. Appeal 50 (neutral). Effort 85: a lockfile-only, non-breaking fix is
expected. Recurrence: no prior npm-audit issue for this extension (searched 2026-10-23).

## Plan

Simple change (lockfile bump via `npm audit fix`, no `--force`), so it skips plan QA; final QA still applies.
1. `npm audit fix` in `vscode-extensions/clio` → verify `npm audit` and `npm audit --omit=dev` both report 0.
2. Rebuild, lint, test and package with the extension's own `package.json` scripts; then smoke-load the built bundle.
3. Commit the lockfile (and `package.json` only if the ranges changed).

## Result (2026-10-23)

- `npm audit fix` (non-breaking): `markdown-it` 14.3.0 → 14.3.3 (runtime), plus 5 tooling bumps → `npm audit --omit=dev` = 0.
  Six high findings remained, all through `@vscode/vsce` 3.9.2 → secretlint → globby → fast-glob → micromatch →
  `braces`, whose latest release (3.0.3) is itself in the GHSA-vfj7-8cjw-p6xm range.
- **Deviation from "no `--force`":** bumped devDependency `@vscode/vsce` `^3.3.0` → `^4.0.0` (semver-major, packaging
  tool only, not shipped). This follows the extension README's own policy ("tools with no runtime presence ... track
  latest"). Result: `npm audit` = 0. vsce 4 requires Node >= 22, so packaging needs Node 22+ (local v22.22.3);
  no CI builds this extension.
- Gates before/after: `check`, `lint`, `test` (14/14), `build:prod` all rc 0; `npm run package -- --allow-missing-repository`
  produced `sidebar-markdown-0.2.1.vsix` with vsce 4.0.0. Evidence: `TESTS-RESULTS/2026-10-23+GH-358/`.
