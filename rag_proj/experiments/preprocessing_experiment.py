import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import chromadb
from config import DOCS_DIR, GOLD_PATH, COLLECTION_NAME, RESULTS_DIR, TOP_K_LIST
from utils import load_documents, load_gold, evaluate_ranked_sources, save_csv

CONFIGS = ["raw", "basic", "strict"]


def run_one(preprocessing):
    docs = load_documents(DOCS_DIR, preprocessing=preprocessing, chunk_method="fixed", chunk_size=900, overlap=150)
    gold = load_gold(GOLD_PATH)

    db_path = f"chroma_db_exp_preproc_{preprocessing}"
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
    return {"preprocessing": preprocessing, "chunks": len(docs), **metrics}


def main():
    rows = []
    print("preprocessing\tchunks\tHit@1\tHit@3\tHit@5\tMRR@5")
    for prep in CONFIGS:
        row = run_one(prep)
        rows.append(row)
        print(f"{prep}\t{row['chunks']}\t{row['Hit@1']:.4f}\t{row['Hit@3']:.4f}\t{row['Hit@5']:.4f}\t{row['MRR@5']:.4f}")

    save_csv(RESULTS_DIR / "preprocessing_results.csv", rows)
    print("[DONE] Saved results/preprocessing_results.csv")


if __name__ == "__main__":
    main()
