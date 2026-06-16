from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.chat import ConversationRead, ConversationSummary

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
def list_conversations(db: Session = Depends(get_db)) -> list[ConversationSummary]:
    repository = ConversationRepository(db)
    return [
        ConversationSummary(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            message_count=message_count,
        )
        for conversation, message_count in repository.list_summaries()
    ]


@router.get("/{conversation_id}", response_model=ConversationRead)
def get_conversation(conversation_id: UUID, db: Session = Depends(get_db)):
    conversation = ConversationRepository(db).get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa nao encontrada.")
    return conversation


@router.delete("")
def delete_all_conversations(db: Session = Depends(get_db)) -> dict[str, str | int]:
    repository = ConversationRepository(db)
    deleted_count = repository.delete_all()
    db.commit()
    return {
        "message": "Historico de conversas removido com sucesso.",
        "deleted_count": deleted_count,
    }


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: UUID, db: Session = Depends(get_db)) -> dict[str, str]:
    repository = ConversationRepository(db)
    conversation = repository.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversa nao encontrada.")

    repository.delete(conversation)
    db.commit()
    return {"message": "Conversa removida com sucesso."}
