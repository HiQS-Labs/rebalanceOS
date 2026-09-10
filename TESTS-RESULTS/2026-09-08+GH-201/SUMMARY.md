# Benchmark Protocol & Technical Spike Results: GH-201
**Campaign**: `2026-09-08+GH-201`  
**Tracking Issue**: [#201](https://github.com/HiQS-Labs/rebalanceOS/issues/201)  
**Working Document**: [`PROJECT/2-WORKING/GH-201-GITCANARY-PATTERNS.md`](file:///Users/noelsaw/Documents/GH Repos/rebalanceOS-gh201/PROJECT/2-WORKING/GH-201-GITCANARY-PATTERNS.md)  
**Date**: 2026-09-08  
**Operator**: noel  

---

## Executive Summary & Go / No-Go Verdict

- **Decision**: **NO-GO (HALT ROLLOUT)**
- **Verdict Rationale**: Average probe latency 609.1ms exceeds 500ms threshold
- **Production Zero-Mutation Guarantee**: Verified. `rebalance.db` opened strictly with `PRAGMA query_only = ON;` and `file:...?mode=ro`. Zero DDL, zero DML, zero git mutations performed on working copies.
- **Average Remote Peek Latency**: **609.1ms** (Min: 489.8ms, Max: 896.6ms) vs 500ms ceiling.
- **Subprocess Safety**: 7 / 7 cases passed with zero askpass/credential prompt hangs, verified descendant process termination, and zero zombie processes.
- **Contract & Recovery Verification**: 100% passed across all Stage 0B sandbox tests (R2 complete ref-map cache hit, failed-file-read retry, secondary branch movement, stale scheduler overlap rejection, two-store battery deferral, AC backlog drain, force_reembed vector preservation, and red control) using shipped production modules directly.

---

## Stage 0A: Live Read-Only Compatibility Sweep

| Repo | Canonical Remote URL | Branch | Remote Peek SHA | SQLite Stored SHA | Divergence Match? | Latency (ms) | Probe Status |
|---|---|---|---|---|---|---|---|
| `hiqs-labs/rebalanceos` | `https://github.com/hiqs-labs/rebalanceos.git` | `development` | `0bffc4dab7` | `None` | No | 489.8 | `OK` |
| `hiqs-labs/gitcanary-fork` | `https://github.com/hiqs-labs/gitcanary-fork.git` | `development` | `14da205413` | `None` | No | 507.8 | `OK` |
| `hypercart-dev-tools/ask-self` | `https://github.com/hypercart-dev-tools/ask-self.git` | `main` | `461574f545` | `None` | No | 896.6 | `OK` |
| `deusdata/codebase-memory-mcp` | `https://github.com/deusdata/codebase-memory-mcp.git` | `main` | `055fbb7d82` | `None` | No | 657.7 | `OK` |
| `aider-ai/aider` | `https://github.com/aider-ai/aider.git` | `development` | `5dc9490bb3` | `None` | No | 638.5 | `OK` |
| `hypercart-dev-tools/ai-ddtk-fix-iterate-loop` | `https://github.com/hypercart-dev-tools/ai-ddtk-fix-iterate-loop.git` | `main` | `61d608df8d` | `None` | No | 587.7 | `OK` |
| `hiqs-labs/aegis-sleuth-slackbot` | `https://github.com/hiqs-labs/aegis-sleuth-slackbot.git` | `development` | `b462d43912` | `None` | No | 586.1 | `OK` |
| `hiqs-labs/agentchorus-skill` | `https://github.com/hiqs-labs/agentchorus-skill.git` | `main` | `2b1353d1bf` | `None` | No | 508.6 | `OK` |

### Subprocess Safety Matrix

| Test Case | Description | Result | Latency / Metric | Notes |
|---|---|---|---|---|
| Case 1 | HTTPS credential-helper / askpass hang prevention | PASS | 1060.65ms | Production peek_remote_refs failed cleanly without interactive prompt hang |
| Case 2 | Conflicting SSH command options isolation | PASS | 87.01ms | Production build_hardened_ssh_command handled invalid SSH options cleanly without hang |
| Case 3 | Offline network (exit 128 / unreachable host) | PASS | 74.14ms | Offline network cleanly returns None without uncaught exception |
| Case 4 | Absent git executable simulation | PASS | N/A | Production run_git raises standard OSError; degrades to authoritative fallback |
| Case 5 | Detached / unborn HEAD repo handling | PASS | N/A | Unborn repo without remote handled cleanly by peek_remote_refs |
| Case 6 | Subprocess timeout & descendant cleanup | PASS | 515.88ms | run_git killed hung process and child descendant (PID 41363) cleanly |
| Case 7 | Empty / malformed output parsing | PASS | N/A | Malformed output safely rejected by production peek_remote_refs |

---

## Stage 0B: Sandboxed Read/Write Contract & Recovery Tests

| Test Suite | Assertion & Scenario | Status | Contract Finding |
|---|---|---|---|
| Test B1 | First-run on empty database | PASS | Clean cache-miss on empty table |
| Test B2 | Checkpoint publication & cache-hit equality | PASS | Checkpoint written and matches exact ref map |
| Test B3 | Failed-file-read retry control (Codex R2) | PASS | Production backfill_commits flags incomplete rows and skips checkpoint on file errors |
| Test B4 | Unchanged-default-tip / changed-other-branch (Codex R2) | PASS | Production is_commit_walk_cached rejects cache hit when secondary branch moves |
| Test B5 | Branch addition and deletion invalidation (Codex R2) | PASS | Production is_commit_walk_cached invalidates cache on branch add/delete |
| Test B6 | Stale scheduler overlap rejection (SCHEDULER.md:72) | PASS | Production atomic UPSERT conditional predicate rejected stale snapshot write |
| Test B7 | Negative broken checkpoint control | PASS | Empty/corrupted ref proof safely yields cache-miss and shallow clone refused |
| Test B8 | Widened lookback window invalidation | PASS | Widened lookback window forces cache-miss |
| Test B9 | Two-store battery recovery & red control (Codex R3/R5/R6) | PASS | Production refresh_index, embed_chunks, two-store battery deferral, AC drain, and red control verified |

---

## Threats to Validity

1. **Network Fluctuations**: `git ls-remote` latency is subject to GitHub edge CDN response times. Under network instability, per-probe 2.0s timeout and authoritative fallback prevent ingest blockage.
2. **Local Clone Branch Tracking**: The probe reflects the remote's canonical `refs/heads/*`. If a developer creates local-only branches without pushing, those remain un-tracked by remote peeking (as intended: local unpushed work is private).
3. **Scheduler Overlap Resolution**: In high-frequency multi-process scheduler configurations, checkpoint writes rely on SQLite WAL locking and monotonic verified timestamps.
