from fastapi import FastAPI, Request
import chromadb
import traceback
import re

app = FastAPI()

COLLECTION_NAME = "hse_admission_docs"

client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection(COLLECTION_NAME)


@app.get("/")
def health_check():
    return {"status": "ok"}


def clean_text(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def retrieve_answer(query: str) -> str:
    result = collection.query(query_texts=[query], n_results=1)

    if not result.get("documents") or not result["documents"][0]:
        return "I could not find relevant information in the university documents."

    text = clean_text(result["documents"][0][0])

    if len(text) > 450:
        text = text[:450] + "..."

    return "According to HSE documents: " + text


@app.post("/alice")
async def alice_webhook(request: Request):
    try:
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
                "text": answer,
                "end_session": False
            }
        }

    except Exception as e:
        print(traceback.format_exc())

        return {
            "version": "1.0",
            "session": {},
            "response": {
                "text": f"Backend error: {str(e)}"[:450],
                "end_session": False
            }
        }