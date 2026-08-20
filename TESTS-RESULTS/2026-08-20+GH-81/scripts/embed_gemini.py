"""Embed the frozen bake-off corpus with Gemini's hosted embedding model.

Gemini is the only lane with a real asymmetry knob in its API: passages go in
as RETRIEVAL_DOCUMENT, queries as RETRIEVAL_QUERY (protocol 2). Passages are
done here; the query side happens at scoring time.

Reads only temp/bakeoff/corpus.db. Resumable — re-running continues where it
stopped, because a partial run over ~10k documents is expensive to throw away.
"""

from __future__ import annotations

import json
import os
import sqlite3
import struct
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "src")

import sqlite_vec  # noqa: E402

from rebalance.ingest.config import get_gemini_api_key  # noqa: E402

CORPUS = "temp/bakeoff/corpus.db"
OUT = "temp/bakeoff/emb-gemini.db"
MODEL = "gemini-embedding-001"
DIM = 3072
BATCH = 100  # the API's documented per-request ceiling for batchEmbedContents
ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:batchEmbedContents"


def vec_bytes(v) -> bytes:
    return struct.pack(f"{len(v)}f", *v)


def l2(v):
    n = sum(x * x for x in v) ** 0.5
    return [x / n for x in v] if n else v


def connect(path):
    conn = sqlite3.connect(path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def embed_batch(texts, api_key, *, task="RETRIEVAL_DOCUMENT", attempt=0):
    payload = {
        "requests": [{"model": f"models/{MODEL}", "content": {"parts": [{"text": t}]}, "taskType": task} for t in texts]
    }
    req = urllib.request.Request(
        f"{ENDPOINT}?key={api_key}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            body = json.loads(r.read())
        return [e["values"] for e in body["embeddings"]]
    except urllib.error.HTTPError as exc:
        # 429/5xx are the retryable ones; back off rather than losing the run.
        if exc.code in (429, 500, 502, 503, 504) and attempt < 6:
            wait = min(60, 2**attempt * 5)
            print(f"    HTTP {exc.code} — retry {attempt + 1} in {wait}s", flush=True)
            time.sleep(wait)
            return embed_batch(texts, api_key, task=task, attempt=attempt + 1)
        raise RuntimeError(f"HTTP {exc.code}: {exc.read()[:400].decode(errors='replace')}") from exc


def main() -> int:
    api_key = get_gemini_api_key()
    if not api_key:
        print("no Gemini API key available", file=sys.stderr)
        return 1

    src = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True)
    rows = src.execute("SELECT doc_id, coalesce(title,''), body FROM docs ORDER BY doc_id").fetchall()
    texts = [(d, (t + "\n\n" + b) if t else b) for d, t, b in rows]

    fresh = not os.path.exists(OUT)
    out = connect(OUT)
    if fresh:
        out.execute(f"CREATE VIRTUAL TABLE vec USING vec0(embedding float[{DIM}])")
        out.execute("CREATE TABLE map (rowid INTEGER PRIMARY KEY, doc_id INTEGER NOT NULL)")
        out.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        out.commit()

    done = {r[0] for r in out.execute("SELECT doc_id FROM map")}
    todo = [(d, s) for d, s in texts if d not in done]
    print(f"[gemini] {len(texts)} docs, {len(done)} already embedded, {len(todo)} to go", flush=True)

    t0 = time.monotonic()
    calls = 0
    for i in range(0, len(todo), BATCH):
        chunk = todo[i : i + BATCH]
        vecs = embed_batch([s for _, s in chunk], api_key)
        calls += 1
        for (doc_id, _), v in zip(chunk, vecs):
            cur = out.execute("INSERT INTO vec(embedding) VALUES (?)", (vec_bytes(l2(v)),))
            out.execute("INSERT INTO map(rowid, doc_id) VALUES (?,?)", (cur.lastrowid, doc_id))
        out.commit()
        el = time.monotonic() - t0
        print(f"[gemini] {i + len(chunk)}/{len(todo)}  {el:.0f}s  ({calls} api calls)", flush=True)

    elapsed = time.monotonic() - t0
    for k, v in [
        ("lane", "gemini"),
        ("model", MODEL),
        ("dim", DIM),
        ("task_type_passage", "RETRIEVAL_DOCUMENT"),
        ("task_type_query", "RETRIEVAL_QUERY"),
        ("n_docs", len(texts)),
        ("normalized", "1"),
        ("api_calls_this_run", calls),
        ("embed_seconds_this_run", round(elapsed, 1)),
    ]:
        out.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (k, str(v)))
    out.commit()
    total = out.execute("SELECT COUNT(*) FROM map").fetchone()[0]
    print(f"[gemini] DONE {total}/{len(texts)} docs, {calls} calls, {elapsed:.0f}s", flush=True)
    return 0 if total == len(texts) else 2


if __name__ == "__main__":
    raise SystemExit(main())
