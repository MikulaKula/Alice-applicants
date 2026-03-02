# 🎓 Чат-бот для иностранных абитуриентов (RAG)

## Структура проекта

```
chatbot_project/
├── config.py              # Настройки (пути, модели, параметры)
├── load_documents.py      # Загрузка .docx → чанки → ChromaDB
├── chatbot.py             # RAG-пайплайн (retrieval + LLM)
├── evaluate.py            # Оценка по золотому датасету
├── requirements.txt       # Зависимости
├── gold_dataset.json      # 50 золотых вопросов
├── documents/             # ← Сюда кладёшь .docx файлы
│   ├── 1Правила приема бакалавриат, специалитет 2026.docx
│   ├── 1Регламент отбора иностранных граждан...docx
│   ├── Положение бакалавриат с изменениями.docx
│   └── ...
└── chroma_db/             # Создаётся автоматически
```

## Как запустить

### 1. Установи зависимости
```bash
pip install -r requirements.txt
```

### 2. Положи документы в папку `documents/`

### 3. Индексация документов
```bash
python load_documents.py
```

### 4. Запуск чат-бота
```bash
python chatbot.py
```

### 5. Оценка по золотому датасету
```bash
python evaluate.py
```

## Порядок запуска
```
load_documents.py  →  chatbot.py (интерактив) / evaluate.py (оценка)
```

## Без OpenAI API
Система работает и без API-ключа — просто показывает найденные фрагменты
документов без генерации ответа через LLM. Для полного RAG задай ключ:
```bash
export OPENAI_API_KEY="sk-..."
```


## Формат `gold_dataset.json` (document-level)
Каждая запись содержит:
- `question` — тестовый вопрос
- `gold_doc_id` — имя файла `.docx` (точное), которое считается правильным источником
- `gold_answer` — краткая подсказка/эталон (опционально, для отчёта)

Важно: `gold_doc_id` должен **в точности** совпадать с `filename` в папке `documents/`,
потому что `load_documents.py` пишет `metadata["source"] = filename`.
