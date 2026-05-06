import re
import csv
import json
from pathlib import Path
from typing import List, Dict
from docx import Document as DocxDocument


def read_docx(path: Path) -> str:
    doc = DocxDocument(str(path))
    paras = [p.text.strip() for p in doc.paragraphs if p.text and p.text.strip()]
    return "\n".join(paras)


def clean_text_basic(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def clean_text_strict(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\u00ad\u200b]", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text.strip()


def chunk_fixed(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = clean_text_basic(text)
    if not text:
        return []
    chunks = []
    step = max(1, chunk_size - overlap)
    i = 0
    while i < len(text):
        chunk = text[i:i + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        i += step
    return chunks


def chunk_by_paragraphs(text: str, max_chars: int = 900) -> List[str]:
    paragraphs = [p.strip() for p in text.split("\\n") if p.strip()]
    chunks, cur = [], ""
    for p in paragraphs:
        if len(cur) + len(p) + 1 <= max_chars:
            cur = (cur + " " + p).strip()
        else:
            if cur:
                chunks.append(cur)
            cur = p
    if cur:
        chunks.append(cur)
    return chunks


def load_documents(docs_dir: Path, preprocessing: str = "basic", chunk_method: str = "fixed",
                   chunk_size: int = 900, overlap: int = 150):
    docs = []
    for f in sorted(docs_dir.glob("*.docx")):
        text = read_docx(f)
        if preprocessing == "basic":
            text = clean_text_basic(text)
        elif preprocessing == "strict":
            text = clean_text_strict(text)
        elif preprocessing == "raw":
            pass
        else:
            raise ValueError(f"Unknown preprocessing: {preprocessing}")

        if chunk_method == "fixed":
            chunks = chunk_fixed(text, chunk_size, overlap)
        elif chunk_method == "paragraph":
            chunks = chunk_by_paragraphs(text, max_chars=chunk_size)
        else:
            raise ValueError(f"Unknown chunk method: {chunk_method}")

        for idx, ch in enumerate(chunks):
            docs.append({
                "id": f"{f.name}::chunk_{idx}",
                "text": ch,
                "metadata": {"source": f.name, "chunk_index": idx}
            })
    return docs


def load_gold(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def reciprocal_rank(rank: int) -> float:
    return 1.0 / rank if rank > 0 else 0.0


def evaluate_ranked_sources(gold, ranked_sources_by_question, top_k_list=(1, 3, 5)):
    n = len(gold)
    hit_counts = {k: 0 for k in top_k_list}
    rr_sums = {k: 0.0 for k in top_k_list}

    for item, top_sources in zip(gold, ranked_sources_by_question):
        gold_doc = item["gold_doc_id"]
        rank = 0
        for i, src in enumerate(top_sources, start=1):
            if src == gold_doc:
                rank = i
                break
        for k in top_k_list:
            if 0 < rank <= k:
                hit_counts[k] += 1
                rr_sums[k] += reciprocal_rank(rank)

    result = {}
    for k in top_k_list:
        result[f"Hit@{k}"] = hit_counts[k] / n if n else 0.0
        result[f"MRR@{k}"] = rr_sums[k] / n if n else 0.0
    return result


def save_csv(path: Path, rows: List[Dict]):
    if not rows:
        return
    keys = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
