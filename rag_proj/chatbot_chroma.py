import chromadb
from config import COLLECTION_NAME

TOP_K = 5


def main():
    client = chromadb.PersistentClient(path="chroma_db")
    col = client.get_collection(COLLECTION_NAME)

    print("Chroma chat (retrieval only). Type 'exit' to stop.")
    while True:
        q = input("\nYou: ").strip()
        if q.lower() == "exit":
            break

        res = col.query(query_texts=[q], n_results=TOP_K)
        for i, (doc_id, meta, dist) in enumerate(zip(res["ids"][0], res["metadatas"][0], res["distances"][0]), start=1):
            print(f"{i}) dist={dist:.4f} | {meta['source']} | {doc_id}")


if __name__ == "__main__":
    main()
