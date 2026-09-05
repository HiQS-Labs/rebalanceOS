"""Shared database layer for rebalance.

Connection factory, schema creation, and typed query helpers. The
implementation is split into submodules:

- ``connection`` — connection factory + ``db_connection`` context manager
- ``schema``     — every ``CREATE TABLE`` statement, grouped by source
- ``github``     — typed query helpers for the ``github_*`` tables
- ``semantic``   — typed query helpers for the semantic-index tables

The connection / schema / github symbols are re-exported here, so
``from rebalance.ingest.db import ...`` keeps working unchanged. The
``github`` and ``semantic`` query helpers are also reachable as submodules
(``from rebalance.ingest.db import github``) for callers that want the
namespaced form.
"""

from __future__ import annotations

from rebalance.ingest.db.connection import db_connection, get_connection
from rebalance.ingest.db.github import (
    repo_last_active,
    repo_meta_names,
    top_active_repos,
)
from rebalance.ingest.db.migrate import current_schema_version, run_migrations
from rebalance.ingest.db.queries import (
    fetch_day_comments,
    fetch_day_commits,
    fetch_day_items,
    fetch_github_balance,
    fetch_open_items_for_projects,
    fetch_open_prs,
    fetch_org_activity,
    fetch_recent_github,
    fetch_release_readiness_data,
    fetch_repo_activity_counts,
    fetch_repo_diagnostics,
    fetch_watched_activity,
)
from rebalance.ingest.db.schema import (
    BASELINE_SCHEMA_VERSION,
    ensure_baseline_schema,
    ensure_calendar_schema,
    ensure_email_schema,
    ensure_github_schema,
    ensure_project_schema,
    ensure_schema,
    ensure_semantic_schema,
)

__all__ = [
    "get_connection",
    "db_connection",
    "ensure_schema",
    "ensure_semantic_schema",
    "ensure_calendar_schema",
    "ensure_email_schema",
    "ensure_github_schema",
    "ensure_project_schema",
    "ensure_baseline_schema",
    "top_active_repos",
    "repo_last_active",
    "repo_meta_names",
    "run_migrations",
    "current_schema_version",
    "BASELINE_SCHEMA_VERSION",
    "fetch_github_balance",
    "fetch_org_activity",
    "fetch_day_commits",
    "fetch_day_items",
    "fetch_day_comments",
    "fetch_watched_activity",
    "fetch_open_items_for_projects",
    "fetch_repo_diagnostics",
    "fetch_release_readiness_data",
    "fetch_recent_github",
    "fetch_repo_activity_counts",
    "fetch_open_prs",
]
