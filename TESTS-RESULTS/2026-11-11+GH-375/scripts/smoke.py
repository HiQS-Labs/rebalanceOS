"""GH-375 live smoke: dry-run against the real T3 store vs a direct read-only count. No writes."""
import json, sqlite3, sys, hashlib
from pathlib import Path
from unittest.mock import patch
from rebalance.ingest import t3_code
from rebalance.lib import time_ops
from rebalance.lib.git_ops import parse_github_remote_url, run_git

t3 = Path.home() / ".t3/userdata/statev2.sqlite"
scratch_db = Path(sys.argv[1])  # never created: dry runs write nothing
cfg = {"t3_code_activity_enabled": True, "t3_code_db_path": str(t3), "t3_code_window_days": 14,
       "watch_repos_from_agent_sessions": False}
start = time_ops.utc_date_days_ago(14)
alias = {}
def anon(repo):
    return alias.setdefault(repo, f"repo-{chr(65 + len(alias))}")

res1 = t3_code.sync_t3_code_activity(scratch_db, dry_run=True, config=cfg)
res2 = t3_code.sync_t3_code_activity(scratch_db, dry_run=True, config=cfg)
agg = res1["aggregates"]
coll = {}
for r in agg:
    c = coll.setdefault(r["repo_full_name"], {"runs": 0, "user_prompts": 0, "providers": {}})
    c["runs"] += r["runs"]; c["user_prompts"] += r["user_prompts"]
    p = c["providers"].setdefault(r["provider"], {"runs": 0, "thread_days": 0})
    p["runs"] += r["runs"]; p["thread_days"] += r["threads"]

# Direct count (independent SQL, counts only, read-only).
conn = sqlite3.connect(f"{t3.resolve().as_uri()}?mode=ro", uri=True); conn.execute("PRAGMA query_only=ON")
roots = dict(conn.execute("SELECT t.thread_id, p.workspace_root FROM orchestration_v2_projection_threads t JOIN projection_projects p ON p.project_id=t.project_id"))
active = {tid for (tid,) in conn.execute("SELECT thread_id FROM orchestration_v2_projection_runs WHERE requested_at >= ? UNION SELECT thread_id FROM orchestration_v2_projection_messages WHERE created_at >= ?", (start, start))}
runs = conn.execute("SELECT thread_id, provider, COUNT(*) FROM orchestration_v2_projection_runs WHERE requested_at >= ? GROUP BY 1,2", (start,)).fetchall()
prompts = conn.execute("SELECT thread_id, COUNT(*) FROM orchestration_v2_projection_messages WHERE created_at >= ? AND role='user' AND json_extract(payload_json,'$.createdBy')='user' GROUP BY 1", (start,)).fetchall()
conn.close()
def repo_of(root):
    p = run_git(Path(root), "remote", "get-url", "origin", timeout=10)
    return parse_github_remote_url(p.stdout) if p.returncode == 0 else None
repo_cache = {}
def repo_for(tid):
    root = roots.get(tid)
    if root not in repo_cache: repo_cache[root] = repo_of(root) if root else None
    return repo_cache[root]
direct = {}
for tid in active:
    repo = repo_for(tid)
    if repo: direct.setdefault(repo, {"threads": 0, "runs": 0, "user_prompts": 0, "providers": {}})["threads"] += 1
for tid, prov, n in runs:
    repo = repo_for(tid)
    if repo:
        d = direct[repo]; d["runs"] += n; d["providers"][prov] = d["providers"].get(prov, 0) + n
for tid, n in prompts:
    repo = repo_for(tid)
    if repo: direct[repo]["user_prompts"] += n

print(f"window_start={start} rows={res1['rows']} unresolved_roots={res1['unresolved_roots']} schema_version={res1['schema_version']}")
print(f"rerun identical aggregates: {res1['aggregates'] == res2['aggregates']}")
print(f"scratch DB created by dry runs: {scratch_db.exists()}")
print("repo | direct threads active | direct runs | collector runs | direct prompts | collector prompts | direct provider runs | collector provider runs/thread_days")
ok = set(direct) == set(coll)
for repo in sorted(set(direct) | set(coll), key=lambda r: anon(r)):
    d, c = direct.get(repo, {}), coll.get(repo, {})
    dprov = dict(sorted(d.get("providers", {}).items())); cprov = {k: v for k, v in sorted(c.get("providers", {}).items())}
    match = d.get("runs") == c.get("runs") and d.get("user_prompts") == c.get("user_prompts") and dprov == {k: v["runs"] for k, v in cprov.items() if v["runs"]}
    ok = ok and match
    print(f"{anon(repo)} | {d.get('threads')} | {d.get('runs')} | {c.get('runs')} | {d.get('user_prompts')} | {c.get('user_prompts')} | {dprov} | {cprov} | {'MATCH' if match else 'MISMATCH'}")
print(f"repo set equal: {set(direct) == set(coll)}  overall: {'PASS' if ok else 'FAIL'}")
# Flag off: skipped without opening the store.
with patch.object(t3_code, "_open_t3", side_effect=AssertionError("opened")):
    off = t3_code.sync_t3_code_activity(scratch_db, dry_run=False, config={**cfg, "t3_code_activity_enabled": False})
print(f"flag off: {off}")
print(f"scratch DB created after flag-off run: {scratch_db.exists()}")
