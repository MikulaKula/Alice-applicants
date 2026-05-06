import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import re
from collections import Counter
import chromadb
from config import GOLD_PATH, COLLECTION_NAME, RESULTS_DIR, TOP_K_LIST
from utils import load_gold, evaluate_ranked_sources, save_csv


def tokenize(text: str):
    return re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", text.lower())


def score_overlap(query: str, doc: str) -> float:
    q = Counter(tokenize(query))
    d = Counter(tokenize(doc))
    if not q or not d:
        return 0.0
    overlap = sum(min(q[t], d[t]) for t in q)
    return overlap / max(1, sum(q.values()))


def main():
    gold = load_gold(GOLD_PATH)
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection(COLLECTION_NAME)

    max_k = 10
    plain_ranked, reranked = [], []

    for item in gold:
        q = item["question"]
        res = col.query(query_texts=[q], n_results=max_k)
        docs = res["documents"][0]
        metas = res["metadatas"][0]

        plain_ranked.append([m["source"] for m in metas[:max(TOP_K_LIST)]])

        scored = [(score_overlap(q, doc), meta["source"]) for doc, meta in zip(docs, metas)]
        scored.sort(reverse=True, key=lambda x: x[0])
        reranked.append([src for _, src in scored[:max(TOP_K_LIST)]])

    plain_metrics = evaluate_ranked_sources(gold, plain_ranked, TOP_K_LIST)
    rerank_metrics = evaluate_ranked_sources(gold, reranked, TOP_K_LIST)

    rows = [
        {"method": "retrieval_only", **plain_metrics},
        {"method": "retrieval_plus_lexical_reranker", **rerank_metrics},
    ]
    save_csv(RESULTS_DIR / "reranker_results.csv", rows)

    print("method\\tHit@1\\tHit@3\\tHit@5\\tMRR@5")
    for row in rows:
        print(f"{row['method']}\\t{row['Hit@1']:.4f}\\t{row['Hit@3']:.4f}\\t{row['Hit@5']:.4f}\\t{row['MRR@5']:.4f}")

    print("[DONE] Saved results/reranker_results.csv")


if __name__ == "__main__":
    main()
