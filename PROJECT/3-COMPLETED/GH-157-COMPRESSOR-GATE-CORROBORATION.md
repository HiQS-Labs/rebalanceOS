---
gh_issue: 157
source: https://github.com/HiQS-Labs/rebalanceOS/issues/157
title: "GH-157 — the compressor gate refused a 1.9 GB job 179 times on a healthy machine"
status: "Merged 2026-09-04 as d31e0e3 via PR #171; shipped into the Embeddings Under Pressure release. Carried the #156 prerequisite; #156 stays open for its remaining scope."
created: 2026-09-03
owner: noel
doc_type: fix
goal: >
  Stop gating the embeddings job on machine-wide compressor pressure it does not cause,
  without weakening the ceiling for the Qwen-class jobs the 0.25 fraction was correctly
  derived for.
effort: 3
complexity: 3
risk: 3
phases: 1
ratings_provisional: false
---

# GH-157 — compressor gate corroboration

## TOC

1. [The premise that stopped holding](#1-the-premise-that-stopped-holding)
2. [What changed](#2-what-changed)
3. [The #156 prerequisite, included](#3-the-156-prerequisite-included)
4. [Live control](#4-live-control)
5. [Backfill check](#5-backfill-check)
6. [Acceptance](#6-acceptance)
7. [What is still open](#7-what-is-still-open)

## 1. The premise that stopped holding

`DEFAULT_MAX_COMPRESSOR_FRACTION = 0.25` was sized from 1,602 recorded sampler rows
(`sysmem-sys-*.csv`, 2026-07-26/27) whose distribution was strongly **bimodal**: median
0.65–0.96 GB when healthy, 25–35 GB in distress, "with almost nothing between". The
constant was placed at 16 GB precisely because it sat in that empty middle, and the
comment says so: "Robustness here is a property of the data, not a lucky constant."

The empty middle is no longer empty. This machine now idles at **17–23 GB** of ambient
compressor from unrelated software — inside the gap the constant depends on — and the
bare threshold refused `obsidian-vault-embeddings` **179 times across 9 days**, 36 times
in a single day on four separate days, i.e. every scheduled run those days.

The job it was refusing peaks at **1.86 GB** and moves the compressor by **0.23 GB**
(17.71 → 17.94 over 59 samples, pid 7416, 8m37s, exit 0). It neither causes the reading
nor meaningfully adds to it. With ambient pressure from other processes the gate had no
path back to healthy; it just waited for other software to release memory.

The workload also changed underneath the constant. The 0.25 figure was derived against
**Qwen3-Embedding-0.6B**, which reached 14.32 GiB and was stopped only by MPS's own
watermark. After the GH-81 migration the guarded job is **BGE-small** (33M params,
384-dim) — roughly 7.5× smaller and empirically incapable of the condition the ceiling
exists to prevent.

The design error underneath all of it: machine-wide compressor pressure answers *"is this
machine in distress?"*. It does not answer *"will running this job put it there?"*, and
for a 1.9 GB job those are different questions.

## 2. What changed

`DEFAULT_MAX_COMPRESSOR_FRACTION` is **unchanged at 0.25**. Raising it was explicitly
rejected in the issue and rejected here: it would weaken the check for every guarded job,
including the Qwen-class ones the figure was correctly derived for. One global fraction
cannot serve jobs three orders of magnitude apart in footprint, and the fix for that is a
better predicate, not a looser one.

What changed is that **crossing the ceiling is now a suspicion, not a verdict**. New
`MemoryCeiling._compressor_trip()` requires the reading to be confirmed by a signal only
genuine distress produces:

- **swap actually in use** above `SWAP_DISTRESS_BYTES` (1 GiB) — the machine has run out
  of room to absorb pressure and is paging; or
- **available memory below the floor** — the availability gate would refuse this run
  anyway.

A large compressor with neither is a machine that absorbed pressure successfully. That is
the compressor doing its job, not evidence against starting a small one. Measured during
an actual refusal on 2026-09-03: compressor 19.25 GB, `vm.swapusage` **0.00M used**, 64%
of memory free, no paging — the refusal had nothing behind it.

New `swap_used_bytes()` parses `sysctl -n vm.swapusage`, keeping `None` (unreadable) and
`0` (positive evidence of no paging) distinct — collapsing them is how a blind probe turns
into a grant of permission. The unit travels with the number and is not always `M`, so
both are parsed.

The same rule governs the **mid-run** check, not just preflight. A long run that started
on a healthy machine must not be killed at minute forty because unrelated software filled
the compressor.

Fails **closed** on a blind probe: if neither corroborating signal can be read, the old
refuse-on-threshold behaviour stands.

## 3. The #156 prerequisite, included

#157 states it depends on #156 — "until it lands, a 'passing' run may simply be an
unguarded one, and any measurement of the new gate is unreliable." That is not a
formality, so #156's core defect is fixed here.

With `total_memory_bytes() == 0` every ceiling resolves to `None` and `start()` logs
"memory ceiling disabled" and returns. A run that passed only because the sysctl was
blocked was indistinguishable from a genuinely well-behaved one. `preflight()` now refuses
instead, with `EX_TEMPFAIL` semantics — deferred, so a supervisor retries rather than
counting it as a job failure.

This is observable, not theoretical: running the suite inside a sandbox that blocks
`sysctl hw.memsize` previously produced 28 green tests with the ceiling silently switched
off. After the change those runs refuse loudly and the suite has to be run where the probe
works. #156 stays open for its remaining scope; this closes the part #157 stands on.

## 4. Live control

Same machine, same live probes, no mocks. Live state: compressor **11.01 GB**, swap
**0.00 GB**, available **23.87 GB**, total 64 GB. The compressor ceiling was set to 8 GB
via `REBALANCE_JOB_GUARD_MAX_COMPRESSOR_GB` so the live 11 GB reading sits **above** it —
reproducing the 179-refusal condition on demand rather than waiting for it.

| control | condition | result |
|---|---|---|
| A — admit | compressor 11.0 GB over an 8.0 GB ceiling, swap 0, available healthy | **ADMITTED**, with the reason logged |
| B — refuse | same compressor, same ceiling, availability floor raised above what the machine has | **REFUSED**: "confirmed by available 23.9 GB below floor 35.8 GB" |
| C — unchanged | no override | per-job footprint ceiling still 8.0 GB (12.5%), compressor ceiling still 16.0 GB (25%) |

End to end, the real job under the real gate: `scripts/obsidian_vault_embeddings.sh` with
`REBALANCE_JOB_GUARD_MAX_COMPRESSOR_GB=8` against a live 11 GB compressor — the exact
shape that refused 179 times — **completed**, `errors: []`, 51.61s. Guard telemetry
(`temp/logs/job_rss.jsonl`) records peak footprint **1.49 GB** against the unchanged 8 GB
per-job ceiling, `tripped_reason: null`.

Suite: `tests/test_job_guard_footprint.py` 21 passed, `tests/test_job_guard_wiring.py`
green. Five new tests: the ambient-pressure admit, the swap-confirmed refusal, the
availability-confirmed refusal, the fail-closed blind probe, and the #156 unreadable-RAM
refusal, plus unit parsing for `vm.swapusage`.

## 5. Backfill check

Acceptance asked how stale the index was after 179 skipped runs. It is caught up. The
2026-09-03 run reports `semantic_backfill` 62,358 total / 1,648 updated / 8,218 deleted /
0 inserted, and `semantic_embed` 62,356 total / 3,021 embedded / 59,335 skipped_unchanged.
Zero inserted with a large skipped_unchanged is the signature of a corpus already
projected — the refusals delayed refreshes, they did not lose documents.

## 6. Acceptance

- [x] The embeddings job is gated on a signal it can actually influence, reasoning recorded.
- [x] `DEFAULT_MAX_COMPRESSOR_FRACTION` unchanged.
- [x] A recorded control: the gate refusing and admitting on the same machine state.
- [x] Backfill check: index caught up, nothing missing.
- [x] #156's fail-open RAM probe, the stated prerequisite, fixed.

## 7. What is still open

**Per-job ceilings.** The issue's second suggestion — sizing the compressor ceiling from
each job's recorded peak rather than one global fraction — is **not** implemented. The
corroboration rule removes the false positives without it, and per-job sizing needs
recorded peaks for every guarded job before it can be honest. `temp/logs/job_rss.jsonl`
is accumulating exactly that; revisit when there is enough of it.

**The rest of #156.** Only the physical-RAM fail-open path is closed here. The issue's
broader scope — every other probe that can return a falsy "no problem" when it simply
could not read — is untouched.

**The 07-26/07-27 sampler data is now unrepresentative of this machine.** The bimodality
argument should be re-derived against current data before any future constant leans on it.
