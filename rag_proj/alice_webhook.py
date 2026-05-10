from fastapi import FastAPI, Request
import re
from pathlib import Path
from docx import Document

app = FastAPI()

DOCS_DIR = Path("documents")
DOCUMENT_TEXTS = []

INTENT_RULES = {
    "migration": {
        "triggers": ["migration", "registration", "visa", "arrival", "passport"],
        "positive": [
            "миграционный", "миграция", "миграционный учет", "миграционный учёт",
            "постановка на учет", "постановка на учёт", "регистрация",
            "иностранный гражданин", "паспорт", "виза", "прибытие"
        ],
        "negative": [
            "поступающих", "поступление", "абитуриент", "зачисление",
            "портфолио", "магистратура", "бакалавриат", "квота"
        ],
    },
    "dormitory": {
        "triggers": ["dormitory", "housing", "accommodation", "live"],
        "positive": ["общежитие", "общежития", "проживание", "заселение", "место в общежитии"],
        "negative": ["поступающих", "портфолио", "зачисление"],
    },
    "contacts": {
        "triggers": ["contact", "email", "support", "help"],
        "positive": ["контакт", "почта", "email", "поддержка", "помощь", "адрес"],
        "negative": [],
    },
}

QUERY_EXPANSIONS = {
    "migration": ["миграционный", "миграция", "иностранный", "иностранные"],
    "registration": ["регистрация", "учет", "учёт", "миграционный учет", "миграционный учёт"],
    "documents": ["документы", "документ", "копии", "скан"],
    "dormitory": ["общежитие", "общежития", "проживание"],
    "housing": ["общежитие", "проживание", "заселение"],
    "visa": ["виза", "визовый", "приглашение"],
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


def detect_intent(query: str) -> str | None:
    query_lower = query.lower()

    for intent, rule in INTENT_RULES.items():
        for trigger in rule["triggers"]:
            if trigger in query_lower:
                return intent

    return None


def expand_query(query: str) -> list[str]:
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]+", query.lower())
    expanded = []

    for word in words:
        if len(word) >= 4:
            expanded.append(word)
        if word in QUERY_EXPANSIONS:
            expanded.extend(QUERY_EXPANSIONS[word])

    return list(set(expanded))


def score_text(query: str, text: str, source: str) -> int:
    keywords = expand_query(query)
    text_lower = text.lower()
    source_lower = source.lower()

    score = 0

    for word in keywords:
        word_lower = word.lower()
        if word_lower in text_lower:
            score += 1
        if word_lower in source_lower:
            score += 3

    intent = detect_intent(query)

    if intent:
        rule = INTENT_RULES[intent]

        for word in rule["positive"]:
            if word.lower() in text_lower:
                score += 5
            if word.lower() in source_lower:
                score += 8

        for word in rule["negative"]:
            if word.lower() in text_lower:
                score -= 4
            if word.lower() in source_lower:
                score -= 10

    return score


def choose_fragment(query: str, text: str) -> str:
    text_lower = text.lower()
    keywords = expand_query(query)

    intent = detect_intent(query)
    if intent:
        keywords = INTENT_RULES[intent]["positive"] + keywords

    start = 0

    for word in keywords:
        pos = text_lower.find(word.lower())
        if pos != -1:
            start = max(0, pos - 120)
            break

    fragment = text[start:start + 500]
    return fragment


def retrieve_answer(query: str) -> str:
    if not DOCUMENT_TEXTS:
        return "The document base is not loaded yet."

    best_doc = None
    best_score = -10**9

    for doc in DOCUMENT_TEXTS:
        score = score_text(query, doc["text"], doc["source"])
        if score > best_score:
            best_score = score
            best_doc = doc

    if best_doc is None or best_score <= 0:
        return "I could not find relevant information in the HSE documents."

    fragment = choose_fragment(query, best_doc["text"])

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