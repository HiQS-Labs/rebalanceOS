# GH-334 verification summary

These are manual checks; no suite was added. The change is a skill and docs only.

| Check | Result |
|---|---|
| Plan QA, codex | **Approved** in round 3/3, attested against `b246a70` (`qa/gh334-plan-qa-relay.md`) |
| Smoke, main path (read-only, this Mac) | Steps 0–1 found: `scheduler:pulse-sync` error (not loaded), `pulse` configured, fleet not enrolled, no operation in progress, clean tree, 39 behind / 10 ahead, `PULSE_PUSH` unset, job not registered. Planned actions: 2.1 `load -w`, 2.3 report only, 3 off-fleet resync. `smoke-main-path.log` |
| Smoke, adjacent path (disposable repos) | 2.4 as written. **RED** lock held → stopped, refs and state unchanged. **RED** live `git` process with cwd in the checkout (relative command line) → stopped, unchanged. **MAIN** abandoned conflicted rebase → both backup refs verified, the patch retains the conflict edit, the abort restores `main` to `orig-head`, the local commit is reachable. **RED** merge in progress → classified outside the exception, no command run. `smoke-rebase-recovery.log` |
| Not run before merge | The real repairs and resync on this Mac (`load -w`, kickstart, completion observation). They mutate the device and run when the operator invokes the installed skill. Completion attribution (fast, failed or already-running jobs) has no runtime qualification yet. |

The smoke exposed one fix: step 2.4 needs `export PULSE G` before its lock wrapper.
