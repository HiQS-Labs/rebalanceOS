# GH-199 CLIO capture verification

Date: 2026-09-08. Issue: https://github.com/HiQS-Labs/rebalanceOS/issues/199.
Plan: [GH-199-CLIO-FIRST-PROMPT.md](../../PROJECT/2-WORKING/GH-199-CLIO-FIRST-PROMPT.md).
Candidate runtime/test commit: `4a0ff1f`. Baseline runtime: `0bffc4d`
(the initial test clone had doc-only commit `48ef6fa`).

| Check | Result |
|---|---|
| Four CLIO shell suites, canonical | All pass; individual logs and candidate-runs.jsonl retained |
| Four CLIO shell suites, downstream | All pass against copied tailer/test and downstream writer; downstream-runs.jsonl retained |
| New discovery regression on original tailer | Fails: completed first prompt lost before discovery; source remains nonempty and unchanged |
| Five deliberately broken variants | All fail the matching positive/exclusion checks; mutation-controls.jsonl and scripts/mutation-check.py retained |
| Full pytest tests/ HiQS/tests, baseline | 1 failed, 2484 passed, 21 skipped, 11 xfailed (159.98 seconds) |
| Full pytest tests/ HiQS/tests, candidate | Same 1 failed, 2484 passed, 21 skipped, 11 xfailed (158.56 seconds) |
| Doctor baseline | Incomplete: no output after more than four minutes; own process terminated, exit 143 |
| PDDA changelog | 0 errors |
| PDDA frontmatter/status-table/hardcoded-paths/roadmap-coverage | 6/6/5/6 errors respectively in other documents; no GH-199 finding. These commands return 0 despite findings; do not read the exit code as a green gate |
| Downstream front-door checks | Baselines green; existing FD-05/06/07 remain open (troubleshooting, Agy scheduling prose, missing .gitignore) |

## Reproduce

Run the existing `bash test/clio-codex-tail.sh` manually for the full Codex fixture
harness. The other three suites are `clio-capture`, `clio-exporter`, and
`clio-agy-tail` under `test/`. No CI/CD wiring was added. Mutation checks can be
invoked manually with `python3 TESTS-RESULTS/2026-09-08+GH-199/scripts/mutation-check.py`
from a disposable clone. It runs the same Python fixture block against temporary
copies and the original baseline, without changing the candidate source.

All shell fixtures use temporary homes and synthetic prompt text. The canonical
broad suites ran in a separate full clone; HEAD, origin and core.bare were intact
after the run. The shared Python environment supplied dependencies, with source
resolved from the disposable clone. Machine-specific paths in retained console
logs are replaced with placeholders; prompt bodies from real sessions are absent.

## Limits and remaining gates

The one failing Python test is
`tests/test_doctor_scheduled_stack.py::DeclaredRuntimeRootTests::test_declared_root_overrides_running_checkout`:
expected warning, received ok. It fails identically before and after this CLIO
change. Doctor is not attested healthy. The canonical PR remains draft pending
those broader gates; focused correctness is not an overall merge-readiness claim.
The skipped and expected-failure test cases remain explicitly listed in both logs.

Initial capture begins at the persisted first-run instant, not installation time.
The historical missing prompt has not been backfilled, installed hooks have not
been changed, and no live capture claim is made. An abandoned lock still needs
operator recovery. Pre-boundary pending data cannot be recovered automatically
after legacy file provenance is lost. Same-second writer ID collisions remain the
existing contract. Synthetic reproduction proves the code defect; missing
historical first-poll telemetry limits exact incident attribution.
