# HSE International Students Voice Assistant

## Project Description

This project is a lightweight Retrieval-Augmented Generation (RAG) voice assistant designed for international students of HSE University. The assistant is integrated with Yandex Alice and provides answers using official HSE university documents.

The goal of the project is to simplify access to important university information for international students and reduce the load on administrative support services.

The assistant currently supports questions related to:
- migration registration;
- dormitories and accommodation;
- university regulations;
- admission-related procedures;
- international student support.

The system returns short English responses generated from official HSE documents.

---

# Main Features

- Integration with Yandex Alice
- FastAPI webhook backend
- Retrieval from official HSE documents
- English-language responses
- Intent-based query routing
- Fallback handling for unrelated questions
- Deployment on Render
- GitHub-based version control

---

# System Architecture

```text
User
   ↓
Yandex Alice
   ↓
FastAPI Webhook
   ↓
Intent Detection
   ↓
Document Retrieval
   ↓
Response Generation
   ↓
Alice Response
```

---

# Technologies Used

- Python
- FastAPI
- Render
- GitHub
- requests
- python-docx
- ChromaDB (experimental stage)
- Yandex Alice Dialogs

---

# Knowledge Base

The knowledge base consists of official HSE university documents in DOCX format.

The documents include information related to:
- international admissions;
- migration procedures;
- dormitory regulations;
- university policies;
- support procedures for international students.

---

# Deployment

The backend is deployed on Render as a cloud web service.

Yandex Alice communicates with the deployed FastAPI webhook through HTTPS requests.

---

# Example Queries

## Migration

```text
What documents are required for migration registration?
```

## Dormitories
```text
Can international students live in HSE dormitories?
```

## Support
```text
How can international students contact HSE support?
```

## Regulations
```text
Where can I find official university regulations?
```
