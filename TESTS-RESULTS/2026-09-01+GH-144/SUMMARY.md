# GH-144 Phase 0 — measured CI lane spike: campaign summary

| | |
|---|---|
| **Campaign** | `2026-09-01+GH-144` (ran 2026-09-01 → 09-02) |
| **Tracking issue** | [HiQS-Labs/rebalanceOS#144](https://github.com/HiQS-Labs/rebalanceOS/issues/144) |
| **Protocol** | [`PROJECT/2-WORKING/GH-144-CI-LANE-PROTOCOL.md`](../../PROJECT/2-WORKING/GH-144-CI-LANE-PROTOCOL.md) v1.1, frozen pre-run, independently reviewed (Codex + agy; [`qa/`](qa/RECONCILIATION.md)) |
| **Systems under test** | Incumbent CI `test` job (C0) vs C1 pip-cache, C2 HiQS job split, C3 embeddings seam lane, C4 pytest-xdist 2/4 |
| **Test tree** | `8f733ce` (origin/development). S2 decision samples: `06e2380` (C0–C2, C4), `345298d` (c3 jobs) — workflow-only delta, see protocol §12 P5 |
| **Duration** | ~4 h wall (S1 local driver ~2.5 h; S2 9 workflow executions) |
| **Output files** | `runs.jsonl` (S1+controls primitive), `ci-job-timings.jsonl` (S2), `console/`, `inventory/`, `scripts/`, `qa/` |

## Headline: the decision (D1–D4, protocol §1)

Per-Python CI critical path = `max(job wall)` over the candidate's required
jobs, median of 3 same-SHA samples, GitHub runners (source S2 only):

| Candidate | Required jobs (per py) | CP 3.12 | CP 3.13 | Cut 3.12 | Cut 3.13 | D1 (≥20 % both) | D2 exact-once | D3 red | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **C0 incumbent** | 1 serialized job | 162 s | 159 s | — | — | baseline | — | — | stands as-is |
| C1 pip cache | 1 job + cache | 150 s | 150 s | 7.4 % | 5.7 % | ✗ | n/a (same job) | ✓ | **reject** |
| C2 HiQS split | root, hiqs | 135 s | 143 s | 16.7 % | 10.1 % | ✗ | ✓ (S1+S2) | ✓ | **reject** |
| **C3 seam lane** | root-noembed, seam, hiqs | **82 s** | **74 s** | **49.4 %** | **53.5 %** | ✓ | ✓ (S1+S2) | ✓ | **RECOMMENDED** |
| C4 xdist-4 | root-n4, hiqs | 103 s | 102 s | 36.4 % | 35.8 % | ✓ | ✓ (S1+S2) | ✓ | passes, later in order |

**Recommendation: C3 — split the embeddings seam out of the root lane.**
Evaluated in the issue's fixed order, C3 is the first candidate that clears all
four gates, and by the widest margin: the required PR critical path roughly
**halves** (162→82 s on 3.12, 159→74 s on 3.13, medians). C3 is cumulative —
it subsumes C1 (all lanes cached) and C2 (HiQS in its own job). C4 (xdist-4)
also clears D1 with a ~36 % cut, zero outcome flips in 12 CI executions + 12
local runs, and **needed no serial exclusions** — it is published as the
measured next escalation if the seam-file list ever becomes a maintenance
burden, keeping the #67-class parallelism concern out of the default path.

### Why the seam lane is the whole story

The incumbent job's cost decomposes (S2 medians, 3.12): install-with-torch
~55 s + root suite ~100 s + HiQS suite+install ~25 s, serialized. Only **4
tests in 2 files** actually need the embeddings extra
(`tests/test_embedder.py::EmbedderTests` — 2 nodes — and
`tests/test_embedder_metal_unavailable.py` — 2 nodes; the other 4 nodes in
those files pass either way, and ride the seam lane). Dropping torch from the
root job halves it (135→76 s); the HiQS lane was already nearly free (24 s).
The residual critical path is the seam job itself (82 s: torch install + 8
tests). The seam split fails **closed**: a future embeddings-dependent test
landing outside the seam files turns the root lane red — it cannot be silently
skipped.

### Billed-minutes tradeoff (recorded, not decisive)

Approx. total runner seconds per Python-version pair, medians: C0 ≈ 321 s;
C2 ≈ 327 s; C3 ≈ 354 s (+10 % vs incumbent); C4 ≈ 254 s (−21 %). C3 buys ~2×
faster feedback for ~10 % more compute. Exact per-job numbers: `ci-job-timings.jsonl`.

## D2 — executed-inventory evidence (protocol §7)

Executed set of the incumbent: **2146 root + 165 HiQS = 2311 nodes** (S1:
collected == executed, byte-identical node lists; S2: junit artifacts).

| Check (vs C0, per Python) | missing | added | duplicated | outcome flips |
|---|---|---|---|---|
| C2 root lane (no HiQS installed) — S1 | 0 | 0 | — | 0 |
| C2 HiQS lane (no root pkg, no torch) — S1 | 0 | 0 | — | 0 |
| C2 union — S2 | 0 | 0 | 0 | 0 |
| C3 union (root-noembed + seam + hiqs) — S1 | 0 | 0 | 0 | 0 |
| C3 union — S2 | 0 | 0 | 0 | 0 |
| C4-n2 / C4-n4 — S1 | 0 | 0 | — | 0 |
| C4-n4 union — S2 | 0 | 0 | 0 | 0 |

The C3 seam gate (issue wording): remaining root suite **collects and passes**
without the embeddings extra — 6/6 green locally (2138 = 2146 − 8 seam nodes),
3/3 green per Python on CI; seam lane green with the extra (8/8 nodes); union
exact-once everywhere. M7 probe: without the extra, exactly 4 nodes fail, all
inside the 2 seam files, identical across 6 runs × 2 Pythons.

## D3 — witnessed-red (protocol §8)

S1 lane-level (py3.12, full evidence in `console/M10-*`): root 133 s red / 119
s post-green; xdist-n4 36 s / 34 s; HiQS 3 s / 2 s; seam 10 s / 8 s; plus the
routing control — with the mutation inside a seam file, the ignoring C3 root
lane stayed green while the seam lane went red. S2 job-level: red commit
`6db581e` failed **every** lane owning a mutated file (including `c2-hiqs` for
the HiQS mutation) while `c3-embed-seam` correctly stayed green; revert
`fcfdabb` → all 16 jobs green ([red run](https://github.com/HiQS-Labs/rebalanceOS/actions/runs/33597447023),
[green run](https://github.com/HiQS-Labs/rebalanceOS/actions/runs/33597701658)).
Required-check routing on a real PR remains an implementation-phase proof, as
the protocol pre-declared.

## S1 structural findings (local macOS, feasibility only — never fed D1)

- Cold vs warm c0 install: ~53 s → ~46 s locally (mac wheels are small; the
  real cache story is S2's 162→150 s).
- Root suite serial 134.1 s [121–147] n=6; xdist-n2 75.8 s, n4 44.1 s,
  identical 2146-node inventory, zero failures.
- HiQS suite: 7.6 s in the incumbent venv; 2.8 s in a HiQS-only venv — HiQS is
  genuinely standalone (also proven on CI in both directions).
- The root suite does **not** need the HiQS package installed (M4b 6/6 green,
  identical inventory) — the packaging boundary is real.

## Incumbent flakiness observed (noise floor)

`tests/test_github_knowledge.py::…::test_sync_does_not_hold_write_lock_across_network_fetch`
failed once in the incumbent lane itself (S2 sample 2, c0 3.13: 0.38 s vs the
0.3 s assertion under runner load) and passed in the other 5 c0/c1 executions.
Incumbent job spread was 143–322 s (3.12). Both facts size the ≥20 % D1
threshold: C3's ~2× margin is far outside this noise; C1/C2's single-digit
cuts are inside it.

## Threats to validity

- **Platform proxy (S1)** — declared and honored: D1 consumed S2 only; no
  cross-source ratio appears anywhere in this summary.
- **n=3 per S2 config** is small; all raw values are in `ci-job-timings.jsonl`
  and the conclusion margin (2×) is far beyond observed spread. One incumbent
  outlier (322 s) shows runner tail noise; medians were used.
- **Seam set is commit-specific.** It is exactly 2 files at `8f733ce`; new
  embeddings-dependent tests shift it — by design this fails the root lane red
  (fail-closed), but it is a maintenance surface C4 does not have.
- **Spike jobs are not a real PR check** — no required-check gating, no
  queueing interaction; deferred to implementation as pre-declared.
- **Not measured:** runner queue time, artifact-upload overhead (inside job
  wall times), lint/typecheck/docs jobs (unchanged by #144), HiQS-under-xdist
  (out of scope: #7 process boundary + a 25 s lane).
- **Deviations from protocol** are recorded in protocol §12 (A1–A13 pre-run
  amendments from review; P1–P5 post-run). The material ones: one DNS-failed
  cold-install record (retained, excluded from aggregates), a junit nodeid
  reconstruction bug fixed with all maps regenerated from retained junit
  (P2), and S2 run 1 invalidated by the repo's own machine-local-path ratchet
  firing on campaign artifacts (P5 — the guard was right, the artifacts got
  the disclosed `.txt` + prefix-sanitization treatment).
- **Inventory maps contain strings like `/tmp/abs` inside parametrized node
  ids** (path-escape test data, `tests/test_hiqs_digest.py`). They are
  byte-exact test identifiers, not paths, and must not be "sanitized"; the
  markdown-link checker passes.

## Recomputability

`runs.jsonl` (S1 primitive, schema 1) + `ci-job-timings.jsonl` (S2) carry
every number above; `scripts/` contains the runner, driver, analyzer, map
regenerator, CI-union checker, sanitizer, and the spike workflow as run
(`phase0-measure.yml.as-run.yaml`). CI-side records link run/job URLs; local
junit files (sha256 in `runs.jsonl`) live in gitignored `temp/gh144/artifacts/`
and regenerate from the same commands. Scripts as run:

```bash
bash TESTS-RESULTS/2026-09-01+GH-144/scripts/run_s1_all.sh          # M1–M9
python3 TESTS-RESULTS/2026-09-01+GH-144/scripts/regen_outcome_maps.py # P2 regen
python3 TESTS-RESULTS/2026-09-01+GH-144/scripts/analyze.py           # D2 tables
python3 TESTS-RESULTS/2026-09-01+GH-144/scripts/check_ci_union.py temp/gh144/s2artifacts 33595630182
bash   TESTS-RESULTS/2026-09-01+GH-144/scripts/m10_witness.sh        # lane controls
```

## What Phase 0 did NOT do

No change to `ci.yml` on any branch. 3-Eyes untouched. The spike branch and
its throwaway workflow are the measurement instrument only; the implementation
PR (three required lanes per Python: root `.[calendar,server]`, embeddings
seam, HiQS-only — all cached, HiQS still a separate pytest process per #7) is
the follow-up, gated on operator review of this campaign.
