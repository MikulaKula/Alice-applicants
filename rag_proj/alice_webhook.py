from fastapi import FastAPI, Request
import chromadb
import traceback

app = FastAPI()

client = chromadb.PersistentClient(path="chroma_db")

collection = client.get_collection("hse_admission_docs")


@app.get("/")
def health():
    return {"status": "ok"}


def search_docs(query: str) -> str:
    result = collection.query(
        query_texts=[query],
        n_results=1
    )

    docs = result["documents"][0]

    if not docs:
        return "I could not find relevant information."

    text = docs[0]

    text = text.replace("\n", " ")

    if len(text) > 350:
        text = text[:350] + "..."

    return text


@app.post("/alice")
async def alice(request: Request):
    try:
        data = await request.json()

        user_text = data["request"]["original_utterance"]

        if not user_text:
            answer = "Hello. I can help international students with HSE-related questions."
        else:
            answer = search_docs(user_text)

        return {
            "version": "1.0",
            "session": data["session"],
            "response": {
                "text": answer,
                "end_session": False
            }
        }

    except Exception as e:
        print(traceback.format_exc())

        return {
            "version": "1.0",
            "response": {
                "text": str(e),
                "end_session": False
            }
        }