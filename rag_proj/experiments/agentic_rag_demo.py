ADMISSION_KEYWORDS = [
    "admission", "documents", "deadline", "visa", "migration", "dormitory",
    "student card", "insurance", "schedule", "lms", "exam", "retake",
    "поступление", "документы", "дедлайн", "виза", "миграция", "общежитие",
    "студенческий", "страховка", "расписание", "экзамен", "пересдача"
]


def choose_action(query: str) -> str:
    q = query.lower()
    if len(q.split()) < 3:
        return "ask_clarification"
    if not any(k in q for k in ADMISSION_KEYWORDS):
        return "refuse_offtopic"
    if "contact" in q or "email" in q or "phone" in q or "контакт" in q:
        return "provide_contact"
    return "retrieve_answer"


def main():
    print("AgenticRAG demo. Type 'exit' to stop.")
    while True:
        q = input("\nUser: ").strip()
        if q.lower() == "exit":
            break
        action = choose_action(q)
        print(f"Selected action: {action}")


if __name__ == "__main__":
    main()
