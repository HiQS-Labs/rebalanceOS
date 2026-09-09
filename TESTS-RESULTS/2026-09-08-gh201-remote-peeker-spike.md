# Benchmark Protocol & Technical Spike Results: GH-201
**Campaign**: `2026-09-08+GH-201`  
**Tracking Issue**: [#201](https://github.com/HiQS-Labs/rebalanceOS/issues/201)  
**Working Document**: [`PROJECT/2-WORKING/GH-201-GITCANARY-PATTERNS.md`](file:///Users/noelsaw/Documents/GH Repos/rebalanceOS-gh201/PROJECT/2-WORKING/GH-201-GITCANARY-PATTERNS.md)  
**Date**: 2026-09-08  
**Operator**: noel  

---

## Executive Summary & Go / No-Go Verdict

- **Decision**: **GO (PROCEED TO PHASE 1)**
- **Verdict Rationale**: All stop rules satisfied: 0 hangs/leaks, average latency 414.7ms (threshold: <=500ms)
- **Production Zero-Mutation Guarantee**: Verified. `rebalance.db` opened strictly with `PRAGMA query_only = ON;` and `file:...?mode=ro`. Zero DDL, zero DML, zero git mutations performed on working copies.
- **Average Remote Peek Latency**: **414.7ms** (Min: 321.2ms, Max: 762.6ms) vs 500ms ceiling.
- **Subprocess Safety**: 7 / 7 cases passed with zero askpass/credential prompt hangs and zero zombie processes.
- **Contract & Recovery Verification**: 100% passed across all Stage 0B sandbox tests (R2 complete ref-map cache hit, failed-file-read retry, secondary branch movement, stale scheduler overlap rejection, two-store battery deferral, AC backlog drain, force_reembed vector preservation, and red control).

---

## Stage 0A: Live Read-Only Compatibility Sweep

| Repo | Canonical Remote URL | Branch | Remote Peek SHA | SQLite Stored SHA | Divergence Match? | Latency (ms) | Probe Status |
|---|---|---|---|---|---|---|---|
| `hiqs-labs/rebalanceos` | `https://github.com/HiQS-Labs/rebalanceOS.git` | `development` | `0bffc4dab7` | `None` | No | 321.2 | `OK` |
| `hiqs-labs/gitcanary-fork` | `https://github.com/HiQS-Labs/GitCanary-fork.git` | `development` | `14da205413` | `None` | No | 424.8 | `OK` |
| `hypercart-dev-tools/ask-self` | `https://github.com/Hypercart-Dev-Tools/ask-self.git` | `main` | `461574f545` | `None` | No | 762.6 | `OK` |
| `deusdata/codebase-memory-mcp` | `https://github.com/DeusData/codebase-memory-mcp.git` | `main` | `b5185d10c4` | `None` | No | 355.3 | `OK` |
| `aider-ai/aider` | `https://github.com/Aider-AI/aider.git` | `development` | `5dc9490bb3` | `None` | No | 403.9 | `OK` |
| `hypercart-dev-tools/ai-ddtk-fix-iterate-loop` | `https://github.com/Hypercart-Dev-Tools/AI-DDTK-Fix-Iterate-Loop.git` | `main` | `61d608df8d` | `None` | No | 342.0 | `OK` |
| `hiqs-labs/aegis-sleuth-slackbot` | `https://github.com/HiQS-Labs/AEGIS-Sleuth-Slackbot.git` | `development` | `5d04348b7f` | `None` | No | 337.6 | `OK` |
| `hiqs-labs/agentchorus-skill` | `https://github.com/HiQS-Labs/AgentChorus-Skill` | `main` | `2b1353d1bf` | `None` | No | 369.8 | `OK` |

### Subprocess Safety Matrix

| Test Case | Description | Result | Latency / Metric | Notes |
|---|---|---|---|---|
| Case 1 | HTTPS credential-helper / askpass hang prevention | PASS | 437.21ms | Failed cleanly without interactive prompt hang |
| Case 2 | Conflicting SSH command options isolation | PASS | 29.36ms | Handled invalid SSH options cleanly without hang: command-line line 0: Bad port '99999'.
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists. |
| Case 3 | Offline network (exit 128 / unreachable host) | PASS | 35.2ms | Offline network cleanly returns None without uncaught exception: fatal: unable to access 'https://invalid-domain-xyz-404.example.com/repo.git/': Could not resolve host: invalid-domain-xyz-404.example.com |
| Case 4 | Absent git executable simulation | PASS | N/A | Executable error raised and caught; degrades to authoritative fallback |
| Case 5 | Detached / unborn HEAD repo handling | PASS | N/A | Unborn repo without remote handled cleanly: fatal: 'origin' does not appear to be a git repository
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists. |
| Case 6 | Subprocess timeout & zombie process cleanup | PASS | 506.45ms | Timeout terminates promptly with zero zombie leak |
| Case 7 | Empty / malformed output parsing | PASS | N/A | Malformed output safely rejected and returns empty map |

---

## Stage 0B: Sandboxed Read/Write Contract & Recovery Tests

| Test Suite | Assertion & Scenario | Status | Contract Finding |
|---|---|---|---|
| Test B1 | First-run on empty database | PASS | Clean cache-miss on empty table |
| Test B2 | Checkpoint publication & cache-hit equality | PASS | Checkpoint written and matches exact ref map |
| Test B3 | Failed-file-read retry control (Codex R2) | PASS | Failed file reads refuse checkpoint advance and keep row retryable |
| Test B4 | Unchanged-default-tip / changed-other-branch (Codex R2) | PASS | Cache-hit rejected when non-default branch moves |
| Test B5 | Branch addition and deletion invalidation (Codex R2) | PASS | Branch addition or deletion cleanly invalidates cache |
| Test B6 | Stale scheduler overlap rejection (SCHEDULER.md:72) | PASS | Stale walk snapshot rejected by conditional verified_at check |
| Test B7 | Negative broken checkpoint control | PASS | Empty/corrupted ref proof safely yields cache-miss |
| Test B8 | Widened lookback window invalidation | PASS | Widened lookback window forces cache-miss |
| Test B9 | Two-store battery recovery & red control (Codex R3) | PASS | Two-store battery deferral, AC drain, force_reembed preservation, and red control all verified |

---

## Threats to Validity

1. **Network Fluctuations**: `git ls-remote` latency is subject to GitHub edge CDN response times. Under network instability, per-probe 2.0s timeout and authoritative fallback prevent ingest blockage.
2. **Local Clone Branch Tracking**: The probe reflects the remote's canonical `refs/heads/*`. If a developer creates local-only branches without pushing, those remain un-tracked by remote peeking (as intended: local unpushed work is private).
3. **Scheduler Overlap Resolution**: In high-frequency multi-process scheduler configurations, checkpoint writes rely on SQLite WAL locking and monotonic verified timestamps.
