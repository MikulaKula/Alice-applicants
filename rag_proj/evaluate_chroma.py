import json
from pathlib import Path
import chromadb

DB_DIR = Path("chroma_db")
COLLECTION_NAME = "hse_admission_docs"
GOLD_PATH = Path("gold_dataset.json")

TOP_K_LIST = [1, 3, 5]


def reciprocal_rank(rank: int) -> float:
    return 1.0 / rank if rank > 0 else 0.0


def main():
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    n = len(gold)
    if n == 0:
        raise SystemExit("gold_dataset.json is empty.")

    client = chromadb.PersistentClient(path=str(DB_DIR))
    col = client.get_collection(COLLECTION_NAME)

    hit_counts = {k: 0 for k in TOP_K_LIST}
    rr_sum_at_k = {k: 0.0 for k in TOP_K_LIST}
    max_k = max(TOP_K_LIST)

    for item in gold:
        q = item["question"]
        gold_doc = item["gold_doc_id"]

        res = col.query(query_texts=[q], n_results=max_k)
        top_sources = [m["source"] for m in res["metadatas"][0]]

        rank = 0
        for idx, src in enumerate(top_sources, start=1):
            if src == gold_doc:
                rank = idx
                break

        for k in TOP_K_LIST:
            if rank > 0 and rank <= k:
                hit_counts[k] += 1
                rr_sum_at_k[k] += reciprocal_rank(rank)

    print(f"Questions: {n}")
    for k in TOP_K_LIST:
        hit = hit_counts[k] / n
        mrr = rr_sum_at_k[k] / n
        print(f"Hit@{k}: {hit:.4f} | MRR@{k}: {mrr:.4f}")


if __name__ == "__main__":
    main()