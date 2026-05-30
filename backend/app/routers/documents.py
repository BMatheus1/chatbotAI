from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.document import DocumentRead, DocumentUploadResponse
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(db: Session = Depends(get_db)) -> list:
    return document_service.list_documents(db)


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(file: UploadFile, db: Session = Depends(get_db)) -> dict:
    try:
        document = document_service.upload_and_index(db, file)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Falha ao processar o PDF. Verifique se OPENAI_API_KEY e uma chave valida "
                "e se a conta possui creditos para OCR e embeddings."
            ),
        ) from exc

    return {"document": document, "message": "PDF enviado e indexado com sucesso."}
