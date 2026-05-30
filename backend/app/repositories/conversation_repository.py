from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation, Message


class ConversationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, title: str = "Nova conversa") -> Conversation:
        conversation = Conversation(title=title)
        self.db.add(conversation)
        self.db.flush()
        return conversation

    def get(self, conversation_id: UUID) -> Conversation | None:
        statement = (
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .options(selectinload(Conversation.messages))
        )
        return self.db.scalar(statement)

    def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            message_metadata=metadata,
        )
        self.db.add(message)
        self.db.flush()
        return message

    def update_title(self, conversation: Conversation, title: str) -> Conversation:
        conversation.title = title[:160]
        self.db.flush()
        return conversation

    def recent_messages(self, conversation_id: UUID, limit: int) -> list[Message]:
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(reversed(list(self.db.scalars(statement))))

    def list_summaries(self) -> list[tuple[Conversation, int]]:
        statement = (
            select(Conversation, func.count(Message.id).label("message_count"))
            .outerjoin(Message)
            .group_by(Conversation.id)
            .order_by(Conversation.updated_at.desc())
        )
        return [(conversation, count) for conversation, count in self.db.execute(statement).all()]

