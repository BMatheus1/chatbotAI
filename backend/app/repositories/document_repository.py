from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.document import Document, DocumentChunk


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, document: Document) -> Document:
        self.db.add(document)
        self.db.flush()
        return document

    def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        self.db.add_all(chunks)
        self.db.flush()

    def list_all(self) -> list[Document]:
        statement = select(Document).order_by(Document.created_at.desc())
        return list(self.db.scalars(statement))

    def get(self, document_id: UUID) -> Document | None:
        return self.db.get(Document, document_id)

    def semantic_search(self, embedding: list[float], limit: int) -> list[tuple[DocumentChunk, float]]:
        distance = DocumentChunk.embedding.cosine_distance(embedding)
        statement = (
            select(DocumentChunk, distance.label("distance"))
            .options(joinedload(DocumentChunk.document))
            .order_by(distance)
            .limit(limit)
        )
        return [(chunk, float(distance_value)) for chunk, distance_value in self.db.execute(statement).all()]
