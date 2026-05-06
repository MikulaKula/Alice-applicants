import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import json
import chromadb
from config import GOLD_PATH, COLLECTION_NAME, RESULTS_DIR
from utils import load_gold

OUT_PATH = RESULTS_DIR / "generation_eval_template.json"


def main():
    gold = load_gold(GOLD_PATH)
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection(COLLECTION_NAME)

    rows = []
    for item in gold[:20]:
        q = item["question"]
        res = col.query(query_texts=[q], n_results=3)
        contexts = res["documents"][0]
        sources = [m["source"] for m in res["metadatas"][0]]

        generated_answer = contexts[0][:700] if contexts else ""

        rows.append({
            "question": q,
            "gold_doc_id": item.get("gold_doc_id"),
            "retrieved_sources": sources,
            "generated_answer": generated_answer,
            "manual_scores": {
                "factual_correctness_0_2": None,
                "completeness_0_2": None,
                "groundedness_0_2": None,
                "hallucination_0_1": None
            }
        })

    OUT_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] Manual generation evaluation template saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
