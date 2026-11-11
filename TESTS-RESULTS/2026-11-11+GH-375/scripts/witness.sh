#!/bin/bash
set -u
S="$1"; F=src/rebalance/ingest/t3_code.py
run() { # name file old new -k-expr
  echo "## $1"; echo "mutation: $2 :: replace «$3» → «$4»"
  python3 "$S/mutate.py" "$2" "$3" "$4" || { echo "ANCHOR FAIL"; return; }
  echo "witness: pytest tests/test_t3_code.py -k \"$5\""
  .venv/bin/python -m pytest tests/test_t3_code.py -k "$5" -q -p no:cacheprovider 2>&1 | grep -E "passed|failed|error|ERROR" | tail -1
  git checkout -q -- "$2"; echo; }
echo "# Mutation witnesses — GH-375 (SOP §3.6). Base commit $(git rev-parse --short HEAD). Each guard removed → named test must go red; file restored after each run."; echo
run "schema guard removed" $F '    row = conn.execute(_VERSION_SQL).fetchone()' '    return 2\n    row = conn.execute(_VERSION_SQL).fetchone()' "unsupported_schema"
run "column probes removed (version check kept)" $F '            conn.execute(f"SELECT {columns} FROM {table} LIMIT 0")' '            pass' "missing_column"
run "write transaction removed (delete committed alone)" $F '        conn.execute("BEGIN IMMEDIATE")\n        try:\n            conn.execute(\n                "DELETE FROM agent_session_activity WHERE source = ? AND device_id = ? AND day >= ?",\n                (SOURCE, device_id, window_start),\n            )' '        try:\n            conn.execute(\n                "DELETE FROM agent_session_activity WHERE source = ? AND device_id = ? AND day >= ?",\n                (SOURCE, device_id, window_start),\n            )\n            conn.commit()' "insert_failure"
run "row-joined runs stream (messages joined in)" $F 'FROM orchestration_v2_projection_runs\nWHERE requested_at >= ?\nGROUP BY thread_id, provider, day' 'FROM orchestration_v2_projection_runs\nJOIN orchestration_v2_projection_messages USING (thread_id)\nWHERE requested_at >= ?\nGROUP BY thread_id, provider, day' "edge_cases or predicted_rows"
run "provider fallback removed (no thread default_provider)" $F 'COALESCE(r.provider, t.default_provider) AS provider' 'r.provider AS provider' "edge_cases or predicted_rows"
run "message text read added" $F "SUM(m.role = 'user' AND json_extract(m.payload_json, '\$.createdBy') = 'user') AS user_prompts," "SUM(m.role = 'user' AND json_extract(m.payload_json, '\$.createdBy') = 'user') AS user_prompts, json_extract(m.payload_json, '\$.text') AS leak," "metadata_only"
run "watched-repo flag ignored (always union)" src/rebalance/ingest/index_ops.py '            if get_t3_code_config()["watch_repos_from_agent_sessions"]:' '            if True:' "union_opt_in"
run "dry-run writes health on missing store" $F '        if not dry_run:\n            _record_health(database_path, device_id, "missing"' '        if True:\n            _record_health(database_path, device_id, "missing"' "missing_file or dry_run"
run "doctor ignores the flag" src/rebalance/doctor.py '    if not enabled:\n        retained' '    if False:\n        retained' "doctor"
echo "## control: unmutated tree"; .venv/bin/python -m pytest tests/test_t3_code.py -q -p no:cacheprovider 2>&1 | tail -1
