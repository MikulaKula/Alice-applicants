from fastapi import FastAPI, Request
import re
from pathlib import Path
from docx import Document

app = FastAPI()

DOCS_DIR = Path("documents")
DOCUMENT_TEXTS = []


INTENT_RULES = {
    "migration": {
    "triggers": [
        "migration",
        "registration",
        "visa",
        "passport",
        "arrival",
        "migration registration"
    ],

    "positive": [
        "миграционный",
        "миграция",
        "миграционный учет",
        "миграционный учёт",
        "регистрация",
        "постановка на учет",
        "постановка на учёт",
        "иностранный гражданин",
        "иностранный студент",
        "паспорт",
        "виза",
        "прибытие",
        "документ",
        "документы",
        "уведомление"
    ],

    "negative": [
        "скидка",
        "скидок",
        "аттестация",
        "портфолио",
        "собеседование"
    ],
},
    "dormitory": {
        "triggers": ["dormitory", "housing", "accommodation", "live"],
        "positive": [
            "общежитие", "общежития", "проживание", "заселение",
            "место в общежитии", "кампус"
        ],
        "negative": [
            "портфолио", "собеседование", "скидка", "аттестация"
        ],
    },
    "contacts": {
        "triggers": ["contact", "email", "support", "help", "office"],
        "positive": [
            "контакт", "почта", "email", "e-mail", "поддержка",
            "помощь", "адрес", "телефон", "обратной связи"
        ],
        "negative": [
            "портфолио", "скидка", "аттестация"
        ],
    },
    "regulations": {
        "triggers": ["regulation", "regulations", "rules", "policy"],
        "positive": [
            "положение", "регламент", "правила", "приказ",
            "утверждено", "порядок"
        ],
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


def detect_intent(query: str) -> str | None:
    query_lower = query.lower()

    for intent, rule in INTENT_RULES.items():
        for trigger in rule["triggers"]:
            if trigger in query_lower:
                return intent

    return None


def score_text(query: str, text: str, source: str) -> int:
    intent = detect_intent(query)

    text_lower = text.lower()
    source_lower = source.lower()

    score = 0

    query_words = re.findall(r"[a-zA-Zа-яА-ЯёЁ]+", query.lower())
    for word in query_words:
        if len(word) >= 4:
            if word in text_lower:
                score += 1
            if word in source_lower:
                score += 2

    if intent:
        rule = INTENT_RULES[intent]

        for word in rule["positive"]:
            if word.lower() in text_lower:
                score += 8
            if word.lower() in source_lower:
                score += 12

        for word in rule["negative"]:
            if word.lower() in text_lower:
                score -= 6
            if word.lower() in source_lower:
                score -= 12

    return score


def find_best_document(query: str):
    if not DOCUMENT_TEXTS:
        return None, 0

    best_doc = None
    best_score = -10**9

    for doc in DOCUMENT_TEXTS:
        score = score_text(query, doc["text"], doc["source"])
        if score > best_score:
            best_score = score
            best_doc = doc

    return best_doc, best_score


def make_english_answer(query: str) -> str:
    intent = detect_intent(query)
    best_doc, score = find_best_document(query)

    if best_doc is None or score <= 0:
        return (
    "I could not find this information in the official HSE documents. "
    "Please try rephrasing the question or ask about admissions, migration, dormitories, "
    "university regulations, or international student support."
)

    source = best_doc["source"]

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

    return (
        "I found relevant information in the HSE documents, but the current lightweight version of the assistant "
        "can only provide a short summary. Please check the official source for exact details. "
        f"Relevant source: {source}."
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