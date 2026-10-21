"""Webhook de teste da Meta WhatsApp Cloud API.

GET valida o desafio; POST autentica assinatura e registra somente metadados.
NÃO responde ao WhatsApp nem aciona IA, independentemente das variáveis de ambiente.
"""
import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.whatsapp_event import WhatsAppWebhookEvent
from app.services.whatsapp_webhook import (
    extract_incoming_metadata,
    verify_challenge,
    verify_meta_signature,
)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["whatsapp-webhook"])
MAX_WEBHOOK_BODY_BYTES = 256 * 1024


@router.get("")
def verify_webhook(request: Request) -> PlainTextResponse:
    if not settings.whatsapp_webhook_verify_token:
        raise HTTPException(status_code=503, detail="Webhook ainda não configurado.")
    params = request.query_params
    if not verify_challenge(
        params.get("hub.mode"),
        params.get("hub.verify_token"),
        settings.whatsapp_webhook_verify_token,
    ):
        raise HTTPException(status_code=403, detail="Verificação recusada.")
    challenge = params.get("hub.challenge")
    if challenge is None:
        raise HTTPException(status_code=400, detail="Desafio ausente.")
    return PlainTextResponse(challenge)


@router.post("")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db),
) -> dict:
    if not settings.whatsapp_app_secret:
        raise HTTPException(status_code=503, detail="Webhook ainda não configurado.")

    body = await request.body()
    if len(body) > MAX_WEBHOOK_BODY_BYTES:
        raise HTTPException(status_code=413, detail="Evento excede o limite permitido.")
    if not verify_meta_signature(body, x_hub_signature_256, settings.whatsapp_app_secret):
        raise HTTPException(status_code=403, detail="Assinatura inválida.")

    try:
        payload = json.loads(body)
    except (ValueError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Evento inválido.") from None

    messages = extract_incoming_metadata(payload, settings.whatsapp_app_secret)
    new_messages = 0
    try:
        for item in messages:
            if (
                settings.whatsapp_test_phone_number_id
                and item["phone_number_id"] != settings.whatsapp_test_phone_number_id
            ):
                continue
            try:
                with db.begin_nested():
                    db.add(WhatsAppWebhookEvent(**item))
                    db.flush()
                new_messages += 1
            except IntegrityError:
                # A Meta pode repetir a entrega do mesmo evento.
                continue
        db.commit()
    except Exception:
        db.rollback()
        # Retornar erro permite que a Meta tente reenviar o webhook.
        raise HTTPException(status_code=503, detail="Falha temporária de processamento.") from None

    return {
        "status": "accepted",
        "events_received": len(messages),
        "new_events": new_messages,
        "auto_reply": False,
    }
