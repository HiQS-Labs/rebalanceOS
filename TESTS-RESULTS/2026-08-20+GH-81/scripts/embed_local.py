"""Embed the frozen bake-off corpus with one local sentence-transformers model.

One sidecar database per lane, per protocol 3.1. The live database is opened
read-only when the corpus is built (build step, separate) and never touched
here at all — this script reads only temp/bakeoff/corpus.db.

Usage:  python temp/bakeoff/embed_local.py <lane> <model-name>
"""

from __future__ import annotations

import os
import sqlite3
import struct
import sys
import time

import sqlite_vec

CORPUS = "temp/bakeoff/corpus.db"
BATCH = int(__import__("os").environ.get("BAKEOFF_BATCH", "64"))


def vec_bytes(v) -> bytes:
    return struct.pack(f"{len(v)}f", *v)


def connect(path):
    conn = sqlite3.connect(path)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def main(lane: str, model_name: str) -> int:
    out_path = f"temp/bakeoff/emb-{lane}.db"
    if os.path.exists(out_path):
        os.remove(out_path)

    from sentence_transformers import SentenceTransformer

    print(f"[{lane}] loading {model_name} ...", flush=True)
    t0 = time.monotonic()
    # Device is not part of what this experiment measures, but it must be
    # RECORDED: it changes the embed-time and query-latency secondary metrics,
    # and both local lanes must run on the same one for those to be comparable.
    device = os.environ.get("BAKEOFF_DEVICE") or None
    model = SentenceTransformer(model_name, device=device)
    device = str(model.device)

    # Optional cap on the model's own context window.
    #
    # Needed for Qwen3-Embedding-0.6B, whose native limit is 32,768 tokens:
    # allocating that window across a batch exhausts MPS memory outright
    # (observed: "MPS backend out of memory ... allocated 65.99 GiB"). Capping
    # is a deviation from protocol 3.3's "each lane at its native limit", so it
    # is measured rather than waved through — under Qwen's own tokenizer this
    # corpus runs p50=125, p90=571, p99=1,643, max=14,825 tokens, so a 4,096
    # cap truncates 14 of 10,000 documents (0.14%). That is small enough not to
    # decide anything, and it is recorded in meta either way.
    cap = os.environ.get("BAKEOFF_MAX_SEQ")
    native_max = int(model.max_seq_length)
    if cap:
        model.max_seq_length = min(int(cap), native_max)
    max_seq = int(model.max_seq_length)
    dim = int(model.get_sentence_embedding_dimension())
    print(f"[{lane}] dim={dim} max_seq_length={max_seq} device={device} load={time.monotonic() - t0:.1f}s", flush=True)

    src = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True)
    rows = src.execute("SELECT doc_id, coalesce(title,''), body FROM docs ORDER BY doc_id").fetchall()
    texts = [(d, (t + "\n\n" + b) if t else b) for d, t, b in rows]
    print(f"[{lane}] {len(texts)} docs", flush=True)

    # Truncation is the model's own, at its native limit (protocol 3.3) — no
    # uniform cap. Count how many inputs actually exceed it so the rate can be
    # reported rather than assumed.
    tok = model.tokenizer
    truncated = sum(1 for _, s in texts if len(tok.encode(s, add_special_tokens=False)) > max_seq)
    print(f"[{lane}] over max_seq_length: {truncated} / {len(texts)} ({100 * truncated / len(texts):.1f}%)", flush=True)

    out = connect(out_path)
    out.execute(f"CREATE VIRTUAL TABLE vec USING vec0(embedding float[{dim}])")
    out.execute("CREATE TABLE map (rowid INTEGER PRIMARY KEY, doc_id INTEGER NOT NULL)")
    out.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")

    # One encode() call over the whole corpus, not a hand-rolled loop of fixed
    # slices. sentence-transformers sorts internally by length before batching
    # and restores the original order afterwards, so long documents batch with
    # long and short with short. Feeding it pre-cut doc_id-ordered slices
    # defeats that: every batch pads to its own longest member, and with a p50
    # of 125 tokens against a 4,096 cap almost all the compute went into
    # padding (measured: ~0.34 s/doc, a ~57-minute projection for this corpus).
    # The vectors are identical either way — this is throughput only.
    t0 = time.monotonic()
    vecs = model.encode([s for _, s in texts], normalize_embeddings=True, show_progress_bar=True, batch_size=BATCH)
    for (doc_id, _), v in zip(texts, vecs):
        cur = out.execute("INSERT INTO vec(embedding) VALUES (?)", (vec_bytes(v.tolist()),))
        out.execute("INSERT INTO map(rowid, doc_id) VALUES (?,?)", (cur.lastrowid, doc_id))
    elapsed = time.monotonic() - t0

    for k, v in [
        ("lane", lane),
        ("model", model_name),
        ("dim", dim),
        ("max_seq_length", max_seq),
        ("native_max_seq_length", native_max),
        ("truncated_count", truncated),
        ("truncated_pct", round(100 * truncated / len(texts), 2)),
        ("n_docs", len(texts)),
        ("passage_prefix", ""),
        ("device", device),
        ("normalized", "1"),
        ("embed_seconds", round(elapsed, 1)),
    ]:
        out.execute("INSERT INTO meta VALUES (?,?)", (k, str(v)))
    out.commit()
    print(f"[{lane}] DONE {len(texts)} docs in {elapsed:.0f}s -> {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
