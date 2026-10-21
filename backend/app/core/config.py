from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Business Assistant"
    environment: str = "development"
    api_prefix: str = "/api"
    frontend_url: str = "http://localhost:3000"

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@postgres:5432/ai_business_assistant"
    )

    openai_api_key: str | None = None
    ai_provider: str = "mock"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"
    chat_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    upload_dir: Path = Path("uploads")
    max_upload_mb: int = 180
    retrieval_limit: int = 5
    conversation_memory_limit: int = 8
    enable_ocr_fallback: bool = True
    ocr_model: str = "gpt-4.1-mini"

    # WhatsApp Cloud API — parâmetros ausentes mantêm o webhook desligado.
    whatsapp_app_secret: str = ""
    whatsapp_webhook_verify_token: str = ""
    whatsapp_test_phone_number_id: str = ""
    whatsapp_auto_reply_enabled: bool = False  # reservada; sem implementação de envio

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
