from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.openai_client import openai_service
from app.ai.prompts import SYSTEM_PROMPT, build_rag_context
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.document import DocumentChunk
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.document_repository import DocumentRepository


class ChatService:
    def send_message(self, db: Session, message: str, conversation_id: UUID | None) -> dict:
        conversations = ConversationRepository(db)
        documents = DocumentRepository(db)

        conversation = self._get_or_create_conversation(conversations, conversation_id, message)
        conversations.add_message(conversation.id, "user", message)

        query_embedding = openai_service.embed_texts([message])[0]
        retrieved_results = documents.semantic_search(query_embedding, settings.retrieval_limit)
        retrieved_chunks = [chunk for chunk, _distance in retrieved_results]
        memory = conversations.recent_messages(conversation.id, settings.conversation_memory_limit)

        answer = openai_service.generate_answer(
            instructions=SYSTEM_PROMPT,
            input_text=self._build_model_input(message, retrieved_chunks, memory),
        )

        source_metadata = [
            self._source_payload(chunk, distance) for chunk, distance in retrieved_results
        ]
        conversations.add_message(
            conversation.id,
            "assistant",
            answer,
            metadata={"sources": source_metadata},
        )
        db.commit()

        return {
            "conversation_id": conversation.id,
            "message": answer,
            "sources": source_metadata,
        }

    def _get_or_create_conversation(
        self,
        repository: ConversationRepository,
        conversation_id: UUID | None,
        first_message: str,
    ) -> Conversation:
        if conversation_id:
            conversation = repository.get(conversation_id)
            if conversation:
                return conversation

        title = first_message.strip().replace("\n", " ")[:80] or "Nova conversa"
        return repository.create(title=title)

    def _build_model_input(
        self,
        message: str,
        chunks: list[DocumentChunk],
        memory: list,
    ) -> str:
        context = build_rag_context([chunk.content for chunk in chunks])
        history = "\n".join(
            f"{item.role}: {item.content}" for item in memory if item.content.strip()
        )

        return f"""
Contexto dos documentos:
{context}

Historico recente:
{history or "Sem historico anterior."}

Mensagem atual do cliente:
{message}
""".strip()

    def _source_payload(self, chunk: DocumentChunk, distance: float) -> dict:
        return {
            "document_id": chunk.document_id,
            "filename": chunk.document.original_filename if chunk.document else "Documento",
            "page_number": chunk.page_number,
            "content": chunk.content[:500],
            "score": round(max(0.0, 1.0 - distance), 4),
        }


chat_service = ChatService()
