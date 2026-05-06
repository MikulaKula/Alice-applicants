import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import chromadb
from config import DOCS_DIR, GOLD_PATH, COLLECTION_NAME, RESULTS_DIR, TOP_K_LIST
from utils import load_documents, load_gold, evaluate_ranked_sources, save_csv

CONFIGS = [
    ("fixed", 600, 100),
    ("fixed", 900, 150),
    ("fixed", 1200, 200),
    ("fixed", 1500, 250),
    ("paragraph", 900, 0),
]


def run_one(method, chunk_size, overlap):
    docs = load_documents(DOCS_DIR, preprocessing="basic", chunk_method=method, chunk_size=chunk_size, overlap=overlap)
    gold = load_gold(GOLD_PATH)

    db_path = f"chroma_db_exp_chunk_{method}_{chunk_size}_{overlap}"
    client = chromadb.PersistentClient(path=db_path)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    col = client.create_collection(name=COLLECTION_NAME)
    col.add(ids=[d["id"] for d in docs], documents=[d["text"] for d in docs], metadatas=[d["metadata"] for d in docs])

    max_k = max(TOP_K_LIST)
    ranked_sources = []
    for item in gold:
        res = col.query(query_texts=[item["question"]], n_results=max_k)
        ranked_sources.append([m["source"] for m in res["metadatas"][0]])

    metrics = evaluate_ranked_sources(gold, ranked_sources, TOP_K_LIST)
    return {"method": method, "chunk_size": chunk_size, "overlap": overlap, "chunks": len(docs), **metrics}


def main():
    rows = []
    print("method\tchunk/overlap\tchunks\tHit@1\tHit@3\tHit@5\tMRR@5")
    for method, cs, ov in CONFIGS:
        row = run_one(method, cs, ov)
        rows.append(row)
        print(f"{method}\t{cs}/{ov}\t{row['chunks']}\t{row['Hit@1']:.4f}\t{row['Hit@3']:.4f}\t{row['Hit@5']:.4f}\t{row['MRR@5']:.4f}")

    save_csv(RESULTS_DIR / "chunking_results.csv", rows)
    print("[DONE] Saved results/chunking_results.csv")


if __name__ == "__main__":
    main()
