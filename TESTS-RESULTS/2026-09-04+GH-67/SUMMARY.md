# GH-67 — is the test suite's result independent of the directory pytest is invoked from?

| | |
|---|---|
| **Ran** | 2026-09-04 |
| **Tracking issue** | [#67](https://github.com/HiQS-Labs/rebalanceOS/issues/67) — "15 tests fail when pytest is invoked from outside the repo root" |
| **Working doc** | [PROJECT/3-COMPLETED/GH-67-PYTEST-CWD-DEPENDENT-FAILURES.md](../../PROJECT/3-COMPLETED/GH-67-PYTEST-CWD-DEPENDENT-FAILURES.md) |
| **System under test** | the `tests/` suite, invoked from two different working directories |
| **Commit** | `c897072fe6539c636ee4ee414b65974c9f3eebe2` (branch `hotfix/gh67-pytest-rootdir-config`, rebased on `development` @ `65634bf`) |
| **Environment** | macOS, Apple Silicon; Python 3.14.7; pytest 9.1.1; venv built with `pip install -e ".[dev,server]"` |
| **Duration** | 108.7 s (repo root) + 95.3 s (foreign cwd) |
| **Output files** | `from-repo-root.txt`, `from-foreign-cwd.txt`, `rootdir-proof.txt` |

Published because [PR #166](https://github.com/HiQS-Labs/rebalanceOS/pull/166) and the GH-67 working
doc both cite these numbers. `SOP.md` §1: *a claim whose evidence is unpublished is an assertion.*

## Commands, exactly as run

```
# repo root
cd <repo> && .venv/bin/python -m pytest tests/ -q -p no:randomly

# foreign cwd
cd /tmp   && <repo>/.venv/bin/python -m pytest <repo>/tests/ -q -p no:randomly
```

`-p no:randomly` pins collection order so the two runs are comparable. That is the only deviation
from a default invocation.

## Result

| Invocation directory | Result |
|---|---|
| repo root | 10 failed, 2187 passed, 20 skipped, 10 xfailed, 143 subtests passed |
| `/tmp` | 10 failed, 2187 passed, 20 skipped, 10 xfailed, 143 subtests passed |

The two `FAILED` lists are **byte-identical** after normalising the path prefix (`diff` returns
nothing). None of the 15 tests #67 named appear in either list — the 14 in
`tests/test_uninstall_rebalance.py` and the one in `tests/test_doctor_json.py` all pass from both
directories.

`rootdir` resolves to the repository from either invocation, with `configfile: pyproject.toml`
(see `rootdir-proof.txt`).

## The 10 failures, and why they are not GH-67

All 10 fail identically from both directories, so none is CWD-dependent. They fall into three
pre-existing environmental groups on this host:

```
tests/test_credential_dedup.py::OAuthCommonLoaderTests::test_insufficient_scope_raises_service_error
tests/test_credential_dedup.py::OAuthCommonLoaderTests::test_refresh_persists_to_both_stores
tests/test_gmail_keyring.py::GmailLoadCredentialsTests::test_keyring_blob_is_preferred_over_pickle
tests/test_gmail_keyring.py::GmailLoadCredentialsTests::test_missing_required_scope_raises
tests/test_oauth_json_fallback.py::test_refresh_persists_json_to_both_stores
      -> macOS Keychain-backed credential paths

tests/test_embedder.py::EmbedderTests::test_embed_vault_chunks_end_to_end
tests/test_embedder.py::EmbedderTests::test_load_and_embed_batch_with_mock_model
tests/test_embedder_metal_unavailable.py::test_real_model_loads_and_embeds_on_this_machine
tests/test_embedder_metal_unavailable.py::test_load_model_succeeds_even_when_metal_unavailable
      -> sentence-transformers, not installed by the [dev] extra; CI --ignore's the two
         test_embedder* files in the root lane and runs them in the `seam` lane instead

tests/test_doctor_scheduled_stack.py::DeclaredRuntimeRootTests::test_declared_root_overrides_running_checkout
      -> reads host launchd state
```

Under CI's exact root-lane command (`--ignore=tests/test_embedder.py
--ignore=tests/test_embedder_metal_unavailable.py`) the count is 6 failed / 2142 passed, all
Keychain-bound. CI itself is green on this branch across all 9 checks.

## Finding

**GH-67's symptom is fixed, and was fixed before this branch existed.** The `_run()` cwd pin landed
2026-08-27; this run is an independent re-measurement of it, made by someone who had not seen that
fix. The `[tool.pytest.ini_options]` block that declares `rootdir` came later, via #162.

## Threats to validity

Stating these because a summary that reports only what worked is a sales document.

1. **Two points is not a proof.** This compares exactly two directories, the repo root and `/tmp`.
   It falsifies the specific symptom #67 reported. It does **not** establish directory-independence
   in general. A directory containing a stray `conftest.py` or `pytest.ini`, a path with spaces, or
   a location outside `$HOME` could still behave differently and was not tested.
2. **One host, one interpreter.** macOS on Apple Silicon, Python 3.14.7. CI runs 3.12 and 3.13 on
   ubuntu, so this local interpreter is outside the CI matrix entirely. A CWD dependency that only
   appears on Linux, or only on 3.12, would not show up here.
3. **10 failures were assumed environmental, not proven so.** They are identical across both
   directories and match what `development` produces on its own, which is why they are attributed to
   the environment. Their individual root causes were not investigated.
4. **Collection order was pinned.** `-p no:randomly` was used deliberately for comparability, which
   means any order-dependent behaviour — including the known cross-suite state leak recorded in
   closed issue #7 — is suppressed rather than exercised.
5. **Not a campaign.** `SOP.md` §2 does not require one here: this is a refactor and documentation
   change with no comparative claim. There is no baseline, no paired test, and no significance
   testing, and none is claimed.
