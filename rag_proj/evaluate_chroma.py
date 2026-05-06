import chromadb
from config import GOLD_PATH, COLLECTION_NAME, TOP_K_LIST
from utils import load_gold, evaluate_ranked_sources


def main():
    gold = load_gold(GOLD_PATH)
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection(COLLECTION_NAME)

    max_k = max(TOP_K_LIST)
    ranked_sources = []

    for item in gold:
        res = col.query(query_texts=[item["question"]], n_results=max_k)
        ranked_sources.append([m["source"] for m in res["metadatas"][0]])

    metrics = evaluate_ranked_sources(gold, ranked_sources, TOP_K_LIST)

    print(f"Questions: {len(gold)}")
    for k in TOP_K_LIST:
        print(f"Hit@{k}: {metrics[f'Hit@{k}']:.4f} | MRR@{k}: {metrics[f'MRR@{k}']:.4f}")


if __name__ == "__main__":
    main()
