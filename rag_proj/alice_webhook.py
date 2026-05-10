from fastapi import FastAPI, Request
import re
from pathlib import Path
from docx import Document

app = FastAPI()

DOCS_DIR = Path("documents")
DOCUMENT_TEXTS = []

QUERY_EXPANSIONS = {
    "migration": ["миграционный", "миграция", "иностранный", "иностранные"],
    "registration": ["регистрация", "учет", "учёт", "миграционный учет", "миграционный учёт"],
    "documents": ["документы", "документ", "копии", "скан"],
    "dormitory": ["общежитие", "общежития", "проживание"],
    "visa": ["виза", "визовый"],
    "contact": ["контакт", "почта", "email", "адрес"],
    "support": ["поддержка", "помощь", "сопровождение"],
    "regulations": ["положение", "регламент", "правила", "приказ"],
    "international": ["иностранный", "иностранные", "международный"],
    "student": ["студент", "студенты", "обучающийся"],
}


def clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_docx_text(path: Path) -> str:
    doc = Document(path)
    parts = []

    for paragraph in doc.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)

    return clean_text(" ".join(parts))


def load_documents() -> None:
    global DOCUMENT_TEXTS

    texts = []

    if DOCS_DIR.exists():
        for path in DOCS_DIR.rglob("*.docx"):
            try:
                text = load_docx_text(path)
                if text:
                    texts.append({"source": path.name, "text": text})
            except Exception:
                pass

    DOCUMENT_TEXTS = texts


load_documents()


@app.get("/")
def health_check():
    return {"status": "ok", "documents_loaded": len(DOCUMENT_TEXTS)}


def expand_query(query: str) -> list[str]:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]+", query.lower())
    expanded = []

    for word in words:
        if len(word) >= 4:
            expanded.append(word)
        if word in QUERY_EXPANSIONS:
            expanded.extend(QUERY_EXPANSIONS[word])

    return list(set(expanded))


def score_text(query: str, text: str) -> int:
    keywords = expand_query(query)
    text_lower = text.lower()

    score = 0
    for word in keywords:
        if word.lower() in text_lower:
            score += 1

    return score


def retrieve_answer(query: str) -> str:
    if not DOCUMENT_TEXTS:
        return "The document base is not loaded yet."

    best_doc = None
    best_score = 0

    for doc in DOCUMENT_TEXTS:
        score = score_text(query, doc["text"])
        if score > best_score:
            best_score = score
            best_doc = doc

    if best_doc is None or best_score == 0:
        return "I could not find relevant information in the HSE documents."

    text = best_doc["text"]
    text_lower = text.lower()

    keywords = expand_query(query)
    start = 0

    for word in keywords:
        pos = text_lower.find(word.lower())
        if pos != -1:
            start = max(0, pos - 120)
            break

    fragment = text[start:start + 500]

    return f"According to HSE documents ({best_doc['source']}): {fragment}..."


@app.post("/alice")
async def alice_webhook(request: Request):
    data = await request.json()

    user_text = (
        data.get("request", {}).get("original_utterance", "")
        or data.get("request", {}).get("command", "")
        or data.get("text", "")
    )

    if not user_text:
        answer = "Hello. I can help international students with HSE-related questions."
    else:
        answer = retrieve_answer(user_text)

    return {
        "version": data.get("version", "1.0"),
        "session": data.get("session", {}),
        "response": {
            "text": answer[:900],
            "end_session": False
        }
    }