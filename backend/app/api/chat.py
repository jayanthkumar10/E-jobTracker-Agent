from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.services.chat_rag import ChatRAGService

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("")
def chat_ai(
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    Accepts conversational questions about user's career logs and queries hybrid RAG.
    """
    from app.services.chat_rag import ChatRAGService
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be blank.")
        
    result = ChatRAGService.answer_query(db, str(current_user.id), payload.message)
    return result
