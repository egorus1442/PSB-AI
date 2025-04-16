def stub_rag(request_data: dict) -> dict:
    """
    Функция-заглушка для RAG-системы.
    
    Принимает запрос в формате:
    {
        "id": "пример id",
        "question": "Любой вопрос",
        "thread_id": "пример thread_id"
    }
    
    Возвращает ответ в формате:
    {
        "id": "пример id",
        "answer": "Ответ"
    }
    """
    response = {
        "id": request_data.get("id", "no_id"),
        "answer": "Ответ"
    }
    return response