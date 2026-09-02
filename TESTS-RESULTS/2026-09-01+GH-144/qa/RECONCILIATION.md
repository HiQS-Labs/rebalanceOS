# Protocol review reconciliation — GH-144 Phase 0

Coordinator: Claude (ZCode), 2026-09-01. Advisors: Codex (gpt-5.6-sol, retry at
900 s cap after the first attempt hit the 300 s consult cap — see
`protocol-review.attempt1-degrade-note.txt`) and agy. Transcripts verbatim:
`protocol-review.codex.txt`, `protocol-review.agy.txt`. Issue comment filed:
https://github.com/HiQS-Labs/rebalanceOS/issues/144#issuecomment-5504300832

**Disclosed mechanical treatment of the transcripts (nothing paraphrased):**
stored as `.txt` (they are raw session logs / console captures, matching this
repo's convention for raw output, which the markdown-link checker does not
scan), and passed through `../scripts/sanitize_artifacts.py`, which replaces
machine-local path prefixes (`/Users/<user>` → `~`, `/private/var/folders/` →
`<var-folders>/`, etc.) — the repo ratchets against committed machine-local
paths (`scripts/check_doc_links.py` MACHINE_LOCAL), and the raw transcripts
quote advisor worktree paths. Content otherwise byte-for-byte as produced.

## TLDR

Both advisors blocked the protocol as drafted — D1 was not computable because
candidates had no CI-side measurement, C3 was internally contradictory, and the
inventory fingerprint was collection-only. All blocking findings were adopted
as amendments A1–A13 in the protocol's §12 before any measurement ran. One
disagreement was adjudicated (below). Protocol v1.1 is the run protocol.

## Disagree (and adjudication)

- **agy:** mandate draft-PR CI runs for *all* candidates and evaluate D1
  strictly on CI wall time. **Codex:** the local/CI hybrid is coherent for
  feasibility and structure; only adoption-level speedup claims need CI.
  **Adjudication → Codex's split**, implemented as the spike-branch S2 workflow
  (real runners, same SHA, ×3 re-runs) carrying D1 exclusively, while S1 local
  runs carry feasibility/determinism/inventory. This satisfies agy's substance
  (no D1 input is local) within the issue's 1–2 h spike scope.

## Agree (adopted, cross-model)

1. D1 needed complete end-to-end same-source candidate paths (Codex #1, agy #1)
   → A1: S2 spike workflow; local timings demoted.
2. C3 as drafted could not pass by definition; seam exclusion + seam-lane row +
   exact-once union required (Codex #4, agy #2/#3) → A4.
3. Witnessed-red needed the full retained evidence chain and must not overclaim
   Actions routing (Codex #9) → A10.
4. Publication skeleton and two-source separation were sound (Codex pass #2/#5,
   agy pass #6/#7) — no change.

## Adopted from a single advisor

- **agy #4 → A5:** C2's root lane had never been proven without HiQS installed
  (the incumbent venv contains HiQS); cell M4b added.
- **Codex #2/#3/#5–#8/#10 → A2/A3/A6–A9:** D1 disambiguation (cumulative,
  max-per-Python, both-Pythons), ≥3 runs everywhere, C4 `--dist` + C4b
  serial-exclusion spec, node-level exact-once union, fail-closed collection,
  literal clean-clone mirror, full primitive schema.
- **Codex optional #2/#3 → A12 (partial):** billed runner-minutes and cache
  hit/miss recorded; local cache-restore granularity not measured (S2 carries it).

## Dismissed (with reason)

- **Codex optional #1** (interleave S1 candidate order) → A11: S1 timings no
  longer feed D1 after A1; interleaving doubles matrix cost for a decision it
  cannot affect. Recorded as a §10 threat instead.
- **Codex optional #4** (exact patch versions in protocol header) → handled by
  the primitive records capturing exact versions per run; protocol text stays
  version-flexible so it does not drift stale.
