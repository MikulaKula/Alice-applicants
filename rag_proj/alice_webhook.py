from fastapi import FastAPI, Request
import re
from pathlib import Path
from docx import Document

app = FastAPI()

DOCS_DIR = Path("documents")
CHUNKS = []

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150


INTENT_RULES = {
    "migration": {
        "triggers": ["migration", "registration", "visa", "passport", "arrival"],
        "positive": [
            "миграционный", "миграция", "миграционный учет", "миграционный учёт",
            "регистрация", "постановка на учет", "постановка на учёт",
            "иностранный гражданин", "иностранный студент", "паспорт", "виза",
            "прибытие", "документ", "документы", "уведомление"
        ],
        "negative": ["скидка", "скидок", "аттестация", "портфолио", "собеседование"],
    },
    "dormitory": {
        "triggers": ["dormitory", "housing", "accommodation", "live"],
        "positive": ["общежитие", "общежития", "проживание", "заселение", "место в общежитии"],
        "negative": ["портфолио", "собеседование", "скидка", "аттестация"],
    },
    "contacts": {
        "triggers": ["contact", "email", "support", "help", "office"],
        "positive": ["контакт", "почта", "email", "e-mail", "поддержка", "помощь", "адрес", "телефон"],
        "negative": ["портфолио", "скидка", "аттестация"],
    },
    "regulations": {
        "triggers": ["regulation", "regulations", "rules", "policy"],
        "positive": ["положение", "регламент", "правила", "приказ", "утверждено", "порядок"],
        "negative": [],
    },
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


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def load_chunks() -> None:
    global CHUNKS

    chunks = []

    if DOCS_DIR.exists():
        for path in DOCS_DIR.rglob("*.docx"):
            try:
                full_text = load_docx_text(path)
                for i, chunk in enumerate(split_into_chunks(full_text)):
                    chunks.append({
                        "source": path.name,
                        "chunk_id": i,
                        "text": chunk
                    })
            except Exception:
                pass

    CHUNKS = chunks


load_chunks()


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "chunks_loaded": len(CHUNKS)
    }


def detect_intent(query: str) -> str | None:
    query_lower = query.lower()

    for intent, rule in INTENT_RULES.items():
        for trigger in rule["triggers"]:
            if trigger in query_lower:
                return intent

    return None


def score_chunk(query: str, chunk: dict) -> int:
    intent = detect_intent(query)

    text_lower = chunk["text"].lower()
    source_lower = chunk["source"].lower()

    score = 0

    query_words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]+", query.lower())

    for word in query_words:
        if len(word) >= 4:
            if word in text_lower:
                score += 2
            if word in source_lower:
                score += 3

    if intent:
        rule = INTENT_RULES[intent]

        for word in rule["positive"]:
            word_lower = word.lower()
            if word_lower in text_lower:
                score += 10
            if word_lower in source_lower:
                score += 8

        for word in rule["negative"]:
            word_lower = word.lower()
            if word_lower in text_lower:
                score -= 8
            if word_lower in source_lower:
                score -= 10

    return score


def find_best_chunk(query: str):
    if not CHUNKS:
        return None, 0

    best_chunk = None
    best_score = -10**9

    for chunk in CHUNKS:
        score = score_chunk(query, chunk)
        if score > best_score:
            best_score = score
            best_chunk = chunk

    return best_chunk, best_score


def make_english_answer(query: str) -> str:
    intent = detect_intent(query)
    best_chunk, score = find_best_chunk(query)

    if best_chunk is None or score <= 0:
        return (
            "I could not find this information in the official HSE documents. "
            "Please try rephrasing the question or ask about admissions, migration, dormitories, "
            "university regulations, or international student support."
        )

    source = best_chunk["source"]

    if intent == "migration":
        return (
            "According to the available HSE documents, questions about migration registration "
            "should be checked through the official university procedures for international students. "
            "The student may need to provide identity and migration-related documents, such as passport, visa, "
            "arrival or registration documents, depending on the specific case. "
            f"Relevant source: {source}."
        )

    if intent == "dormitory":
        return (
            "According to the available HSE documents, international students may use HSE dormitory-related "
            "services if they meet the relevant university conditions. The exact accommodation procedure, "
            "allocation rules, and settlement details should be checked in the official dormitory or admission documents. "
            f"Relevant source: {source}."
        )

    if intent == "contacts":
        return (
            "According to the available HSE documents, students should use the official HSE contact channels "
            "for support questions. If the issue concerns documents, migration, accommodation, or academic procedures, "
            "it is better to contact the responsible university office directly. "
            f"Relevant source: {source}."
        )

    if intent == "regulations":
        return (
            "According to the available HSE documents, this topic is regulated by official university rules, "
            "orders, or regulations. The exact procedure depends on the specific document and student category. "
            f"Relevant source: {source}."
        )

    fragment = best_chunk["text"][:350]

    return (
        "I found relevant information in the HSE documents. "
        f"Relevant source: {source}. "
        f"Fragment: {fragment}..."
    )


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
        answer = make_english_answer(user_text)

    return {
        "version": data.get("version", "1.0"),
        "session": data.get("session", {}),
        "response": {
            "text": answer[:900],
            "end_session": False
        }
    }