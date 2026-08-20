"""Score every bake-off lane against the frozen query set (protocol 5).

Six lanes: bge, bge-asym, qwen, qwen-asym, gemini, fts. The *-asym lanes reuse
their base lane's sidecar unchanged — only the query-side embedding differs, so
the asymmetric-prompting question costs one extra query pass and zero extra
corpus embedding.

Significance is a PAIRED test. Every lane answers the same queries, so
between-query difficulty — the dominant variance component — is common to all
of them and cancels. Comparing independent per-lane intervals would throw that
away; an earlier draft of the protocol did exactly that and was corrected in QA.
"""

from __future__ import annotations

import json
import math
import os
import random
import sqlite3
import struct
import sys
import time
from itertools import combinations

import sqlite_vec

sys.path.insert(0, "src")

CORPUS = "temp/bakeoff/corpus.db"
K = 10
BOOT = 10000
SEED = 20260820

BGE_Q = "Represent this sentence for searching relevant passages: "
QWEN_Q = "Instruct: Given a web search query, retrieve relevant passages that answer the query\nQuery: "


def vec_bytes(v) -> bytes:
    return struct.pack(f"{len(v)}f", *v)


def connect_ro(path):
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


# --- retrieval ---------------------------------------------------------------


def vec_ranks(lane_db, qvecs, queries):
    """Rank of each query's target under one embedding lane. None = outside top-K."""
    conn = connect_ro(lane_db)
    out, lat = [], []
    for q, qv in zip(queries, qvecs):
        t0 = time.monotonic()
        rows = conn.execute(
            "SELECT m.doc_id FROM vec v JOIN map m ON m.rowid = v.rowid "
            "WHERE v.embedding MATCH ? AND k = ? ORDER BY distance",
            (vec_bytes(qv), K),
        ).fetchall()
        lat.append(time.monotonic() - t0)
        ids = [r[0] for r in rows]
        out.append(ids.index(q["target_doc_id"]) + 1 if q["target_doc_id"] in ids else None)
    lat.sort()
    return out, lat[len(lat) // 2]


def fts_query(text: str) -> str:
    toks = [t for t in "".join(c if c.isalnum() else " " for c in text).split() if len(t) > 2]
    return " OR ".join(f'"{t}"' for t in toks) or '"x"'


def fts_ranks(queries, k=K):
    conn = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True)
    out = []
    for q in queries:
        rows = conn.execute(
            "SELECT rowid FROM docs_fts WHERE docs_fts MATCH ? ORDER BY rank LIMIT ?", (fts_query(q["query"]), k)
        ).fetchall()
        ids = [r[0] for r in rows]
        out.append(ids.index(q["target_doc_id"]) + 1 if q["target_doc_id"] in ids else None)
    return out


def fts_top50_hit(queries):
    """The lexical-easy / lexical-hard label (protocol 4.2). A LABEL, not a filter."""
    return [r is not None for r in fts_ranks(queries, k=50)]


# --- metrics -----------------------------------------------------------------


def rr(ranks):
    return [0.0 if r is None else 1.0 / r for r in ranks]


def metrics(ranks):
    n = len(ranks) or 1
    hit = lambda k: sum(1 for r in ranks if r is not None and r <= k) / n  # noqa: E731
    return {
        "n": len(ranks),
        "recall@1": round(hit(1), 4),
        "recall@5": round(hit(5), 4),
        "recall@10": round(hit(10), 4),
        "mrr@10": round(sum(rr(ranks)) / n, 4),
    }


def wilcoxon(diffs):
    """Two-sided Wilcoxon signed-rank p-value. Zeros dropped, ties averaged.

    Reciprocal rank is bounded, discrete and heavily tied at 0 and 1, so a
    paired t-test's normality assumption does not hold; signed-rank does not
    need it.
    """
    d = [x for x in diffs if x != 0]
    n = len(d)
    if n == 0:
        return 1.0, 0
    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        avg = (i + j) / 2 + 1
        for t in range(i, j + 1):
            ranks[order[t]] = avg
        i = j + 1
    w_plus = sum(ranks[i] for i in range(n) if d[i] > 0)
    mu = n * (n + 1) / 4
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    if sigma == 0:
        return 1.0, n
    z = (w_plus - mu) / sigma
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    return min(1.0, p), n


def holm(pairs):
    """Holm-Bonferroni. Uniformly more powerful than Bonferroni, same assumptions."""
    ordered = sorted(pairs, key=lambda kv: kv[1])
    m = len(ordered)
    out, prev = {}, 0.0
    for i, (key, p) in enumerate(ordered):
        adj = max(prev, min(1.0, (m - i) * p))
        out[key] = adj
        prev = adj
    return out


def boot_ci(diffs, seed=SEED, n=BOOT):
    """Bootstrap CI on the PAIRED difference — effect size, not a significance gate."""
    if not diffs:
        return (0.0, 0.0)
    rnd = random.Random(seed)
    m = len(diffs)
    meds = []
    for _ in range(n):
        s = [diffs[rnd.randrange(m)] for _ in range(m)]
        s.sort()
        meds.append(s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2)
    meds.sort()
    return (round(meds[int(0.025 * n)], 4), round(meds[int(0.975 * n)], 4))


def boot_ci_mean(diffs, seed=SEED, n=BOOT):
    """Bootstrap CI on the MEAN paired difference — the effect-size figure that
    survives heavy tying, unlike the median."""
    if not diffs:
        return (0.0, 0.0)
    rnd = random.Random(seed)
    m = len(diffs)
    means = sorted(sum(diffs[rnd.randrange(m)] for _ in range(m)) / m for _ in range(n))
    return (round(means[int(0.025 * n)], 4), round(means[int(0.975 * n)], 4))


def median(xs):
    if not xs:
        return 0.0
    s = sorted(xs)
    m = len(s)
    return s[m // 2] if m % 2 else (s[m // 2 - 1] + s[m // 2]) / 2


# --- main --------------------------------------------------------------------


def main() -> int:
    queries = json.load(open("temp/bakeoff/queries.json"))
    print(
        f"queries: {len(queries)}  (A={sum(1 for q in queries if q['set'] == 'A')}, "
        f"B={sum(1 for q in queries if q['set'] == 'B')})"
    )

    # protocol 4.2 validity gate: target must be in the corpus, unique per set.
    corpus = sqlite3.connect(f"file:{CORPUS}?mode=ro", uri=True)
    present = {r[0] for r in corpus.execute("SELECT doc_id FROM docs")}
    bad = [q["qid"] for q in queries if q["target_doc_id"] not in present]
    if bad:
        print(f"GATE FAILURE — targets missing from corpus: {bad}")
        return 2
    print(f"gate: all {len(queries)} targets present in corpus ✓")

    easy = fts_top50_hit(queries)
    for q, e in zip(queries, easy):
        q["lexical"] = "easy" if e else "hard"
    print(f"lexical labels: easy={sum(easy)}  hard={len(easy) - sum(easy)}")

    lanes, latency = {}, {}
    from sentence_transformers import SentenceTransformer

    for lane, db, model_name, prefix in [
        ("bge", "temp/bakeoff/emb-bge.db", "BAAI/bge-small-en-v1.5", ""),
        ("bge-asym", "temp/bakeoff/emb-bge.db", "BAAI/bge-small-en-v1.5", BGE_Q),
        ("qwen", "temp/bakeoff/emb-qwen.db", "Qwen/Qwen3-Embedding-0.6B", ""),
        ("qwen-asym", "temp/bakeoff/emb-qwen.db", "Qwen/Qwen3-Embedding-0.6B", QWEN_Q),
    ]:
        # A sidecar that exists but is short is worse than one that is absent:
        # every unembedded document silently scores as a miss, which reads as a
        # bad model rather than an unfinished run. Require completeness.
        if not os.path.exists(db):
            print(f"  skip {lane}: {db} missing")
            continue
        n_lane = sqlite3.connect(f"file:{db}?mode=ro", uri=True).execute("SELECT COUNT(*) FROM map").fetchone()[0]
        n_corpus = corpus.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        if n_lane < n_corpus:
            print(f"  skip {lane}: only {n_lane}/{n_corpus} docs embedded (incomplete)")
            continue
        m = SentenceTransformer(model_name, device=os.environ.get("BAKEOFF_DEVICE") or None)
        qv = m.encode([prefix + q["query"] for q in queries], normalize_embeddings=True, show_progress_bar=False)
        lanes[lane], latency[lane] = vec_ranks(db, [v.tolist() for v in qv], queries)
        print(f"  scored {lane}")
        del m

    gdb = "temp/bakeoff/emb-gemini.db"
    if os.path.exists(gdb):
        conn = sqlite3.connect(f"file:{gdb}?mode=ro", uri=True)
        n_g = conn.execute("SELECT COUNT(*) FROM map").fetchone()[0]
        n_c = corpus.execute("SELECT COUNT(*) FROM docs").fetchone()[0]
        if n_g < n_c:
            print(f"  skip gemini: only {n_g}/{n_c} docs embedded (incomplete)")
        else:
            import urllib.request

            from rebalance.ingest.config import get_gemini_api_key

            key = get_gemini_api_key()
            payload = {
                "requests": [
                    {
                        "model": "models/gemini-embedding-001",
                        "content": {"parts": [{"text": q["query"]}]},
                        "taskType": "RETRIEVAL_QUERY",
                    }
                    for q in queries
                ]
            }
            req = urllib.request.Request(
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"gemini-embedding-001:batchEmbedContents?key={key}",
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
            )
            embs = json.loads(urllib.request.urlopen(req, timeout=180).read())["embeddings"]

            def l2(v):
                n = sum(x * x for x in v) ** 0.5
                return [x / n for x in v] if n else v

            lanes["gemini"], latency["gemini"] = vec_ranks(gdb, [l2(e["values"]) for e in embs], queries)
            print("  scored gemini")
    else:
        print("  skip gemini: sidecar missing")

    lanes["fts"] = fts_ranks(queries)
    print("  scored fts")

    # ---- report ----
    results = {"queries": queries, "ranks": lanes, "query_latency_p50": latency, "report": {}}
    idx = {s: [i for i, q in enumerate(queries) if q["set"] == s] for s in ("A", "B")}
    idx["ALL"] = list(range(len(queries)))
    idx["hard"] = [i for i, q in enumerate(queries) if q["lexical"] == "hard"]
    idx["easy"] = [i for i, q in enumerate(queries) if q["lexical"] == "easy"]

    for slice_name, ii in idx.items():
        results["report"][slice_name] = {ln: metrics([lanes[ln][i] for i in ii]) for ln in lanes}

    raw = {}
    for a, b in combinations(sorted(lanes), 2):
        ra, rb = rr(lanes[a]), rr(lanes[b])
        d = [x - y for x, y in zip(ra, rb)]
        p, n = wilcoxon(d)
        raw[(a, b)] = p
        # The MEDIAN paired difference is reported but is near-useless here: most
        # queries tie (both lanes put the target at rank 1), so the median sits
        # at 0.000 even for a large real effect. The mean, the MRR gap, and the
        # win/loss split are what actually carry the effect size on tied data.
        results.setdefault("pairwise", {})[f"{a} vs {b}"] = {
            "median_paired_rr_diff": round(median(d), 4),
            "mean_paired_rr_diff": round(sum(d) / len(d), 4),
            "mean_ci95": boot_ci_mean(d),
            "mrr_gap": round(sum(ra) / len(ra) - sum(rb) / len(rb), 4),
            "n_a_better": sum(1 for x in d if x > 0),
            "n_b_better": sum(1 for x in d if x < 0),
            "n_tied": sum(1 for x in d if x == 0),
            "p_raw": round(p, 5),
            "n_nonzero": n,
        }
    for k, v in holm(list(raw.items())).items():
        results["pairwise"][f"{k[0]} vs {k[1]}"]["p_holm"] = round(v, 5)

    json.dump(results, open("temp/bakeoff/results.json", "w"), indent=1)

    print("\n" + "=" * 92)
    for slice_name in ("ALL", "A", "B", "hard", "easy"):
        r = results["report"][slice_name]
        n = r[next(iter(r))]["n"]
        print(f"\n### {slice_name}  (n={n})")
        print(f"{'lane':<11} {'MRR@10':>8} {'R@1':>7} {'R@5':>7} {'R@10':>7}")
        for ln in sorted(r, key=lambda x: -r[x]["mrr@10"]):
            m = r[ln]
            print(f"{ln:<11} {m['mrr@10']:>8.4f} {m['recall@1']:>7.3f} {m['recall@5']:>7.3f} {m['recall@10']:>7.3f}")

    print("\n### pairwise (paired Wilcoxon on reciprocal rank, full query set; 'a vs b' -> positive favours a)")
    print(f"{'comparison':<26} {'MRR gap':>8} {'mean d':>8} {'mean ci95':>18} {'W/L/T':>10} {'p_raw':>8} {'p_holm':>8}")
    for k, v in sorted(results["pairwise"].items(), key=lambda kv: kv[1]["p_holm"]):
        sig = " *" if v["p_holm"] < 0.05 else ""
        wlt = f"{v['n_a_better']}/{v['n_b_better']}/{v['n_tied']}"
        print(
            f"{k:<26} {v['mrr_gap']:>8.4f} {v['mean_paired_rr_diff']:>8.4f} {str(v['mean_ci95']):>18} "
            f"{wlt:>10} {v['p_raw']:>8.4f} {v['p_holm']:>8.4f}{sig}"
        )
    print("\nwrote temp/bakeoff/results.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
