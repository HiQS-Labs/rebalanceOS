# T3 capture verification

Tracking: [GH-370](https://github.com/HiQS-Labs/rebalanceOS/issues/370).
Plan: [capture contract](../../PROJECT/2-WORKING/GH-370-T3-CLIO-CAPTURE.md).
Base: `f0819314c078f58e9d51b6ccd698c76b700ec1cc`.
Environment: macOS, Python 3.14; synthetic T3 sources and temporary CLIO homes.

The added store cases first failed on the base helper with AttributeError for
missing configure_t3/capture_t3. The implemented cases cover short/multiline
prompts, steering, multiple providers, fresh human input in imported and child
threads, version/creator/source filtering, page boundaries, missing project/run
metadata, changed projections, interrupted cursor publication, queued writes,
scheduled exports and idempotent rereads. Source bytes remain unchanged.

`clio-store.txt` retains the store suite output. Existing `test/clio-capture.sh`,
`test/clio-runtime.sh`, `test/clio-exporter.sh`, `test/clio-codex-tail.sh` and
`test/clio-agy-tail.sh` passed. SQLite/import and script-inventory ratchets passed;
documentation link checking found no broken links or machine-local paths.

`smoke.txt` records the real CLI configure/capture path on a disposable fixture,
then a second capture invocation. The setup reuses the existing acceptance
fixture, not a new runner: activate a temporary store, create its synthetic T3
source, register with configure-t3, append one `ok` human event, invoke capture-t3
twice, and assert one unchanged record with T3 provenance.

Independent plan QA round 1 requested steering attribution, event-level import
filtering, explicit frozen identity/retry policy and version boundaries. All four
were accepted; round 2 Approved implementation. Reviews ran through T3-managed
Codex delegation because host orchestration takes precedence over shell relay.

Runtime doctor ran and returned failure for an existing silent fleet device and
an existing scheduled digest failure, plus configuration/staleness warnings.
This change does not modify fleet or job configuration. No overall machine-health
claim is made. A separate doctor run from the maintained base checkout also
returned exit 1 with the same silent-device and scheduled-digest errors; private
device labels and config paths are not published here.

Final independent QA round 2 Approved code revision `e6b91f8`; the verbatim
response is retained in `final-qa.md`. The final store suite also passed in the
disposable full verification clone at that exact revision (`clio-store-final.txt`).
Full repository verification completed at approved code revision `e6b91f8` in a
disposable full clone whose HEAD remained unchanged and whose only untracked
artifact was the retained final store log. Root suite: **2815 passed, 21 skipped,
10 xfailed, 171 subtests passed** (`root-tests.txt`). HiQS: **163 passed, 1 skipped,
1 xfailed** (`hiqs-tests.txt`). Both separate invocations exited 0. The root suite
retains its existing platform/data skips; one optional pre-push fixture skipped
because the disposable clone has no local venv. The real branch push uses the
armed pre-push gate with the existing interpreter explicitly selected.

The initial combined root+HiQS
invocation finished with 2974 passed, 4 failed, 22 skipped, 11 xfailed and 171
subtests passed (`combined-invocation.txt`, local checkout paths redacted). All
four failures are quarantine tests importing the other suite's bare `conftest`
module. They pass alone on unmodified base (`baseline-quarantine.txt`). The
suites were therefore rerun in separate processes, matching CI; the combined
run is retained as failed invocation evidence, not reported as a passing gate.
The same minimal combined invocation reproduces all four failures on unmodified
base (`baseline-combined-collision.txt`). Running HiQS separately passes:
163 passed, 1 skipped, 1 xfailed (`hiqs-tests.txt`). Its existing private-name
check is skipped because the private allowlist is absent, not counted as a pass.

PDDA frontmatter/status/roadmap checks returned their existing warn-mode findings:
7 frontmatter errors, 9 status-table errors and 9 missing roadmap pointers, all
in other existing plans. The same results reproduced on the unmodified base
`f081931` in a separate full clone; no new plan finding was reported. These
commands returned exit 0 under the repo's configured enforcement mode.

Final QA round 1 found replay blocked by missing current run metadata despite a
retained committed/pending payload. The existing interruption fixture was
extended to delete the run projection and failed before the correction with
`T3 submission run metadata unavailable`. The fix resolves stable identity and
checks retained payloads before attributing unseen messages. Both committed and
pending replay cases now remove the run projection before retry. The focused
three-case T3 rerun is retained as `t3-recovery.txt`.

## Threats to validity

Greptile identified two reproducible cases after publication. An existing
provider fixture with 1,001 older sessions stalled capture on the previous
all-session cap; the query now returns only the newest session per referenced
instance using a single grouped window query. A null modelSelection also escaped
the local scheduled-capture guard and stopped existing-history publication.
Model objects are now validated and AttributeError is contained at that boundary.
The existing cases were extended (no new runner): both failed before correction;
the full 20-case store suite rerun is `greptile-regressions.txt`. It also verifies
that malformed thread metadata still allows a freshly rebuilt compatibility
export while retaining the capture cursor. Broader package suites were not
repeated because these changes affect only the standalone CLIO helper and its
existing acceptance fixture; packaged Rebalance sources are unchanged.

Hosted run `41103203124` cancelled `readme-install` before assigning a runner or
executing any step. Its check annotation explicitly identifies GitHub's scheduled
macOS 14 image brownout. The failure occurred inside the announced October 30
14:00–October 31 00:00 UTC interval. GitHub's
[runner retirement notice](https://github.com/actions/runner-images/issues/13518)
names `macos-15` as a supported migration. Only that job's runner label was
updated; its README installation and test-collection steps are unchanged.
Root cause: retired hosted image policy; fix site: the workflow's runner label;
application code cannot run before runner assignment. Fresh hosted verification
of the replacement runner remains pending.

The fixture matches the inspected unified V2 T3 event/projection contract; other
layouts deliberately refuse capture. No live installation or post-merge rollout
was performed. Native provider capture may independently retain the same input;
this proves T3 submission retry deduplication, not cross-harness reconciliation.
Metadata is observed from projections at capture time. Full machine health is
not qualified by these focused capture checks. Fleet readers must receive the
updated CLIO helper before T3 capture is enabled; older helpers cannot validate
the T3 producer's identity rule. Cross-version fleet rollout was not performed.
