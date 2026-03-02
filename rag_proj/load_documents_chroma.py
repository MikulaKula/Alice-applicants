import glob
import re
from pathlib import Path
from typing import List, Dict

from docx import Document as DocxDocument
import chromadb


DOCS_DIR = Path("documents")
DB_DIR = Path("chroma_db")
COLLECTION_NAME = "hse_admission_docs"

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


def read_docx(path: Path) -> str:
    doc = DocxDocument(str(path))
    paras = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paras)


def chunk_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    i = 0
    n = len(text)
    while i < n:
        j = min(i + chunk_size, n)
        chunk = text[i:j].strip()
        if chunk:
            chunks.append(chunk)
        i += step
    return chunks


def main():
    if not DOCS_DIR.exists():
        raise SystemExit("Folder 'documents/' not found.")

    files = sorted([Path(p) for p in glob.glob(str(DOCS_DIR / "*.docx"))])
    if not files:
        raise SystemExit("No .docx files found in documents/")

    client = chromadb.PersistentClient(path=str(DB_DIR))
    # пересоздаём коллекцию (чтобы не копить мусор)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    col = client.create_collection(name=COLLECTION_NAME)

    ids = []
    docs = []
    metas: List[Dict] = []

    for f in files:
        raw = read_docx(f)
        chs = chunk_text(raw, CHUNK_SIZE, CHUNK_OVERLAP)
        print(f"[OK] {f.name}: {len(chs)} chunks")

        for idx, ch in enumerate(chs):
            cid = f"{f.name}::chunk_{idx}"
            ids.append(cid)
            docs.append(ch)
            metas.append({"source": f.name, "chunk_index": idx})

    col.add(ids=ids, documents=docs, metadatas=metas)

    print("\n[DONE] Chroma index built successfully.")
    print(f"[INFO] Collection: {COLLECTION_NAME}")
    print(f"[INFO] Total chunks: {len(ids)}")
    print(f"[INFO] DB path: {DB_DIR.resolve()}")


if __name__ == "__main__":
    main()