import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.ai.openai_client import openai_service
from app.core.config import settings
from app.models.document import Document, DocumentChunk
from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import chunking_service
from app.services.pdf_service import pdf_service


class DocumentService:
    def upload_and_index(self, db: Session, file: UploadFile) -> Document:
        if file.content_type != "application/pdf":
            raise ValueError("Apenas arquivos PDF sao aceitos.")

        settings.upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = f"{uuid.uuid4()}-{Path(file.filename or 'documento.pdf').name}"
        storage_path = settings.upload_dir / safe_name

        with storage_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        max_bytes = settings.max_upload_mb * 1024 * 1024
        if storage_path.stat().st_size > max_bytes:
            storage_path.unlink(missing_ok=True)
            raise ValueError(f"O arquivo excede o limite de {settings.max_upload_mb} MB.")

        pages = pdf_service.extract_pages(storage_path)
        if self._needs_ocr(pages) and settings.enable_ocr_fallback:
            pages = self._extract_pages_with_ocr(storage_path, file.filename or safe_name)

        chunk_payloads: list[tuple[int, int, str]] = []

        for page_number, page_text in pages:
            for chunk_index, chunk in enumerate(chunking_service.chunk_text(page_text)):
                chunk_payloads.append((page_number, chunk_index, chunk))

        if not chunk_payloads:
            storage_path.unlink(missing_ok=True)
            raise ValueError("Nao foi possivel extrair texto do PDF.")

        embeddings = openai_service.embed_texts([payload[2] for payload in chunk_payloads])
        repository = DocumentRepository(db)
        document = repository.create(
            Document(
                filename=safe_name,
                original_filename=file.filename or safe_name,
                content_type=file.content_type,
                storage_path=str(storage_path),
                chunk_count=len(chunk_payloads),
            )
        )

        chunks = [
            DocumentChunk(
                document_id=document.id,
                page_number=page_number,
                chunk_index=chunk_index,
                content=content,
                embedding=embedding,
            )
            for (page_number, chunk_index, content), embedding in zip(
                chunk_payloads, embeddings, strict=True
            )
        ]
        repository.add_chunks(chunks)
        db.commit()
        db.refresh(document)
        return document

    def list_documents(self, db: Session) -> list[Document]:
        return DocumentRepository(db).list_all()

    def _needs_ocr(self, pages: list[tuple[int, str]]) -> bool:
        return sum(len(text.strip()) for _, text in pages) < 200

    def _extract_pages_with_ocr(self, storage_path: Path, filename: str) -> list[tuple[int, str]]:
        extracted_pages: list[tuple[int, str]] = []

        if not openai_service.uses_openai:
            page_count = pdf_service.count_pages(storage_path)
            return [
                (
                    page_number,
                    f"Documento {filename}. {openai_service.extract_text_from_image(b'', page_number)}",
                )
                for page_number in range(1, page_count + 1)
            ]

        for page_number, image_bytes in pdf_service.render_page_images(storage_path):
            text = openai_service.extract_text_from_image(image_bytes, page_number)
            cleaned_text = " ".join(text.split())
            if cleaned_text:
                extracted_pages.append((page_number, cleaned_text))

        return extracted_pages


document_service = DocumentService()
