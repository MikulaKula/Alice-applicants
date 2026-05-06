import chromadb
from config import DOCS_DIR, COLLECTION_NAME, DEFAULT_CHUNK_SIZE, DEFAULT_CHUNK_OVERLAP
from utils import load_documents


def main():
    docs = load_documents(DOCS_DIR, preprocessing="basic", chunk_method="fixed",
                          chunk_size=DEFAULT_CHUNK_SIZE, overlap=DEFAULT_CHUNK_OVERLAP)

    client = chromadb.PersistentClient(path="chroma_db")
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    col = client.create_collection(name=COLLECTION_NAME)
    col.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[d["metadata"] for d in docs],
    )

    print("[DONE] Chroma index built successfully.")
    print(f"[INFO] Total chunks: {len(docs)}")
    print("[INFO] DB path: chroma_db")


if __name__ == "__main__":
    main()
