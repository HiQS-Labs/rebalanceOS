---
gh_issue: 312
source: https://github.com/HiQS-Labs/rebalanceOS/issues/312
title: "CI/CD posture audit — ci-optimize scorecard 17/24 (B): execute Rung 1 (quarantine expiry) + Rung 2 Stage 1 (static pre-push gate)"
status: In review
created: 2026-10-03
updated: 2026-10-03
owner: noel
doc_type: architecture
goal: >
  Execute the first two shippable-now rungs of the GH-312 ladder: give the GH-178
  quarantine a UTC expiry with real return-to-gate behavior, and ship the measured
  ~2.5s static pre-push gate (ruff + grep guards + five governance ratchets) tracked
  and armed, closing the GH-259 scanning blind spot for .githooks/ in the same change.
effort: 2
complexity: 1
risk: 1
phases: 1
ratings_provisional: false
roadmap_exempt: false
---

# GH-312 — CI boundary ladder slice: quarantine expiry + static pre-push gate

## Status

| What was just completed | What's next |
|---|---|
| Spike executed 2026-10-02 against the four pre-registered gates; campaign published at `TESTS-RESULTS/2026-10-02+GH-312/`. Full-lane gate rejected (G1/G4 fail); static substrate measured (~2.5 s) and hook mechanics proven (G2/G3 pass). This plan drafted and parked. | Codex plan QA → implement Rung 1 + Stage 1 → focused suites → full gates once → final relay QA → PR. |

## Why

The GH-312 audit scored Gate boundary 1/12 and found the only local hook is "a reminder, never a gate", while hosted CI is the sole boundary. The spike proved a full-lane local gate can't win (296.6 s median vs hosted 144 s median), but the static substrate (ruff check/format + the two ci.yml grep guards + five governance ratchets) costs an estimated ~2.5 s composite from measured primitives (ruff ~0.1 s, guards sub-second, ratchets 0.07–1.13 s each — never timed as one composite command) and catches the lint/format/guard/sprawl classes instantly. Separately, the GH-178 quarantine (10 real product-bug tests xfailed non-strict since 2026-07) has no expiry — the playbook's P13 requires owner, issue, and UTC expiry with fail-on-expiration so a quarantine can't silently become permanent.

## Ratings, with reasons

| Field | Value | Why |
|---|---|---|
| `pri` | 70 | Top two items of the operator-ordered ladder on the audit issue; not blocking broken CI, but explicitly mandated next work. |
| `sev` | 55 | Process-boundary risk, not product defects: quarantine without expiry risks permanent masking (10 real bugs); no data loss or user-facing failure. |
| `appeal` | 50 | Neutral; no operator preference stated. |
| `effort` | 75 | High cheapness: the spike already built, measured, and red-controlled the hook; remaining work is ~1 h of ship + scope fix. |

Recurrence (14-day window to 2026-10-03 vs prior 14): no new quarantine entries; the GH-178 set has been stable since 2026-07 (10 entries, no growth). The gate-boundary gap recurred historically once (GH-178, July) and is now structurally closed on the hosted side; the local side is this slice.

## Phase 0 — Prior art review (why extending existing layers is the approach)

### Prior-art checks — recorded results (2026-10-03)

- **Open PRs, canonical repo:** `gh pr list -R HiQS-Labs/rebalanceOS` → #317 (CLIO docs skill), #311 (GH-310 releases scan), #301/#299 (GH-232 trials, draft), #298 (GH-296 job_guard), #294 (GH-293 docs pointers) — none touch `.githooks/`, the quarantine, or the guard. Second repo (Hypercart-Dev-Tools/rebalance-OS) is the archived predecessor per AGENTS.md; its tree was recovered into `PROJECT/4-MISC/ARCHIVED-PREDECESSOR/` and holds no live gate work.
- **ROADMAP → In progress:** no GH-312 entry existed before this slice (checked 2026-10-03; grep `312` on ROADMAP returned nothing). No parallel quarantine-expiry or pre-push campaign in flight.
- **Cross-package grep (`pre-push`, `quarantine`, hook/gate infra across `src/`, `utils/`, `HiQS/`):** only `.githooks/post-merge` (reminder-only), `utils/pdda/check_script_inventory.py` scope comment, and the GH-178 quarantine in `tests/conftest.py` — no existing pre-push gate to extend.
- **Full suite including CI-skipped parts:** not re-run for the plan (the spike ran the root lane 3× green plus HiQS green on this tree family; GH-282 verification published 2807 passed / 2026-10-02). 3-Eyes tests stay excluded per the operator stand-down.
- **Live ladder reconciliation:** the reviewer relay lacked web access; the ladder was reconciled directly against the live #312 body (consolidated post-spike checklist) and findings comment when this plan was drafted.

- **`.githooks/post-merge`** — exists, but is explicitly "a reminder, never a gate" (drift notice). Extended family: this slice adds a sibling `pre-push` file in the same directory + same `core.hooksPath` convention. Nothing new is invented.
- **Hosted `ci.yml` lint job** — runs the exact checks Stage 1 adopts (ruff, ratchets, grep guards live in the root-noembed job). The gate reuses their logic verbatim; it does not fork a second definition of "clean" (grep guards copied character-for-character; ratchets invoke the same `utils/pdda/check_*.py` scripts).
- **`tests/conftest.py` `KNOWN_FAILING_GH178` + `pytest_collection_modifyitems`** — the existing quarantine writer. Rung 1 extends it with an expiry constant and an expired→no-marker branch. No new quarantine mechanism.
- **`utils/pdda/check_machine_paths.py`** — exists; the GH-259 fix *is* an extension (add `.githooks` to `SCANNED_ROOT_DIRECTORIES`, scan extensionless files there).
- **Spike campaign** — the hook candidate, measurements, and red control already exist in `TESTS-RESULTS/2026-10-02+GH-312/`; this slice ships the measured thing, it does not design a new one.

## Scope (this slice)

1. **Campaign provenance** — commit `TESTS-RESULTS/2026-10-02+GH-312/` so the issue's evidence links resolve.
2. **Rung 1 — quarantine expiry (P13)**: `GH178_QUARANTINE_EXPIRES_UTC = "2026-11-01T00:00:00Z"` beside `KNOWN_FAILING_GH178`; `pytest_collection_modifyitems` adds the xfail marker only while `now < expiry`; past expiry the marker is withheld and the 10 tests run naked (fail red = return to gate, which is the loud signal by design). Reason strings carry `owner: noel; issue: #178; expires 2026-11-01T00:00:00Z`. Expiry check factored into a pure helper so it is unit-testable without collection tricks.
3. **Rung 2 · Stage 1 — static pre-push gate (P1)**: ship `.githooks/pre-push` **tracked + armed (mode 100755)**, static stages only — the spike candidate's 5-minute pytest stage is deliberately stripped (Stage 2 adds tier-mapped tests after Rung 3). Stages: ruff check, ruff format, the two grep guards (verbatim ci.yml logic), the five `utils/pdda/check_*.py --check` ratchets (measured 0.07–1.13 s each). Receipts JSONL to `temp/gate-receipts.jsonl` — **hardened over the candidate** (review R1): the parent dir is created (`mkdir -p`) before append; a failed receipt write prints a loud stderr line and the gate never reports "logged" when it did not; the bypass receipt records a **fixed** detail marker (the bypass value is deliberately NOT interpolated into JSON — no escaping machinery in bash). Logged bypass via `REBALANCE_SKIP_PREPUSH_GATE`; `--verify` mode; delete-only/empty-stdin noops; fail-closed on missing `.venv` python. Arming note: git only runs hooks in clones that opt in via `git config core.hooksPath .githooks`; fresh clones (including the fleet runtime checkout) are unaffected unless they install.
4. **GH-259 scope fix**: `.githooks` added to `SCANNED_ROOT_DIRECTORIES`; `should_scan` includes extensionless files under `.githooks/`; one new negative control, built per review R4: the mock repo **contains a `src/` directory** (so the real root-filtering path applies, not the flat-mock escape hatch at `should_scan`) and a **tracked, extensionless** `.githooks/pre-push` carrying a machine path; the checker must FAIL naming that path:line. Removing either the root inclusion or the extensionless allowance must make this control red. No basename exemptions are added (the checker's self-exclusion list needs no change — `pre-push` is not in it).
5. **Focused tests** (new `tests/test_pre_push_gate.py`, shell-subprocess style matching `test_stack_script.py`/`test_daily_sync_exit.py`): syntax, `--verify` disarmed→armed states (via a temp hooksPath clone), empty-stdin noop, delete-only noop, logged bypass + receipt side effect asserted, and — review R2 — **a parameterized static-failure control**: the hook gains one explicit seam, `REBALANCE_GATE_PY` (defaults to `$ROOT/.venv/bin/python`; naming follows the `RB_PYTHON` pattern of GH-289), so a stub interpreter can drive controlled per-stage exits. Tests assert: a ruff stage exiting non-zero blocks the push with the stage named in output AND receipt; a governance ratchet exiting non-zero does the same; all-green stub + one real green run (~2.5 s) produce exit 0 and a parseable receipt; receipts parse as JSONL on fresh-clone/noop/bypass paths (review R1). The stub only ever writes under `tmp_path`. Red-block behavior is NOT unit-tested — it is witnessed in the campaign's real red control (`gate-red-run1`, exit 1, "push BLOCKED").
6. **Rung 1 tests**: ~3 unit tests on the expiry helper (unexpired → marker, expired → None, far-past → None), monkeypatched clock, no collection integration tests.
7. **Ledger**: ROADMAP park → in-progress promotion after plan QA; `releases roadmap sync`; follow-up issues filed (live-API seam; GH-144 re-measure).

## Non-goals

- No full-lane pre-push gate (rejected by G1/G4 with published numbers).
- No path→tier map (Rung 3), no xdist change (Rung 4 — hosted-only decision for the operator), no flake runbook (Rung 5), no lock work (Rung 6, tracked in #282).
- No new test framework/runner; no changes to `ci.yml` in this slice; 3-Eyes stays stood down.

## Risks & rollback

- **Armed gate blocks a legitimate push** on a lint/format regression in the working tree: bypass is one env var, logged; the gate prints the failing stage and remediation. Rollback = revert the single commit (hook is inert in any clone without `core.hooksPath`).
- **Activation is automatic in ALREADY opted-in clones (review R3):** `.githooks/post-merge` already instructs operators to run `git config core.hooksPath .githooks`, so every such clone — including any unattended/scheduled pusher — picks up the executable `pre-push` on its next pull, no further action. Rollout duties before merge: (1) enumerate existing opted-in clones on the operator's machines (checked during execution; the fleet runtime checkout is a fresh clone that does not set `core.hooksPath` — verified at execution time), (2) confirm each has the static prerequisites (`.venv` python, clean lint) or accept that its push will fail closed with remediation until fixed, (3) document recovery: one-shot `REBALANCE_SKIP_PREPUSH_GATE=1 git push`, or disarm `chmod -x .githooks/pre-push`, or uninstall `git config --unset core.hooksPath`. Fail-closed stays: a soft-skip would conceal a broken gate.
- **Expired quarantine turns CI red** (10 auto_promote tests fail after 2026-11-01 if still unfixed): that is the intended P13 behavior — loud return to gate, forcing fix-or-re-quarantine with a fresh expiry. The date is chosen 30 days out so the operator sees it coming.
- **Guard scope fix flags existing files**: none expected — the five governance runs were green with the hook intent-to-add in the spike (campaign `gov-*` records); re-verified during implementation.

## Verification (bounded)

- Focused: `pytest tests/test_pre_push_gate.py tests/test_machine_path_guard.py tests/test_ci_ratchets.py` + the new quarantine-helper tests + `tests/test_auto_promote.py tests/test_project_inference.py` (must still xfail, not error, unexpired).
- Full gates exactly once on the final approved commit, in this disposable full clone (identity verified pre/post): ruff check + format, mypy `src/`, root-noembed lane + HiQS lane, doc links, five ratchets.
- Rollout prerequisite evidence: enumerate opted-in clones on this machine (launchd plist checkout paths → `git config core.hooksPath`) and record their state in the PR.
- Red control for the changed gate logic: the campaign's `gate-red-run1` (real mutation, exit 1) + the new guard negative control; no further mutation theatre in-unit.
