import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Iterator

from rebalance.ingest.db import db_connection
from rebalance.ingest.db.connection import db_connection_readonly
from rebalance.lib.time_ops import now_iso
from rebalance.paths import resolve_clio_prompt_log_path

if TYPE_CHECKING:
    # Import-time only: the runtime import lives inside clio_semantic_docs to
    # keep this module out of semantic_index's import cycle.
    from rebalance.ingest.semantic_index import SemanticDoc

logger = logging.getLogger(__name__)


def ensure_clio_schema(conn: Any) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS clio_prompts (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            session_id TEXT NOT NULL,
            prompt TEXT NOT NULL,
            agent TEXT,
            repo TEXT,
            synced_at TEXT NOT NULL
        )
        """
    )

    conn.execute("CREATE INDEX IF NOT EXISTS clio_prompts_ts ON clio_prompts (timestamp)")

    # Migration: add repo if missing
    columns = {col[1] for col in conn.execute("PRAGMA table_info(clio_prompts)").fetchall()}
    if "repo" not in columns:
        conn.execute("ALTER TABLE clio_prompts ADD COLUMN repo TEXT")
    if "source_records" not in columns:
        conn.execute("ALTER TABLE clio_prompts ADD COLUMN source_records TEXT NOT NULL DEFAULT '[]'")


def filter_prompt_metadata(prompt: str) -> str:
    """Filter out relay metadata blocks and other noise before storing."""
    if not prompt:
        return prompt
    # 1. Filter out RELAY AUTOMATION blocks
    prompt = re.sub(
        r"<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->.*?<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->",
        "",
        prompt,
        flags=re.DOTALL,
    )
    # 2. Filter out <SYSTEM_MESSAGE>...</SYSTEM_MESSAGE>
    prompt = re.sub(r"<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>", "", prompt, flags=re.DOTALL)
    # 3. Clean up NEXT/STATUS headers if they are left behind
    prompt = re.sub(r"^NEXT:.*\n", "", prompt, flags=re.MULTILINE)
    prompt = re.sub(r"^STATUS:.*\n", "", prompt, flags=re.MULTILINE)
    return prompt.strip()


def load_recent_clio_prompts(database_path: Path, cutoff_iso: str, limit: int = 16) -> list[dict[str, Any]]:
    """Return recent persisted CLIO prompts without refreshing or mutating the source."""
    try:
        with db_connection_readonly(database_path) as conn:
            columns = {row[1] for row in conn.execute("PRAGMA table_info(clio_prompts)")}
            sources = "source_records" if "source_records" in columns else "'[]' AS source_records"
            rows = conn.execute(
                f"SELECT id,timestamp,prompt,agent,repo,{sources} FROM clio_prompts "
                "WHERE julianday(timestamp) >= julianday(?) ORDER BY timestamp DESC LIMIT ?",
                (cutoff_iso, int(limit)),
            ).fetchall()
    except Exception:  # noqa: BLE001 — absent/not-yet-migrated DB is an empty read surface
        return []
    return [dict(row) | {"source_records": json.loads(row["source_records"])} for row in rows]


@dataclass(frozen=True)
class ClioSyncResult:
    prompts_fetched: int
    prompts_inserted: int
    prompts_unchanged: int
    elapsed_seconds: float
    skipped: bool = False
    reason: str = ""


def sync_clio_prompts(database_path: Path) -> ClioSyncResult:
    start = time.monotonic()

    jsonl_path = resolve_clio_prompt_log_path()
    if not jsonl_path.exists():
        return ClioSyncResult(0, 0, 0, round(time.monotonic() - start, 2), skipped=True, reason="no prompt-log found")

    synced_at = now_iso()
    prompts_fetched = inserted = unchanged = 0

    with db_connection(database_path) as conn:
        ensure_clio_schema(conn)

        # Load all existing IDs to avoid expensive upserts if not needed
        existing = {
            row[0]: json.loads(row[1]) for row in conn.execute("SELECT id, source_records FROM clio_prompts").fetchall()
        }

        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or not line.startswith("{"):
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue

                # Derive ID: session_id + timestamp
                # The exporter format: {"timestamp": "...", "session_id": "...", "prompt": "..."}
                # Optional "agent" added in GH-139
                ts = data.get("timestamp", "").strip()
                session_id = data.get("session_id", "").strip()
                prompt = data.get("prompt", "").strip()
                agent = data.get("agent", "")
                repo = data.get("repo", "")

                prompt = filter_prompt_metadata(prompt)

                if not ts or not session_id or not prompt:
                    continue

                # Use a composite ID since multiple prompts could be in the same second?
                # Actually, session_id is a UUID for the run. timestamp + session_id is robust.
                # However, multiple prompts in the same session at the same second is possible.
                # Let's hash the prompt content for uniqueness.
                import hashlib

                content_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:16]
                record_id = f"{session_id}_{ts}_{content_hash}"

                prompts_fetched += 1

                # Keep the existing projection key: adopting canonical keys here
                # would duplicate previously indexed history. Multiple canonical
                # records may project to one filtered prompt, so retain every link.
                sources = existing.get(record_id, []).copy()
                source_id, origin = data.get("record_id"), data.get("origin_id")
                if isinstance(source_id, str) and source_id and isinstance(origin, str) and origin:
                    reference = {"record_id": source_id, "origin_id": origin}
                    if reference not in sources:
                        sources.append(reference)
                        sources.sort(key=lambda item: (item["record_id"], item["origin_id"]))

                if record_id in existing:
                    if sources != existing[record_id]:
                        conn.execute(
                            "UPDATE clio_prompts SET source_records=?, synced_at=? WHERE id=?",
                            (json.dumps(sources), synced_at, record_id),
                        )
                        existing[record_id] = sources
                    unchanged += 1
                    continue

                conn.execute(
                    """
                    INSERT INTO clio_prompts (id, timestamp, session_id, prompt, agent, repo, synced_at, source_records)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (record_id, ts, session_id, prompt, agent, repo, synced_at, json.dumps(sources)),
                )
                existing[record_id] = sources
                inserted += 1

        conn.commit()

    return ClioSyncResult(
        prompts_fetched=prompts_fetched,
        prompts_inserted=inserted,
        prompts_unchanged=unchanged,
        elapsed_seconds=round(time.monotonic() - start, 2),
    )


def clio_semantic_docs(conn: Any) -> "Iterator[SemanticDoc]":
    from rebalance.ingest.semantic_index import SemanticDoc  # noqa: PLC0415

    # sync_clio_prompts only creates the table once a prompt log exists; without
    # this, the semantic stage raised on every CLIO-less machine and rolled back
    # the rest of its pass.
    ensure_clio_schema(conn)
    rows = conn.execute(
        """
        SELECT id, timestamp, session_id, prompt, agent, repo, synced_at, source_records
        FROM clio_prompts
        """
    ).fetchall()

    for row in rows:
        prompt_text = row["prompt"] or ""
        if not prompt_text.strip():
            continue

        # Cap for SemanticDoc embedding
        if len(prompt_text) > 4000:
            prompt_text = prompt_text[:3997] + "..."

        yield SemanticDoc(
            source_pk=row["id"],
            doc_kind="clio_prompt",
            title=f"CLIO Prompt ({row['agent'] or 'claude'})",
            body=prompt_text,
            metadata={
                "session_id": row["session_id"],
                "timestamp": row["timestamp"],
                "agent": row["agent"] or "",
                "repo": row["repo"] or "",
                "source_records": json.loads(row["source_records"]),
            },
            created_at=row["timestamp"],
            updated_at=row["synced_at"],
        )
