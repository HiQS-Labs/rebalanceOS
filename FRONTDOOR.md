# FRONTDOOR.md — onboarding health board

The front door is what a cold newcomer hits: clone → install → verified working, without
correcting stale paths, following a broken route, or reconciling metadata by hand.

Every finding below carries a **deterministic check**. Each check is written to print
**nothing** when the repo is healthy, so the whole board is one command:

```bash
bash utils/frontdoor-check.sh
```

Silence is a pass. Any output is a regression, and the line tells you which one.

Baseline: GH-44, audit commit `465aa90`, verdict *Bumpy* — seven defects, all now closed.
Re-run the board before a release; `RELEASES.md` carries a `Front-door reviewed:` gate per
release, and this is what backs that line.

---

## The checks

| # | Finding (GH-44) | What the check asserts |
|---|---|---|
| 1 | Stale clone directory | No doc tells you to `cd rebalance-OS` / `cd /path/to/rebalance-OS`. The clone is `rebalanceOS`. |
| 2 | Code Intelligence over-promise | README does not claim a committed index, "no setup", or "no API keys" — the index is gitignored and the harness needs `GOOGLE_API_KEY`. |
| 3 | `manifest.json` drift | Manifest version matches `pyproject.toml`, the repo URL is `HiQS-Suite/rebalanceOS`, and the tool list matches the registered `@mcp.tool()` surface exactly. |
| 4 | `ARCHITECTURE.md` bad refs | No links to a nonexistent root `PROJECT.md`; the license footer says AGPL-3.0-only, not Apache. |
| 5 | Credential-free checkpoint | Step 1 ends with `rebalance version` — a check needing no vault, token, or network — before any credential step. |
| 6 | Buried Getting Started | A pointer to Getting Started appears in the first 40 lines of README. |
| 7 | Incomplete egress list | The first-run egress list names `github.com`, `pypi.org`, and `files.pythonhosted.org` — the hosts Step 1 itself needs. |

## Kept green (regression guards)

These were already healthy at the audit and the board keeps them that way:

- Root `README.md` remains canonical and points to the tracked `/welcome` skill.
- `pyproject.toml` and the runtime package version stay aligned.
- `LICENSE` (AGPL-3.0-only) and `LICENSE-COMMERCIAL.md` both remain present.

## Out of scope for this board

- **Secret scanning.** TruffleHog 3.97.0 over full reachable history was clean at the
  audit (0 verified / 0 unverified). That is a separate gate — run the scanner, do not
  approximate it with grep, and never publish raw detector payloads.
- **Human gates.** Vault path, GitHub PAT, optional Google OAuth, and Apple-Silicon
  hardware are real requirements, not defects — the board never tries to remove them.
  It does assert *ordering*: each gate must be named inside the step that needs it
  (Steps 2-5), and the Apple-Silicon gate must be stated before Step 1's install. That
  is a real check, bounded per section, and it fires if a gate goes unmentioned where a
  reader would hit it.
