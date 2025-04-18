from typing import Optional
from app.services.rag_service import RagRequest, RagResponse, stub_rag

from sqlalchemy.orm import Session

def rag_send_message(request: RagRequest, session: Session, user_id: Optional[str] = None, chat_id: Optional[str] = None, session_id: Optional[str] = None) -> RagResponse:
    # Log request

    response = stub_rag(request)

    # Log response

    return response