import json
import logging
import os
import re
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




def filter_prompt_metadata(prompt: str) -> str:
    """Filter out relay metadata blocks and other noise before storing."""
    if not prompt:
        return prompt
    # 1. Filter out RELAY AUTOMATION blocks
    prompt = re.sub(
        r'<!-- ▽ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK ▽ -->.*?<!-- △ RELAY AUTOMATION: DO NOT MODIFY THIS BLOCK △ -->', 
        '', prompt, flags=re.DOTALL
    )
    # 2. Filter out <SYSTEM_MESSAGE>...</SYSTEM_MESSAGE>
    prompt = re.sub(
        r'<SYSTEM_MESSAGE>.*?</SYSTEM_MESSAGE>', 
        '', prompt, flags=re.DOTALL
    )
    # 3. Clean up NEXT/STATUS headers if they are left behind
    prompt = re.sub(r'^NEXT:.*\n', '', prompt, flags=re.MULTILINE)
    prompt = re.sub(r'^STATUS:.*\n', '', prompt, flags=re.MULTILINE)
    return prompt.strip()

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
                
                if record_id in existing:
                    unchanged += 1
                    continue
                
                conn.execute(
                    """
                    INSERT INTO clio_prompts (id, timestamp, session_id, prompt, agent, repo, synced_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (record_id, ts, session_id, prompt, agent, repo, synced_at)
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
        SELECT id, timestamp, session_id, prompt, agent, repo, synced_at
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
            },
            created_at=row["timestamp"],
            updated_at=row["synced_at"],
        )
