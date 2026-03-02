import json
import re
import glob
from pathlib import Path
from typing import List, Dict, Tuple

from docx import Document as DocxDocument
import chromadb

DOCS_DIR = Path("documents")
DB_DIR = Path("chroma_db")  # будем пересоздавать
COLLECTION_NAME = "hse_admission_docs"

GOLD_PATH = Path("gold_dataset.json")
TOP_K_LIST = [1, 3, 5]

CONFIGS: List[Tuple[int, int]] = [
    (600, 100),
    (900, 150),
    (1200, 200),
    (1500, 250),
]


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


def build_chroma_index(chunk_size: int, overlap: int) -> int:
    files = sorted([Path(p) for p in glob.glob(str(DOCS_DIR / "*.docx"))])
    if not files:
        raise SystemExit("No .docx files found in documents/")

    client = chromadb.PersistentClient(path=str(DB_DIR))

    # пересоздаём коллекцию под конкретную конфигурацию
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    col = client.create_collection(name=COLLECTION_NAME)

    ids, docs, metas = [], [], []
    for f in files:
        raw = read_docx(f)
        chs = chunk_text(raw, chunk_size, overlap)
        for idx, ch in enumerate(chs):
            cid = f"{f.name}::chunk_{idx}"
            ids.append(cid)
            docs.append(ch)
            metas.append({"source": f.name, "chunk_index": idx})

    col.add(ids=ids, documents=docs, metadatas=metas)
    return len(ids)


def reciprocal_rank(rank: int) -> float:
    return 1.0 / rank if rank > 0 else 0.0


def evaluate_retrieval() -> Dict[str, float]:
    gold = json.loads(GOLD_PATH.read_text(encoding="utf-8"))
    n = len(gold)
    if n == 0:
        raise SystemExit("gold_dataset.json is empty.")

    client = chromadb.PersistentClient(path=str(DB_DIR))
    col = client.get_collection(COLLECTION_NAME)

    hit_counts = {k: 0 for k in TOP_K_LIST}
    rr_sum = {k: 0.0 for k in TOP_K_LIST}
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
                rr_sum[k] += reciprocal_rank(rank)

    out = {}
    for k in TOP_K_LIST:
        out[f"Hit@{k}"] = hit_counts[k] / n
        out[f"MRR@{k}"] = rr_sum[k] / n
    return out


def main():
    print("Running chunking experiments...\n")
    print("Config\tChunks\tHit@1\tHit@3\tHit@5\tMRR@1\tMRR@3\tMRR@5")

    for (cs, ov) in CONFIGS:
        total_chunks = build_chroma_index(cs, ov)
        metrics = evaluate_retrieval()
        print(
            f"{cs}/{ov}\t{total_chunks}\t"
            f"{metrics['Hit@1']:.4f}\t{metrics['Hit@3']:.4f}\t{metrics['Hit@5']:.4f}\t"
            f"{metrics['MRR@1']:.4f}\t{metrics['MRR@3']:.4f}\t{metrics['MRR@5']:.4f}"
        )

    print("\n[DONE] Experiments finished.")


if __name__ == "__main__":
    main()