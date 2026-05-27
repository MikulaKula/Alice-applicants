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
            "миграционный", "миграция", "регистрация",
            "паспорт", "виза", "документ", "документы"
        ],
        "negative": ["скидка", "аттестация", "портфолио"],
    },
    "dormitory": {
        "triggers": ["dormitory", "housing", "accommodation", "live"],
        "positive": ["общежитие", "проживание", "заселение"],
        "negative": ["портфолио", "аттестация"],
    },
    "contacts": {
        "triggers": ["contact", "email", "support", "help"],
        "positive": ["контакт", "почта", "email", "поддержка"],
        "negative": [],
    },
    "regulations": {
        "triggers": ["regulation", "rules", "policy"],
        "positive": ["положение", "регламент", "правила"],
        "negative": [],
    },
}


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_docx_text(path: Path) -> str:
    doc = Document(path)
    return clean_text(" ".join([p.text for p in doc.paragraphs if p.text]))


def split_into_chunks(text: str):
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def load_chunks():
    global CHUNKS
    CHUNKS = []

    if DOCS_DIR.exists():
        for path in DOCS_DIR.rglob("*.docx"):
            try:
                text = load_docx_text(path)

                for i, chunk in enumerate(split_into_chunks(text)):
                    CHUNKS.append({
                        "source": path.name,
                        "text": chunk
                    })

            except Exception as e:
                print(f"Error loading {path.name}: {e}")

    print(f"Loaded {len(CHUNKS)} chunks")


load_chunks()


@app.get("/")
def health():
    return {"status": "ok", "chunks_loaded": len(CHUNKS)}


def detect_intent(query: str):
    q = query.lower()

    for intent, rule in INTENT_RULES.items():
        for trigger in rule["triggers"]:
            if trigger in q:
                return intent

    return None


def score_chunk(query: str, chunk):
    text = chunk["text"].lower()
    score = 0

    words = re.findall(r"[a-zA-Zа-яА-Я]+", query.lower())

    for w in words:
        if len(w) >= 4 and w in text:
            score += 2

    intent = detect_intent(query)

    if intent:
        for w in INTENT_RULES[intent]["positive"]:
            if w in text:
                score += 8

        for w in INTENT_RULES[intent]["negative"]:
            if w in text:
                score -= 5

    return score


def find_best_chunk(query: str):
    best = None
    best_score = -999

    for chunk in CHUNKS:
        s = score_chunk(query, chunk)

        if s > best_score:
            best_score = s
            best = chunk

    return best, best_score


def make_answer(query: str):
    intent = detect_intent(query)
    chunk, score = find_best_chunk(query)

    if chunk is None or score <= 0:
        return (
            "I could not find this information in the official HSE documents. "
            "Please ask about migration, dormitories, regulations, or contacts."
        )

    source = chunk["source"]

    if intent == "migration":
        return f"You may need passport, visa and migration documents. Source: {source}."

    if intent == "dormitory":
        return (
            f"According to the available HSE documents, international applicants may be eligible "
            f"for HSE dormitory accommodation under the relevant university rules. "
            f"The exact conditions should be checked in the official admission or dormitory documents. "
            f"Source: {source}."
        )

    if intent == "contacts":
        return f"Please use official HSE contact channels. Source: {source}."

    if intent == "regulations":
        return f"This is defined by official HSE regulations. Source: {source}."

    return f"Relevant information found. Source: {source}."


@app.post("/alice")
async def webhook(request: Request):
    try:
        data = await request.json()

        user_text = (
            data.get("request", {}).get("original_utterance", "")
            or data.get("request", {}).get("command", "")
            or ""
        )

        q = user_text.lower().strip()
        q = q.replace("?", "").replace("!", "").replace(".", "")

        # HELP
        if q in ["help", "помощь", "что ты умеешь", "what can you do"]:
            answer = (
                "I help international applicants find official HSE information. "
                "You can ask about migration registration, dormitories, admission rules, "
                "university regulations, or support contacts. "
                "For example: What documents are required for migration registration?"
            )

        # GREETING
        elif q in ["hello", "hi", "привет", "start", "начать"]:
            answer = (
                "Hello! This is HSE International Assistant. "
                "I help international applicants find official information about HSE University. "
                "You can ask questions about migration registration, dormitories, "
                "university regulations, or support contacts. "
                "For example: "
                "'What documents are required for migration registration?'"
        )

        # EMPTY
        elif not user_text:
            answer = (
                "Hello! This is HSE International Assistant. "
                "I help international applicants with official HSE information. "
                "You can ask about migration registration, dormitories, "
                "support contacts, or university regulations."
            )

        # MAIN
        else:
            answer = make_answer(user_text)

        return {
            "version": data.get("version", "1.0"),
            "session": data.get("session", {}),
            "response": {
                "text": answer[:900],
                "end_session": False
            }
        }

    except Exception as e:
        print("ERROR:", e)

        return {
            "version": "1.0",
            "response": {
                "text": "Server error.",
                "end_session": False
            }
        }