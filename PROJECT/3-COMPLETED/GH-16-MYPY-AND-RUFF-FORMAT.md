---
gh_issue: 16
source: https://github.com/HiQS-Suite/rebalanceOS/issues/16
title: "Add type checking (mypy) and formatting (ruff format) — the remaining two-thirds of the lint gap"
status: "Completed — shipped as PR #21 (0.69.9): mypy + ruff format + CI typecheck job; issue #16 closed"
created: 2026-08-16
updated: 2026-08-16
owner: noel
doc_type: tooling
related: "GH-298 (old repo) · PR #12 (ruff lint gate) · GH-18 (CommandCode eval)"
goal: >
  Close the remaining tooling gaps identified in the code quality review: establish a gradual
  type checking gate using mypy (baseline resolved without blanket ignores) and adopt ruff format
  for universal repository code formatting without adding extraneous runtime dependencies.
effort: 2
complexity: 2
risk: 1
phases: 4
ratings_provisional: false
roadmap_exempt: false
---

# GH-16 — Tooling: Type Checking (mypy) and Formatting (ruff format)

## Overview & Background

The 2026-08-15 code-quality review gave tooling a grade of **C**:
> *"No ruff, no mypy, no formatter — dev extra is pytest only. At 95k LOC this is the biggest cheap miss."*

The linting half landed with PR #12 (GH-298 Phase R), establishing `ruff check` in CI and resolving baseline findings. This project resolves the remaining two-thirds:
1. **Type Checking**: Adopting `mypy` with gradual typing configuration (`[tool.mypy]` in `pyproject.toml`), clean baseline resolution, and a GitHub Actions CI `typecheck` job.
2. **Code Formatting**: Adopting `ruff format` across the codebase (`src`, `scripts`, `tests`, `utils`), isolating formatting in a standalone commit recorded in `.git-blame-ignore-revs`, and checking formatting in CI.

---

## Status

| Phase | Description | Status | Notes |
|---|---|---|---|
| **Phase 0** | Spike & error census on `src/rebalance` | **Done** | Found 2 parser syntax backslash issues (`web.py:415`, `web_components.py:565`). Baseline typing errors categorized. |
| **Phase 1** | Mypy integration & baseline resolution | **Done** | `mypy>=1.11` in `dev` extra, `[tool.mypy]` in `pyproject.toml`, clean `src/` resolution, CI `typecheck` job. |
| **Phase 2** | `ruff format` adoption & blame ignore | **Done** | Dedicated format commit (`f78caa1`), `.git-blame-ignore-revs`, CI `ruff format --check .` step. |
| **Phase 3** | Documentation, Versioning & QA | **Done** | Version bump to `0.69.9`, `CHANGELOG.md` entry, full pytest + HiQS isolation suite green. |
| **Phase 4** | PR & Evaluation Grade | **Done** | Rebased cleanly onto main (#18-#20), PR #21 updated, evaluation posted to issue #16. |

---

## Phase 0 — Spike & Error Census

Initial error census command:
```bash
uvx mypy src/rebalance --python-version 3.12 --ignore-missing-imports --no-strict-optional --no-check-untyped-defs
```

### Key Spike Findings
1. **F-string syntax backslashes**:
   - `src/rebalance/web.py:415`: `f"{html.escape(r['task_text']) or '<em style=\"color:var(--fg-dim)\">—</em>'}"`
   - `src/rebalance/web_components.py:565`: `f'<li{" class=\"active\"" if key == active else ""}>'`
   - *Resolution*: Extract string literal/class logic before string interpolation to maintain clean AST across all parser implementations.
2. **Census distribution**:
   - SQLite `Row` indexing & dynamic dictionary access in `ingest/`.
   - Typer CLI command signature handling.
   - Third-party library import boundaries (`mlx`, `sqlite-vec`, `google-api-client`).
3. **Decision**:
   - Go with `ignore_missing_imports = true` globally for third-party libs.
   - Use targeted `# type: ignore[<code>]` with inline explanatory comment for structural dynamic SQLite / duck-typing rows; no blanket ignores.

---

## Phase 1 — Mypy Integration

1. Add `mypy>=1.11` to `pyproject.toml` `[project.optional-dependencies] dev`.
2. Add `[tool.mypy]` configuration:
```toml
[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
no_implicit_optional = false
warn_unused_ignores = true
warn_redundant_casts = true
exclude = [
  "macOS",
  "vscode-extensions",
  "temp",
  "ask_self",
  "experimental",
  ".swe-diagram",
]
```
3. Resolve baseline errors across `src/rebalance`.
4. Add GitHub Actions CI job in `.github/workflows/ci.yml`:
```yaml
  typecheck:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install mypy
        run: pip install mypy
      - name: Type check
        run: mypy src/
```

---

## Phase 2 — Ruff Formatting

1. Format code tree:
   ```bash
   ruff format src scripts tests utils
   ```
2. Commit format changes independently:
   ```bash
   git commit -m "style: apply ruff format to src, scripts, tests, utils"
   ```
3. Create `.git-blame-ignore-revs` containing the format commit hash so `git blame` is unpolluted.
4. Add `ruff format --check .` to the `lint` CI job in `.github/workflows/ci.yml`.

---

## Phase 3 — Verification & Repo Conventions

1. **Version bump**: `0.69.6` -> `0.69.7` in `pyproject.toml`.
2. **CHANGELOG.md**: Add plain language entry under `## [0.69.7] - 2026-08-16`.
3. **Test Suite Verification**:
   - `python -m pytest tests/ utils/3-eyes/tests -q`
   - `python -m pytest HiQS/tests -q`
   - `python -m three_eyes.dashboard --check` (in `utils/3-eyes`)
   - `ruff check .`
   - `ruff format --check .`
   - `mypy src/`

---

## Phase 4 — Autonomous Execution & Review Logistics

- **Harness & Model**: CommandCode CLI (`cmd`) with `qwen/qwen3.7-flash` via `--tools-all --yolo -t`.
- **Isolation**: Executed in dedicated standalone clone folder.
- **Orchestration**: Antigravity orchestrates, verifies all diffs, ensures quality assurance standards.
- **Delivery**: Push branch `feat/gh-16-mypy-ruff-format`, open PR to `main`, tear down clone folder, post evaluation comment on Issue #16.
