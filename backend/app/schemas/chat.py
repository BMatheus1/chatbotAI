from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None


class Source(BaseModel):
    document_id: UUID
    filename: str
    page_number: int
    content: str
    score: float | None = None


class ChatResponse(BaseModel):
    conversation_id: UUID
    message: str
    sources: list[Source]


class MessageRead(BaseModel):
    id: UUID
    role: str
    content: str
    message_metadata: dict | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationRead(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[MessageRead] = []

    model_config = {"from_attributes": True}


class ConversationSummary(BaseModel):
    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int

