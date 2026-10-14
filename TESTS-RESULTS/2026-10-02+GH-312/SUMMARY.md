# GH-312 pre-push gate spike — campaign summary

| | |
|---|---|
| **Campaign** | `2026-10-02+GH-312` (ran 2026-10-02, local evening PT) |
| **Tracking issue** | [HiQS-Labs/rebalanceOS#312](https://github.com/HiQS-Labs/rebalanceOS/issues/312) (Rung 2 spike spec, § "The one spike worth doing now") |
| **Working doc** | the issue itself; no separate plan doc — the spike's four decision gates were pre-registered there before any run |
| **Systems under test** | (a) candidate `.githooks/pre-push` fast gate (ruff check/format + root-noembed lane + the two ci.yml grep guards), direct-invoked, never armed; (b) hosted `ci.yml` first-feedback times, from the Actions API |
| **Tree under test** | `e46150a` (origin/development tip at run time); venv Python 3.13.12, pytest 9.1.1, ruff 0.16.3 |
| **Duration** | ~45 min wall (5 full-lane pytest runs ≈ 25 min, serial; the rest mechanics/governance/CI sampling) |
| **Output files** | `gate-timings.jsonl` (primitive), `gate-receipts.jsonl`, `ci-feedback-sample.jsonl` + `consoles/ci-jobs-sample.tsv`, `consoles/`, `scripts/` (timeit runner + hook candidate as run), `red-control.patch` + `red-control-before.sha` |

## Decision (the four pre-registered gates)

| Gate | Bar | Measured | Verdict |
|---|---|---|---|
| **G1 — fast tier < ~3 min locally** | < 180 s | root-noembed lane median **296.6 s** (3 serial runs: 303.3 / 296.6 / 267.7, all green); full gate end-to-end **332.1 s** | **FAIL** |
| **G2 — governance compatibility** | GH-241 + GH-259 + ratchets pass with hook tracked | All five `utils/pdda/check_*.py --check` exit 0 with the hook intent-to-add in `git ls-files`; total **1.9 s**. The hook sits outside GH-241's scan scope (it only rglobs `scripts/` + `utils/`) and outside GH-259's suffix set (extensionless file) — passes today, but see threats | **PASS** |
| **G3 — red control: gate blocks a #178-class breakage** | non-zero exit, failing stage named, byte-for-byte restore | 1-assertion mutation in tracked `tests/test_pytest_rootdir_pinned.py` (`returncode == 0` → `== 99`, `red-control.patch`); gate exit **1**, both mutated tests failed (2 failed / 2638 passed), "push BLOCKED" emitted, receipt written; restored sha256-identical (`fc4e9602…`, matches `red-control-before.sha`), focused re-run 2 passed | **PASS** |
| **G4 — local beats hosted feedback meaningfully** | local median < hosted median | Local full-lane gate **296.6 s** vs hosted PR first-feedback **median 144 s** (n=40 recent PR-triggered `ci.yml` runs, min 79 / max 284). Local loses ≈ 2× | **FAIL** |

**Decision: do not arm the full-lane pre-push gate.** It fails the two gates that matter (runtime and feedback delta) while passing the two that validate its construction (governance and blocking behavior). The hook candidate is mechanically sound — the *scope* is wrong, not the code.

## Findings

1. **The local lane costs ~5 minutes and hosted CI answers in ~2.4 — a local full-lane gate can only ever lose.** Every full-lane run pays the same suite both places, and locally it is slower (macOS process-spawn and real-Git subprocess cost).
2. **Both boundaries are bloated by the same, recently-added suites.** The instrumented run (`consoles/root-noembed-durations.txt`) shows the top-25 slowest tests ≈ 141 s of a 285 s run, dominated by `test_pulse_self_repair` (~47 s), `test_git_publication_contract` (~27 s) and `test_web_surface` setup (22.8 s) — precisely the real-Git publication/self-repair contracts GH-23 and GH-282 landed. Correspondingly, the hosted `root-noembed (3.12)` job — GH-144's C3 winner, targeted at 82 s — now runs **184–251 s** on the runners (`consoles/ci-jobs-sample.tsv`). The lane has roughly tripled as the contract suites grew.
3. **A salvage path exists and it re-orders the ladder:** the static pre-push substrate (ruff check + ruff format + the two grep guards + all five governance ratchets) is measured at **~2.5 s total** and catches the lint/format/guard/sprawl classes instantly; test coverage at the boundary should come from Rung 3's path→tier map (mapped paths → their tier; unmapped → skip locally with a loud receipt, hosted CI stays the fail-closed attestation). In short: **Rung 3 (tiering) becomes the prerequisite for Rung 2 (gate), and the gate ships in two stages — static-now, tiered-after-Rung-3.**
4. **xdist-4 does not rescue the full-lane local gate.** pytest-xdist is not installed locally; applying the CI-measured 36% cut (GH-144) to the local median predicts ~190 s — still over the 180 s bar. Untested locally; recorded as an estimate, not a measurement.
5. **Incidental finding — live API call in the unit lane:** `tests/test_health_issue_reporter.py::TestLLMTriage::test_real_api_call_gemini` made a real network call during the diagnostics run (2.06 s, passed). The repo's own testing policy puts external integrations behind mock harnesses (`MOCK_MODE`); this test appears to violate it. Flagged for a follow-up issue; not fixed in this spike.
6. **Incidental observation — GH-144's headline should be re-checked:** median hosted PR feedback (144 s, any job the pole) is well above the 82 s lane target. The win was real (the lane did halve then) but suite growth since has given it all back. Rung 3 is the fix for hosted feedback too; consider re-measuring after it lands.

## What ran (protocol notes)

- Timing runs were **serial and non-overlapping** on the same tree/HEAD (`e46150a`); medians are over 3 identical-command samples, per house style.
- The hook was **never armed** (shipped non-executable; `bash .githooks/pre-push --verify` reports the disarmed state with remediation) and was invoked directly with synthetic pre-push stdin — no real push was made, nothing was committed.
- Mechanics exercised beyond the four gates: `--verify` (reports disarmed, rc 1), empty-stdin noop (rc 0), delete-only noop (rc 0), logged bypass via `REBALANCE_SKIP_PREPUSH_GATE` (rc 0, receipt `kind=bypass`). A first-version stdin parser bug (parsed the ref field instead of the local-oid field, falling through to the full gate on a delete-only test) was caught by exactly this mechanics pass and fixed before any timed run.
- Governance runs used `git add -N` (intent-to-add) so the untracked hook appears in `git ls-files`, then dropped it; the working tree returned to its pre-spike state (pre-existing `ROADMAP.md` modification and one untracked inbox file aside).
- The static substrate composition (~2.5 s) is the sum of already-published primitives (ruff ~0.1 s, grep guards sub-second in gate consoles, five ratchets 0.07–1.13 s); it was not timed as a single composite command.

## Threats to validity

- **Single machine:** operator laptop, darwin/arm64, one venv. The Studio runtime and any other device were not measured.
- **Ambient load uncontrolled:** runs were serial but the machine was not otherwise quiesced. The spread across identical runs (267.7–303.3 s, ~12%) bounds the noise.
- **Provenance gaps, disclosed:** (a) `root-noembed-run1`'s full console was destroyed by a run-labeling mistake (the third run overwrote it); its retained tally line (`2640 passed … in 301.60s`) and its timing primitive stand, but per-line detail for that one run is lost. (b) The green gate receipt was wiped by an `rm` during red-control prep and is re-emitted verbatim from session capture, flagged `"reconstructed": true` in `gate-receipts.jsonl`. (c) The timeit runner printed primitives to session stdout rather than a file; `gate-timings.jsonl` is the faithful transcription of those lines, with consoles for every record except run1 (tally-only).
- **CI sample bias:** the 40-run sample is "most recent PR-triggered runs at sample time," second-precision walls from run create/update timestamps, and includes queue time implicitly. conclusions rest on a ~2× gap, far outside sample noise.
- **Hook scope limits:** the gate tests the working tree, not each pushed ref (multi-ref pushes are checked once); delete/bypass/noop paths are receipted but bypass enforcement is honor-based by design (P1: logged, never silent).
- **Governance pass is scope-shaped, not principle-approved:** GH-241 doesn't scan `.githooks/` at all and GH-259 skips extensionless files — the hook passes *because it is outside the guards*, which also means those guards would never flag machine paths inside it. If the hook ships, that blind spot should be closed (add `.githooks/` to GH-259's scanned set) rather than relied on.
- **No external QA relay** was run for this spike; the campaign is published for review on the tracking issue.
- **3-Eyes suite deliberately excluded** from the lane (operator stand-down, 2026-08-17) — consistent with hosted CI.
