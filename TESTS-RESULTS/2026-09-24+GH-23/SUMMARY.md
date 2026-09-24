# GH-23 publication regression campaign

Date: 2026-09-24. Tracking: #23. Protocol: PROJECT/2-WORKING/GH-23-PUBLICATION-DURABILITY.md, reviewed by Claude Code claude-fable-5-1 at low effort before implementation.

## Results

- Baseline root + HiQS: 2760 passed, 21 skipped, 11 xfailed; 143 subtests. Source e21ec19.
- Nine initial real-Git controls: all nine failed on baseline. Raw failures retained in red.txt.
- Expanded focused contract: eleven passed. Source tests/test_git_publication_contract.py contains the executable fixtures.
- An interim full run overlapped the version bump and correctly reported one version mismatch (old imported constant versus updated packaging file); this is not counted as the final gate.
- Final full run: 2770 passed, 21 skipped, 11 xfailed; 143 subtests. Production source was unchanged during this run. A test lambda received an equivalent default binding for lint compliance.
- Ruff check/format, mypy (117 source files), shell syntax, five governance ratchets and the task-scoped frontmatter/status/roadmap checks pass. Repository-wide PDDA still reports unrelated pre-existing document debt.
- Post-review malformed-pointer and literal-path controls: two failures before fixes; 135 focused tests pass after the review fixes (including thirteen contract controls). Ruff/mypy/shell checks pass again. Initial cloud CI passed on Python 3.12 and 3.13; the review-fix head is being rechecked.
- Implementation QA round 1 textual PASS was rejected by the driver for transcript ordering; its verbatim thread is retained. Round 2 is Approved and driver-attested at 5a7b92f. Full transcript and portable attestation (machine path fields redacted) are retained under qa/. The reviewer could not start its own focused tests (interpreter exit 134); independent cloud CI and the producer's retained runs supply execution evidence.
- Single-device pilot passed: reviewed runtime 0.95.1 and installed collector hashes match; both existing LaunchAgents completed with exit 0 and remote output verification. The displaced 45-commit tip and remote tip survive as recovery-merge ancestors; four missing digests and both pointer blobs are verified remotely. Fresh ls-remote agrees with local HEAD, divergence is 0/0, and the worktree is clean. See pilot.json; complete private payloads, backups and job logs remain outside the public repository.

## Reproduction

Use the repository Python environment with PYTHONPATH=src:HiQS and PYTHONDONTWRITEBYTECODE=1.
Run `python -m pytest tests/test_git_publication_contract.py -q` for real temporary-repository boundaries; `python -m pytest tests/ HiQS/tests/ -q` for the full suite. The deferred supervisor suite is deliberately excluded. No custom runner was introduced.

Console copies trim trailing whitespace and redact machine-local home and temporary paths; assertions and result counts are unchanged. Fixtures contain synthetic data, not production exports.

## Threats to validity

Local macOS/Python 3.13 tests use temporary Git remotes. They do not prove every deployed device uses the new collector or that an uncooperative human Git command honors advisory locking. Existing quarantines remain. Network/SSH and the two actual LaunchAgent execution paths were exercised in the single-device pilot. Other devices have not been upgraded or verified. Persistent filesystem permission failures remain operator-visible deferrals; no new supervisor was added.
