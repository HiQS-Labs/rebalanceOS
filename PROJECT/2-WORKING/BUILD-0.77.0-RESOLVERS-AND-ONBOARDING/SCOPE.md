---
title: "Build 0.77.0 Resolvers, Diagnostics, and Onboarding Hardening Scope"
status: "Draft"
created: 2026-08-21
updated: 2026-08-21
owner: noel
goal: "Live Slack user resolution, doctor diagnostics for tribal lookup files, and repo roots discovery hardening"
gh_issue: 114
source: https://github.com/HiQS-Suite/rebalanceOS/issues/114
related: [115, 116, 113]
effort: 3
complexity: 2
risk: 2
phases: 3
ratings_provisional: false
roadmap_exempt: false
---

# Build 0.77.0 — Resolvers, Diagnostics, and Onboarding Hardening (#114, #115, #116)

## Status

| What was just completed | What's next |
|---|---|
| Phase briefs and MARATHON.yaml authored for Issues #114, #115, #116. | Execute preflight, contract validation, and marathon dry-run. |

## Overview

Decomposes the three follow-up items from #113 into a phased implementation marathon:
- **Phase `ro1` (#114)**: Implement live Slack user resolution and cache write-through in `src/rebalance/ingest/slack_users.py` with fallback to publisher-provided names and comprehensive test coverage in `tests/test_slack_users.py`.
- **Phase `ro2` (#115)**: Add doctor diagnostic check for missing `temp/slack_users.json` when Sleuth records exist in `src/rebalance/doctor.py`, and register an optional lifecycle onboarding stage in `src/rebalance/ingest/lifecycle.py`.
- **Phase `ro3` (#116)**: Align `local_repo_roots` messaging in `src/rebalance/ingest/github_coverage.py` (condensing 60 uncoverable lines into a single honest summary when roots are unset), add doctor remediation hints, and provide an onboarding auto-detect stage in `src/rebalance/ingest/lifecycle.py`.

## Swarm Preflight Contract

```json
{
  "target": { "repo": ".", "ref": "development" },
  "gate": ".venv/bin/pytest tests/ -q",
  "fix_probes": [
    { "type": "path_absent", "path": "tests/test_slack_users.py" },
    { "type": "grep_absent", "path": "src/rebalance/doctor.py", "pattern": "_check_slack_users" },
    { "type": "grep_absent", "path": "src/rebalance/ingest/lifecycle.py", "pattern": "local_repo_roots_configured" },
    { "type": "grep_absent", "path": "src/rebalance/ingest/github_coverage.py", "pattern": "local repo scanning is off" }
  ],
  "artifacts": [
    "src/rebalance/ingest/slack_users.py",
    "src/rebalance/ingest/config.py",
    "src/rebalance/doctor.py",
    "src/rebalance/ingest/lifecycle.py",
    "src/rebalance/ingest/github_coverage.py",
    "tests/test_slack_users.py",
    "tests/test_doctor.py",
    "tests/test_lifecycle_contract.py",
    "tests/test_github_coverage.py"
  ],
  "artifacts_new": [
    "tests/test_slack_users.py"
  ],
  "remediation": {
    "source": "issues#114,#115,#116",
    "criteria": "Live Slack resolution provides write-through caching without silent degradation; doctor checks and onboarding stages surface slack_users.json and local_repo_roots configuration gaps cleanly; coverage checker emits a concise summary when local roots are unset."
  },
  "lanes": {
    "agy_safe": [
      "src/rebalance/ingest/slack_users.py",
      "src/rebalance/ingest/config.py",
      "src/rebalance/doctor.py",
      "src/rebalance/ingest/lifecycle.py",
      "src/rebalance/ingest/github_coverage.py",
      "tests/test_slack_users.py",
      "tests/test_doctor.py",
      "tests/test_lifecycle_contract.py",
      "tests/test_github_coverage.py"
    ],
    "orchestrator_only": []
  }
}
```

## Execution

```bash
.xyz/relay-automation/marathon.sh \
  --plan PROJECT/2-WORKING/BUILD-0.77.0-RESOLVERS-AND-ONBOARDING/MARATHON.yaml \
  --pre-advance-cmd ".venv/bin/pytest tests/ -q" \
  --dry-run
```
