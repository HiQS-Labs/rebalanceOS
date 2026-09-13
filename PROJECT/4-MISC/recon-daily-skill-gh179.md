# Recon Map — `/daily` skill (GH-179 / PR #180)

Commit: `9813d8bec47bbed54018aa74ce59aca7f825fe0e` (PR #180 head; merged into `development` as `e00c608`, 2026-09-05) · Mode: grep+read on full clone `~/Documents/GH Repos/gh179-daily-coaching-reminders` (knowledge graph not used — PR branch not indexed; every edge below confirmed by direct file read) · Lanes: A+B+D via one read-only sub-agent, C (contracts) + ground-truth log audit in main context

## Subject and change class

- **Subject**: `.agents/skills/daily/SKILL.md` — the `/daily` agent skill spec — plus its plan doc `PROJECT/2-WORKING/GH-179-DAILY-COACHING-REMINDERS-PLAN.md`.
- **Change class**: spec/contract change wearing a docs-only diff. The "runtime" it changes is LLM behavior: which signals are read each 15-minute cycle, and what deterministic artifacts get appended to `temp/daily-log/`.

## The seams — where a change here escapes these files

| Seam | Location | Crosses | Breaks if |
|---|---|---|---|
| Log-entry schema | SKILL.md:96–111 | LLM writers → next cycles' retro/trajectory reads of `temp/daily-log/YYYY-MM-DD.log` | Header strings drift; exactly-once greps (`🌅 Yesterday's Arc`, `📅 Weekly Operational Horizon`) stop matching |
| Exactly-once predicates | SKILL.md:65,68 | 5 synced agent runtimes share one unversioned log file | Two agents' first cycles of the day both read "absent" → duplicate retro/horizon |
| Extractor API | SKILL.md:46 → `apple_reminders.py:491` (`extract_apple_reminders`), field `is_completed` at `:121` | skill spec → Python API | Rename/signature change orphans the spec silently (nothing tests the spec) |
| Collector registry | `index_ops.py:2193` — `apple_reminders` registered, opt-in (`included_in_all=False`) | orchestrator-owned refresh vs the skill's direct per-cycle extractor call | Bypass drift: skill never inherits collector refresh/health paths |
| Machine-local parity | 5 global copies (`~/.claude`, `~/.codex`, `~/.gemini/config`, `~/.gemini/antigravity`, `~/.agents`) | repo copy → runtime copies, sync is a manual claim (PLAN.md:53–55) | Silent per-agent spec divergence; nothing in VC or CI enforces it |
| In-repo second copy | `.claude/skills/daily/SKILL.md` (real file, not symlink) | repo-internal parity | **This PR left it at the pre-PR blob `d56ba9b`** (identical to the old `.agents` content); healed post-merge by #187 |

## Call paths in

- Operator/agent says "/daily" (or a trigger phrase, SKILL.md:9–10) → LLM loads the skill and follows it. **No launchd job, hook, script, or CI step invokes it**; the log append is LLM-performed prose (SKILL.md:117). The `daily-sync` launchd job (`scripts/daily_sync.sh`) is a different system that never touches `temp/daily-log/`; so is `utils/daily_synthesis.py` (writes the Obsidian CLIO log).
- `extract_apple_reminders` production callers: the skill's instruction (SKILL.md:46) — code-wise only the collector sync path (`index_ops.py:1372–1375`, catches `AppleRemindersError`) and doctor health (`doctor.py:1250–1254`).

## State

- **Read**: `rebalance.db` — `calendar_events` (`db/schema.py:255`), `sleuth_reminders` (`sleuth_reminders.py:319`; table exists despite living outside `db/`), `apple_reminders` table when the opt-in collector has synced; CLIO prompt log; `collect.sh` output; `temp/daily-log/YYYY-MM-DD.log`.
- **Write**: `temp/daily-log/YYYY-MM-DD.log`, append-only, written by the LLM only. `/temp` gitignored (`.gitignore:4`). **No retention/rotation** — daily-log files accumulate unbounded (only `temp/logs/` launchd logs have pruning).
- **Apple store**: read-only file-copy snapshot is the module's load-bearing invariant (`apple_reminders.py:60–70`); TCC denial / non-macOS **raises** `AppleRemindersAccessError` (`:278–287`, no platform guard — non-macOS lands in the same raise). "Graceful degradation" exists only as skill prose (SKILL.md:48).

## Contracts

- **Log-entry schema** (SKILL.md:96–111) — consumer: subsequent cycles' greps — breaks if section headers change.
- **Trigger citation format** `` `[Trigger: ...]` `` (SKILL.md:72,110) — consumer: coaching falsifiability — held on day one, but the runtime already emits classes beyond the four enumerated rules (milestone commits, unclosed loops, open-PR backlog, deep-work runway — `temp/daily-log/2026-09-05.log`), so the enumeration is a floor, not the system.
- **Extractor API** `extract_apple_reminders` / `AppleReminder.is_completed` (`apple_reminders.py:491,121`) — matches the spec as of this commit.
- **Velocity scale** `Nominal / High / Very High` (SKILL.md:108) — no thresholds declared; day-one distribution 39/42 High-or-Very-High, 3 Nominal.

## Build, failure and rollback today

- CI (`.github/workflows/ci.yml`): ruff + sqlite-gateway lint, doc **link** check, full tests on 3.12/3.13 (`tests/test_apple_reminders.py` is covered). **Nothing validates SKILL.md content**; the skill spec, its four trigger rules, exactly-once gates, and log schema have zero test coverage (`check_doc_links.py` sees machine-local paths only in link targets, not prose).
- Failure mode: extractor raises on TCC/non-macOS; continuation is the LLM's job per prose. Rollback: `git revert` of the two files — docs-only, no data migration, logs unaffected.
- Plan doc's "Pytest: Passed clean" is author-claimed and vacuous for a docs-only diff — no test reads these files.

## Unknowns

| Unknown | Why it matters | What would settle it |
|---|---|---|
| CI status at `9813d8b` | Settled 2026-09-12: all nine PR #180 checks passed (docs, lint, typecheck, root-noembed 3.12/3.13, seam 3.12/3.13, and HiQS 3.12/3.13). | `gh pr checks 180 --repo HiQS-Labs/rebalanceOS` |
| Whether any runtime resolves the **in-repo** `.claude/skills/` copy (vs the global `~/.claude` one) | whether the stale in-repo copy was ever live, or is vestigial | inspect one agent runtime's skill resolution order |
| MCP surface for apple_reminders (grep of `src/rebalance/mcp/` found nothing) | whether a tool path exists beside the collector scope | enumerate the MCP tool registries in `src/rebalance/mcp/` |

## Current-state radius, one line

The `/daily` runtime across 5 agent runtimes on this machine, the unversioned daily-log corpus it writes and re-reads (retro + coaching memory), and the apple_reminders ingest chain (collector, health, doctor) all depend on what these two markdown files say.

**Verdict**: Recon complete — 6 seams, 3 unknowns, current-state radius: the /daily runtime on 5 agent runtimes plus the daily-log corpus it writes and re-reads.
