from fastapi import FastAPI, Request
import re
from pathlib import Path
from docx import Document

app = FastAPI()

DOCS_DIR = Path("documents")
DOCUMENT_TEXTS = []


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
                    texts.append({
                        "source": path.name,
                        "text": text
                    })
            except Exception:
                pass

    DOCUMENT_TEXTS = texts


load_documents()


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "documents_loaded": len(DOCUMENT_TEXTS)
    }


def score_text(query: str, text: str) -> int:
    query_words = set(re.findall(r"[a-zA-Zа-яА-ЯёЁ]+", query.lower()))
    text_lower = text.lower()

    score = 0
    for word in query_words:
        if len(word) >= 4 and word in text_lower:
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

    query_words = [
        w for w in re.findall(r"[a-zA-Zа-яА-ЯёЁ]+", query.lower())
        if len(w) >= 4
    ]

    start = 0
    text_lower = text.lower()

    for word in query_words:
        pos = text_lower.find(word)
        if pos != -1:
            start = max(0, pos - 120)
            break

    fragment = text[start:start + 450]

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