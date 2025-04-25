from typing import Optional
from datetime import datetime
import logging
from sqlalchemy import Column, Integer, String, Text, DateTime, UUID
from sqlalchemy.orm import Session

from app.services.rag_service import RagRequest, RagResponse, stub_rag
from app.services.db import Base, engine

# 1) Настраиваем логгер для записи в файл
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('rag_requests.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] request_id=%(request_id)s thread_id=%(thread_id)s '
    'user_id=%(user_id)s chat_id=%(chat_id)s session_id=%(session_id)s '
    'question="%(question)s" answer="%(answer)s"'
))
logger.addHandler(file_handler)


class LogRag(Base):
    __tablename__ = 'log_rag'

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, nullable=False)
    thread_id = Column(UUID, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    user_id = Column(Integer, nullable=True)
    chat_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

Base.metadata.create_all(bind=engine)


def rag_send_message(
    request: RagRequest,
    db_session: Session,
    user_id: Optional[int] = None,
    chat_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> RagResponse:
    """
    Отправляет запрос в RAG-сервис, логирует запрос и ответ
    в таблицу log_rag и в файл rag_requests.log.
    """
    # Отправка запроса в RAG (stub)
    response: RagResponse = stub_rag(request)

    # 2) Логируем в базу
    log_entry = LogRag(
        request_id=request.id,
        thread_id=request.thread_id,
        question=request.question,
        answer=response.answer,
        user_id=user_id,
        chat_id=chat_id,
        session_id=session_id,
        timestamp=datetime.utcnow()
    )
    db_session.add(log_entry)
    db_session.commit()

    # 3) Логируем в файл
    logger.info(
        '',
        extra={
            'request_id': request.id,
            'thread_id': request.thread_id,
            'question': request.question,
            'answer': response.answer,
            'user_id': user_id,
            'chat_id': chat_id,
            'session_id': session_id
        }
    )

    return response
