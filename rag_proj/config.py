import os

# ============================================================
# config.py — Настройки проекта
# ============================================================

# Папка с .docx документами для RAG
DOCUMENTS_DIR = "documents/"

# Папка для хранения ChromaDB
CHROMA_DB_DIR = "chroma_db/"

# Путь к золотому датасету
GOLD_DATASET_PATH = "gold_dataset.json"

# Модель для эмбеддингов (бесплатная, работает локально)
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Настройки чанкинга
CHUNK_SIZE = 500        # символов на чанк
CHUNK_OVERLAP = 100     # перекрытие между чанками

# Сколько чанков возвращать при поиске
TOP_K = 3

# OpenAI API (для генерации ответов)
# Если нет ключа — система будет работать только как retriever
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = "gpt-3.5-turbo"
