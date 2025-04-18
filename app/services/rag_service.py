import json
from pydantic import BaseModel


class RagRequest(BaseModel):
    id: str
    thread_id: str
    question: str


class RagResponse(BaseModel):
    id: str
    answer: str


def stub_rag(request_data: RagRequest) -> RagResponse:
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
    response = RagResponse(
        id = request_data.id,
        answer="Тестовый ответ. Запрос: " + json.dumps(dict(request_data))
    )
    return response