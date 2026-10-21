"""Registro mínimo de mensagens recebidas para idempotência.

Não persiste texto, remetente original, anexos ou payload completo.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WhatsAppWebhookEvent(Base):
    __tablename__ = "whatsapp_webhook_events"

    message_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    phone_number_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sender_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    message_type: Mapped[str] = mapped_column(String(32), nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
