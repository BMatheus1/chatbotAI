from fastapi import APIRouter

from app.ai.gemini_client import gemini_service
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ai")
def ai_health_check() -> dict[str, bool | str]:
    return {
        "provider": "gemini",
        "model": settings.gemini_model,
        "configured": gemini_service.configured,
    }
