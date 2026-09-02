---
gh_issue: 144
source: https://github.com/HiQS-Labs/rebalanceOS/issues/144
title: "GH-144 Phase 0 protocol — measured CI lane spike"
status: "Protocol v1.1 — amended 2026-09-01 after independent review (Codex + agy), pre-run"
created: 2026-09-01
owner: noel
doc_type: protocol
goal: >
  Measure the incumbent CI test job and the four candidates from issue #144 on
  the same commit and executed-test inventory, and publish the campaign under
  TESTS-RESULTS/2026-09-01+GH-144/ before any workflow change or speedup claim.
effort: 2
complexity: 2
risk: 1
phases: 1
ratings_provisional: false
---

# GH-144 Phase 0 — measured CI lane spike protocol

## TOC

1. [Question and decision rule](#1-question-and-decision-rule)
2. [Constraints inherited from prior issues](#2-constraints-inherited-from-prior-issues)
3. [Provenance and environments](#3-provenance-and-environments)
4. [Candidates under comparison](#4-candidates-under-comparison)
5. [Metrics](#5-metrics)
6. [Run matrix](#6-run-matrix)
7. [Inventory pinning](#7-inventory-pinning)
8. [Witnessed-red negative controls](#8-witnessed-red-negative-controls)
9. [Publication plan](#9-publication-plan)
10. [Pre-declared threats to validity](#10-pre-declared-threats-to-validity)
11. [Checklist](#11-checklist)
12. [Deviations and amendments](#12-deviations-and-amendments)

This protocol is **frozen before any measurement number is generated** (SOP §3.1).
It was independently reviewed before any run (Codex + agy, 2026-09-01, transcripts
in the campaign `qa/`); v1.1 incorporates their blocking findings via dated
amendments in §12. Post-run deviations remain permitted only with a dated §12 note
and a matching entry in the campaign `SUMMARY.md`.

## 1. Question and decision rule

**Question.** Which is the least complex change to the CI test lane that materially
reduces the required PR critical path **without** changing the executed test
inventory or the failure semantics?

**Decision rule (frozen, v1.1).** Candidates are evaluated **cumulatively** in the
issue's fixed order (C1 → C4; each includes its predecessors' changes), and the
first candidate satisfying **all** of D1–D4 is the recommendation. Ties or ambiguous
outcomes resolve to the simpler candidate (fewer jobs, fewer moving parts).

- **D1 — material.** Reduces the **CI-side** per-Python test critical path by ≥ 20 %.
  The critical path of a candidate = `max(job wall time)` over all jobs the
  candidate makes required, **per Python version**, measured on GitHub runners
  (§3, source S2). The reduction must hold on **both** 3.12 and 3.13; a regression
  on either Python fails the candidate. The ≥ 20 % threshold ties to the operator's
  feedback-time target: the test job is the long pole of a PR check run, and a
  sub-20 % cut is within run-to-run noise observed on the incumbent (recorded in
  the campaign) and not worth a structural change.
- **D2 — inventory-preserving.** The **exact-once union** of executed test nodes
  across all lanes a candidate makes required equals the incumbent's executed set,
  per suite, per Python: every incumbent-executed node executes exactly once with
  the same outcome class (pass/fail/skip/xfail), zero additions, zero omissions,
  zero outcome flips (§7). Zero new failures.
- **D3 — witnessed-red.** Every lane a candidate makes *required* has a
  green→red→green negative control with retained evidence: pre-green console,
  mutation diff, red exit code + failing node, post-revert green (§8).
- **D4 — isolation-preserving.** The HiQS suite still runs in its own pytest
  process (#7). No candidate may merge the two suites into one process.

Local-macOS timings (source S1) feed **feasibility, structure, and determinism**
only — never D1. No cross-source ratio is claimed anywhere.

Results that would embarrass the current design, recorded so they cannot be
rationalised away: HiQS suite failing in a root-free venv (kills C2, indicts
HiQS's standalone claim); root suite failing without the HiQS package installed
(kills C2's root lane, indicts package hygiene); root suite failing collection
without the embeddings extra beyond the enumerated seam set (kills C3); xdist
changing the executed set or failing tests that pass serially (kills C4 until
serial exclusions are enumerated and measured).

If no candidate clears D1–D4, the incumbent stands and Phase 0 publishes that.

## 2. Constraints inherited from prior issues

- **#7** — real cross-package state leak; HiQS suite must stay a separate pytest
  process. Binding on all candidates.
- **#67** — tests whose results depended on invoking cwd (fixed 0.70.0, but the
  *class* of host/global-state coupling is why C4 needs determinism evidence, not
  just speed).
- **#127** — clean-clone install contract; the *literal* incumbent install
  sequence (below) is mirrored verbatim locally, starting
  `python -m pip install --upgrade pip`.
- **3-Eyes** — deferred; nothing here runs, repairs, or references its tests.

## 3. Provenance and environments

| Item | Value |
|---|---|
| Commit | `8f733ce` (origin/development at campaign start; re-recorded per record and per CI run) |
| S1 — local | macOS arm64 operator machine, Homebrew CPython 3.12 / 3.13 (exact patch versions recorded per run) |
| S2 — CI | GitHub Actions, `ubuntu-latest`, via a **spike branch** workflow (§4.1); job timings from the Actions API, exact SHA |
| Working tree | pristine single-branch clone at the pinned commit; suites always invoked from repo root |

Two evidence sources, stated separately and never blended:

- **S2 (authoritative for D1 and all wall-time claims).** A throwaway measurement
  workflow on branch `spike/gh144-phase0-lanes` (never merged; deleted after the
  campaign) runs each candidate as complete jobs — checkout, Python setup, pip
  upgrade, cache restore/save where applicable, installs, git identity, suites —
  mirroring the incumbent `test` job step-for-step. Three samples per
  configuration via workflow re-runs on the same SHA. Historical incumbent
  timings from `development` runs are **contextual** (different SHAs), never
  decision inputs.
- **S1 (authoritative for feasibility gates, structure, determinism).** Cold/warm
  install decomposition, collection, per-suite durations, inventory evidence,
  xdist determinism, command-level witnessed-red. Absolute values are
  platform-proxies (§10).

## 4. Candidates under comparison

All commands run from the repo root. **Cumulative:** C2 includes C1's caching, etc.

- **C0 — incumbent (baseline).** One venv per Python, mirroring
  `.github/workflows/ci.yml` `test` literally:
  1. `python -m pip install --upgrade pip`
  2. `pip install --index-url https://download.pytorch.org/whl/cpu torch`
  3. `pip install -e ".[calendar,server,embeddings]" pytest`
  4. `pip install -e HiQS/`
  5. git identity config (as the incumbent step does)
  6. `pytest tests/ -q` then `pytest HiQS/tests -q` (separate processes)
- **C1 — pip caching only.** C0 + an Actions cache on the pip cache dir, keyed on
  `pyproject.toml` + `HiQS/pyproject.toml` + Python version. S1 sizes the prize
  (cold `--no-cache-dir` vs warm); S2 measures it for real (first run = miss,
  re-runs = hit; hit state recorded per job).
- **C2 — HiQS job split.** Two jobs per Python. Root lane: C0 steps 1–3 + 5–6
  (root suite only; **HiQS not installed** — the feasibility gate both ways).
  HiQS lane: fresh environment, `python -m pip install --upgrade pip`,
  `pip install -e HiQS/ pytest`, git identity, `pytest HiQS/tests -q`. Gates:
  HiQS suite green with no root package and no torch; root suite green with no
  HiQS package installed.
- **C3 — embeddings seam lane.** Only if S1 enumerates a clean seam set (below).
  Root lane venv drops the embeddings extra: step 3 becomes
  `pip install -e ".[calendar,server]" pytest`; the root lane **excludes the seam
  files explicitly** (`--ignore=<seam file>` per file). Embeddings lane: C0
  install + `pytest <seam files> -q`. Gate (from the issue): the remaining root
  suite **collects and passes** with the extra absent — zero failures, not
  "failures confined to the seam". D2 then requires the root+seam union to equal
  the incumbent executed set exactly once. If any failure falls outside the seam
  files, or the union is not exact-once, C3 dies (recorded, not patched around).
- **C4 — pytest-xdist.** Root suite with `-n 2` then `-n 4`, `--dist load`
  (pytest's default; stated because it is a behavioral choice), HiQS unchanged
  (D4). `pytest-xdist` installed explicitly in the lane. Gate: exact-once
  executed-set equality and zero outcome flips vs C0 serial on both Pythons
  across all repeats. If any test fails under xdist while passing serially, C4
  only proceeds as **C4b** — a serial-exclusion scheme (`-m "not serial" -n N`
  plus a serial `-m serial` pass), which itself must pass the same gate — and
  the scheme's added complexity counts against the simplicity tiebreak.

### 4.1 CI spike workflow (source S2)

Branch `spike/gh144-phase0-lanes`, workflow `phase0-measure.yml`, `on: push` for
that branch only. Jobs (each × {3.12, 3.13}): `c0-incumbent` (no cache),
`c1-cache`, `c2-root` + `c2-hiqs` (both cached), `c3-root-noembed` +
`c3-embed-seam` (present only if the S1 gate passed; pushed as a second commit so
the first push measures C0–C2 untainted), `c4-xdist-n2`, `c4-xdist-n4`. Job steps
mirror §4 exactly, including the incumbent's git-identity step; each job uploads
its pytest JUnit XML + `pip freeze` as artifacts. Three samples via two full
workflow re-runs on the same SHA. The branch is not merged and is deleted after
the campaign; `ci.yml` itself is untouched for the whole campaign.

## 5. Metrics

Per run record (JSONL primitive, `schema_version: 1`, one line per measurement):

`run_id`, `cell` (matrix id), `candidate`, `lane`, `python` (exact version),
`platform`, `evidence_source` (S1/S2), `commit`, `argv` (exact), `cwd`,
`started_at`/`ended_at` (UTC), `wall_s`, `exit_code`, cache hit/miss state
(S2), `pip_freeze_path` + sha256 (S1 venvs / S2 artifacts), counts
(collected/passed/failed/skipped/xfailed/xpassed/deselected/errors),
`junit_path` + sha256, `console_path` + sha256, `runner` (S2: runner name;
S1: host model), `run_index`, notes.

- Setup decomposition (S1): `wall_s` per install step, cold (`--no-cache-dir`,
  fresh venv) and warm (populated cache), 3 runs each.
- Collection: `pytest --collect-only -q` wall time, collected count, exit code.
- Suite runs: `-q --durations=50` + `--junitxml`; console retained verbatim.
- S2: job wall time from the Actions API (`started_at`/`completed_at`), plus
  per-job totals of billed runner-minutes per candidate (cost is reported
  alongside D1 even though D1 decides on critical path only).

Reporting: median and min–max spread per cell; p90/max retained in the primitive.
No mean-only reporting.

## 6. Run matrix

| # | Cell | Source | Python | Runs |
|---|---|---|---|---|
| M1 | C0 install cold (`--no-cache-dir`, fresh venv), per-step | S1 | 3.12, 3.13 | 3 each |
| M2 | C0 install warm (fresh venv, populated cache), per-step | S1 | 3.12, 3.13 | 3 each |
| M3 | Collection per suite (+ node list + hash, §7) | S1 | 3.12, 3.13 | 3 each |
| M4 | C0 root suite | S1 | 3.12, 3.13 | 3 each |
| M4b | C2 root lane: root-only venv (no HiQS installed), root suite | S1 | 3.12, 3.13 | 3 each |
| M5 | C0 HiQS suite (incumbent venv) | S1 | 3.12, 3.13 | 3 each |
| M6 | C2 HiQS lane: HiQS-only venv (no root pkg, no torch), install + suite | S1 | 3.12, 3.13 | 3 each |
| M7 | C3 probe: root suite without embeddings extra → enumerate seam set; gate = remaining suite green with seam files `--ignore`d | S1 | 3.12, 3.13 | 3 each |
| M7b | C3 seam lane: C0 install + `pytest <seam files>` (only if M7 gates cleanly) | S1 | 3.12, 3.13 | 3 each |
| M8 | C4 root suite `-n 2 --dist load` | S1 | 3.12, 3.13 | 3 each |
| M9 | C4 root suite `-n 4 --dist load` | S1 | 3.12, 3.13 | 3 each |
| M10 | Witnessed-red controls (§8) | S1 (+S2 job-level) | 3.12 | 1 per lane |
| M11 | S2 spike workflow job timings (C0–C4 complete jobs, same SHA) | S2 | 3.12, 3.13 | 3 (initial run + 2 re-runs) |
| M12 | Incumbent historical job timings from `development` — **contextual only** | S2 API | 3.12, 3.13 | last ≥ 10 completed runs |

Suites run sequentially on S1 — never two pytest processes at once — so timings
are uncontaminated. S1 candidate cells run in fixed order C0 → C4; interleaving
was considered and dismissed (§12 A11) because S1 timings no longer feed D1.

## 7. Inventory pinning

For each suite × Python × candidate/lane:

1. **Node list, fail-closed.** `pytest --collect-only -q <suite>` → the full
   sorted node-ID list is saved as a file **and published** (not just a hash);
   its sha256 is recorded. Collection exit code recorded; a non-zero collection
   marks the cell invalid rather than hashing partial output.
2. **Runtime outcomes.** Per-test `nodeid` + outcome from the run's JUnit XML.
3. **D2 check.** Exact-once multiset union of executed nodeids across a
   candidate's required lanes == incumbent's executed set for that suite and
   Python, with outcome classes compared node-by-node. Aggregate counts alone
   never satisfy D2 — swapped skips/xfails or duplicated seam tests would hide
   there.

## 8. Witnessed-red negative controls

One per lane a candidate would make required. Each control retains: pre-mutation
green console (from the matrix runs), the mutation diff (`assert False` injected
into one test in the lane's scope), the lane command's red exit code + failing
node, and the post-revert green console. Lanes:

- Root lane (`pytest tests/ -q`) — covers C1–C3.
- HiQS lane (`pytest HiQS/tests -q` in the C2 venv) — proves the split lane
  cannot silently pass while its suite is broken.
- Embeddings seam lane (if C3 survives §4's gate) — same procedure on a seam test.
- xdist root lane (`pytest tests/ -q -n 4`) — proves a worker-routed failure
  still fails the lane, and that the same mutation fails serially (equivalence).

Command-level controls run on S1/3.12 (routing is structural). S2 adds one
job-level control: a failing test pushed to the spike branch makes the
corresponding spike job red in Actions (screenshot/API record retained). The
final *required-check* routing proof on a real PR belongs to implementation,
not Phase 0 — stated explicitly so D3 is not overclaimed.

## 9. Publication plan

`TESTS-RESULTS/2026-09-01+GH-144/`:

- `SUMMARY.md` — header block, headline table, findings, threats to validity.
- `runs.jsonl` — the primitive (§5 schema).
- `inventory/` — per-suite node-ID lists + sha256 (fail-closed artifacts).
- `console/` — raw console per cell, `--durations=50` included, secrets-scrubbed.
- `scripts/` — the runner scripts as executed (S1) and the spike workflow (S2).
- `qa/` — protocol review transcripts verbatim (Codex + agy + reconciliation).
- `ci-job-timings.jsonl` — M11/M12 records with run/job URLs.

Progress is filed to issue #144 at protocol-freeze, after S1 gates, and at
publication.

## 10. Pre-declared threats to validity

- **Platform proxy (S1).** macOS arm64 ≠ ubuntu-latest x86_64 (wheel sizes, I/O,
  core count). Mitigated: D1 decides on S2 only; S1 claims are structural.
- **S1 pip cache warmth** is the operator's daily cache, not a pristine Actions
  cache restore; first post-key-change CI run is necessarily a miss. C1's S1
  numbers size the prize; the claim rides S2's miss→hit A/B.
- **Shared host (S1).** Background processes add noise; medians over 3 runs with
  min–max spread reported, runs sequential. Fixed candidate order (not
  interleaved) can drift with cache warmth — accepted because S1 no longer
  feeds D1.
- **S2 runner variance.** GitHub runner specs drift; 3 same-SHA samples with
  spread reported; ≥20 % threshold sized against observed incumbent spread.
- **Witnessed-red on 3.12 only** (S1) — assumes failure routing is not
  interpreter-specific; S2 job-level control also runs one Python only.
- **Spike jobs are not a real PR check** — no required-check routing, no
  concurrency with other jobs. D3's Actions-level claim is limited to
  "job goes red"; the required-check proof is deferred to implementation.
- **Not measured:** runner queue time, artifact upload time (recorded, included
  in job wall time), lint/typecheck/docs jobs (unchanged by this issue),
  HiQS-under-xdist (out of scope: process boundary + small suite).

## 11. Checklist

- [x] Protocol reviewed by independent reviewers before any run (SOP §3.3) — Codex + agy, 2026-09-01, `qa/`
- [x] M1–M5 incumbent + M4b measured, both Pythons (S1)
- [x] M6 C2 feasibility both directions + timings
- [x] M7/M7IGN/M7b C3 gate: seam set enumerated (2 files / 4 nodes), root green without extra, union exact-once
- [x] M8–M9 C4 xdist executed-set equality + timings (no serial exclusions needed)
- [x] M10 witnessed-red, one per surviving lane + routing control (S1); S2 job-level red→revert→green
- [x] M11 S2 spike workflow run 3× on same SHA (C0–C2/C4 @ `06e2380`; c3 jobs @ `345298d`); M12 contextual pull
- [ ] Spike branch deleted (done at publication close-out)
- [x] Campaign published under `TESTS-RESULTS/2026-09-01+GH-144/`
- [x] Recommendation + evidence linked in issue #144; no workflow changed

## 12. Deviations and amendments

All amendments below were made **before any measurement ran**, following the
independent review (transcripts in `qa/`); they are recorded for audit, not as
post-hoc rationalisations.

- **A1 (2026-09-01, Codex #1 + agy #1).** D1 re-anchored to CI-side (S2)
  measurement only; candidates get complete end-to-end jobs on a spike branch
  (§4.1). Local timings demoted to feasibility/structure evidence.
- **A2 (2026-09-01, Codex #2 + agy #5).** D1 made unambiguous: cumulative
  candidates, `max(job wall)` per Python, both Pythons must clear ≥20 %, ties →
  simpler; threshold tied to observed incumbent noise.
- **A3 (2026-09-01, Codex #3).** M1 and M7 raised to 3 runs each; M11 samples via
  same-SHA workflow re-runs; M12 relabelled contextual, non-decision.
- **A4 (2026-09-01, Codex #4 + agy #2/#3).** C3 rewritten: gate is *green*
  remaining root suite (explicit `--ignore` of seam files), seam lane added as
  M7b, exact-once union required.
- **A5 (2026-09-01, agy #4).** M4b added: C2 root lane proven in a root-only
  venv (no HiQS installed), both feasibility directions measured.
- **A6 (2026-09-01, Codex #5).** C4 spec: explicit `pytest-xdist` install,
  `--dist load` stated, C4b serial-exclusion scheme defined with its own gate.
- **A7 (2026-09-01, Codex #6).** D2 upgraded from hash+counts to exact-once
  node-level union with outcome-class comparison (§7.3).
- **A8 (2026-09-01, Codex #7).** Collection made fail-closed: exit code recorded,
  node-ID list published as a file, not just a checksum.
- **A9 (2026-09-01, Codex #8).** Clean-clone contract enforced literally:
  `pip install --upgrade pip` first, git-identity step, per-venv `pip freeze`
  retained, exact incumbent argv.
- **A10 (2026-09-01, Codex #9/#10).** Witnessed-red evidence chain and primitive
  schema fully specified (§5, §8); S2 job-level control added; required-check
  routing explicitly deferred to implementation.
- **A11 (2026-09-01, Codex optional #1 — dismissed with reason).** S1 candidate
  interleaving not adopted: S1 timings no longer feed D1 (A1), and interleaving
  would double the matrix cost for a decision it can no longer affect.
- **A12 (2026-09-01, Codex optional #2/#3 adopted in part).** Billed
  runner-minutes per candidate and cache miss/hit/restore states recorded;
  local cache-restore granularity (S1) not measured — S2 carries it.
- **A13 (2026-09-01, coordinator).** Local torch install deviates from the
  incumbent's `--index-url …/whl/cpu` (that index does not serve macOS arm64
  wheels for the pinned versions); S1 installs torch from PyPI, S2 uses the
  incumbent's exact index. Recorded so the S1/S2 install-step numbers are not
  compared cross-source.

Post-run deviations (recorded 2026-09-01/02 at publication; raw records retained as-is):

- **P1.** M1 `c0` py3.12 cold run 3, install step 1 hit a transient DNS failure
  (`files.pythonhosted.org` unresolvable); the `exit_code: 1` record is retained
  and excluded from aggregates, leaving cold py3.12 steps 2–4 at n=2. The driver
  was made idempotent (`already_recorded`) to resume without duplication.
- **P2.** The first `parse_junit` mangled class-based nodeids (junit omits the
  `file` attribute; the fallback derived `module/Class.py::test` instead of
  `module.py::Class::test`). Counts were unaffected and comparisons were
  internally consistent, but the maps were not comparable with the
  `--collect-only` node lists. Fixed, and **all** outcome maps regenerated
  deterministically from the retained junit files (`scripts/regen_outcome_maps.py`);
  the audit chain is junit (sha256 recorded at run time) → script → map.
- **P3.** M7b's first six invocations crashed on an unsplitt `--paths` argument
  (TypeError, no measurement generated); fixed, then M7b ran clean ×6.
- **P4.** `M7IGN` (root-without-embeddings with seam files `--ignore`d — the
  issue's literal gate sentence) ran as an explicit cell rather than being
  folded into M7 as §6 implied.
- **P5.** S2 run 1 (`0530d50`) was invalidated as a measurement by the repo's
  own machine-local-path ratchet firing on the campaign's committed QA
  transcripts — correct guard behaviour, instrumentation lesson recorded.
  Decision samples: C0–C2/C4 at `06e2380`, c3 jobs at `345298d`; the test tree
  is identical across those SHAs (workflow-file-only delta, disclosed here).
