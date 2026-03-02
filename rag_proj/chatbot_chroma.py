from pathlib import Path
import chromadb

DB_DIR = Path("chroma_db")
COLLECTION_NAME = "hse_admission_docs"
TOP_K = 5


def main():
    client = chromadb.PersistentClient(path=str(DB_DIR))
    col = client.get_collection(COLLECTION_NAME)

    print("Chroma chat (retrieval only). Type 'exit' to stop.\n")
    while True:
        q = input("You: ").strip()
        if not q or q.lower() == "exit":
            break

        res = col.query(query_texts=[q], n_results=TOP_K)

        print("\nTop matches:")
        for i in range(TOP_K):
            cid = res["ids"][0][i]
            meta = res["metadatas"][0][i]
            dist = res["distances"][0][i]
            print(f"{i+1}) dist={dist:.4f} | {meta['source']} | {cid}")
        print("")


if __name__ == "__main__":
    main()