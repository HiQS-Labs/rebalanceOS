-- 0010: per-device agent-session activity (GH-375).
--
-- agent_session_activity holds one row per (source, device, repo, UTC day, agent
-- provider) derived from a local agent harness's session store. The first source is
-- T3 Code ('t3-code', written only by ingest/t3_code.py): metadata counts only, never
-- message text. Keyed by `source` so a later harness can write here without a schema
-- change. github_activity and its frozen hiqs_work_activity output are untouched.
--
-- agent_session_source_health persists one health row per (source, device) — status
-- ok | missing | drift | error, the observed upstream schema version and the last
-- success — so `rebalance doctor` reports the source from this DB alone and can tell
-- a successful empty scan from no scan.
--
-- branches_json / pr_urls_json are sorted JSON arrays. Additive + idempotent
-- (IF NOT EXISTS). No BEGIN/COMMIT (the runner owns the transaction; see README.md).

CREATE TABLE IF NOT EXISTS agent_session_activity (
    source          TEXT    NOT NULL,
    device_id       TEXT    NOT NULL,
    repo_full_name  TEXT    NOT NULL,
    day             TEXT    NOT NULL,
    provider        TEXT    NOT NULL,
    threads         INTEGER NOT NULL DEFAULT 0,
    runs            INTEGER NOT NULL DEFAULT 0,
    runs_completed  INTEGER NOT NULL DEFAULT 0,
    user_prompts    INTEGER NOT NULL DEFAULT 0,
    agent_threads   INTEGER NOT NULL DEFAULT 0,
    branches_json   TEXT    NOT NULL DEFAULT '[]',
    pr_urls_json    TEXT    NOT NULL DEFAULT '[]',
    first_at        TEXT,
    last_at         TEXT,
    scanned_at      TEXT    NOT NULL,
    PRIMARY KEY (source, device_id, repo_full_name, day, provider)
);

CREATE INDEX IF NOT EXISTS idx_agent_session_activity_day
    ON agent_session_activity (day);

CREATE TABLE IF NOT EXISTS agent_session_source_health (
    source                   TEXT NOT NULL,
    device_id                TEXT NOT NULL,
    last_attempt_at          TEXT NOT NULL,
    last_success_at          TEXT,
    status                   TEXT NOT NULL,
    observed_schema_version  INTEGER,
    message                  TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (source, device_id)
);
