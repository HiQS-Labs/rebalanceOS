import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

from rebalance.ingest.db import db_connection
from rebalance.lib.time_ops import now_iso

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
            synced_at TEXT NOT NULL
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS clio_prompts_ts ON clio_prompts (timestamp)")


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
    
    jsonl_path = Path(os.path.expanduser("~/.claude/prompt-log.jsonl"))
    if not jsonl_path.exists():
        return ClioSyncResult(0, 0, 0, round(time.monotonic() - start, 2), skipped=True, reason="no prompt-log found")

    synced_at = now_iso()
    prompts_fetched = inserted = unchanged = 0

    with db_connection(database_path) as conn:
        ensure_clio_schema(conn)
        
        # Load all existing IDs to avoid expensive upserts if not needed
        existing = {row[0] for row in conn.execute("SELECT id FROM clio_prompts").fetchall()}
        
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
                
                if record_id in existing:
                    unchanged += 1
                    continue
                
                conn.execute(
                    """
                    INSERT INTO clio_prompts (id, timestamp, session_id, prompt, agent, synced_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (record_id, ts, session_id, prompt, agent, synced_at)
                )
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
    
    rows = conn.execute(
        """
        SELECT id, timestamp, session_id, prompt, agent, synced_at
        FROM clio_prompts
        """
    ).fetchall()
    
    for row in rows:
        prompt_text = row["prompt"] or ""
        if not prompt_text.strip():
            continue
            
        yield SemanticDoc(
            source_pk=row["id"],
            doc_kind="clio_prompt",
            title=f"CLIO Prompt ({row['agent'] or 'claude'})",
            body=prompt_text,
            metadata={
                "session_id": row["session_id"],
                "timestamp": row["timestamp"],
                "agent": row["agent"] or "",
            },
            created_at=row["timestamp"],
            updated_at=row["synced_at"],
        )
