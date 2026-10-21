"""Validação e extração mínima de eventos da WhatsApp Cloud API.

Não guarda texto, número de telefone ou payload integral.
Não importa modelos de IA e jamais envia mensagens.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Any


def verify_meta_signature(body: bytes, header: str | None, app_secret: str) -> bool:
    if not app_secret or not header or not header.startswith("sha256="):
        return False
    supplied = header.removeprefix("sha256=")
    if len(supplied) != 64:
        return False
    expected = hmac.new(app_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, supplied)


def verify_challenge(mode: str | None, token: str | None, expected_token: str) -> bool:
    return bool(
        expected_token and mode == "subscribe" and token
        and hmac.compare_digest(token, expected_token)
    )


def extract_incoming_metadata(payload: Any, app_secret: str) -> list[dict[str, str]]:
    """Extrai metadados de mensagens recebidas, ignorando status e ecos do app.

    Os textos recebidos não são lidos pela versão de teste.
    """
    if not app_secret:
        raise ValueError("App secret necessário para anonimizar remetente.")
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return []
    result: list[dict[str, str]] = []
    for entry in payload.get("entry", []):
        if not isinstance(entry, dict):
            continue
        for change in entry.get("changes", []):
            if not isinstance(change, dict) or change.get("field") != "messages":
                continue
            value = change.get("value", {})
            if not isinstance(value, dict):
                continue
            metadata = value.get("metadata", {})
            if not isinstance(metadata, dict):
                continue
            phone_id = str(metadata.get("phone_number_id", ""))[:64]
            messages = value.get("messages", [])
            if not isinstance(messages, list):
                continue
            for message in messages:
                if not isinstance(message, dict):
                    continue
                message_id = message.get("id")
                sender = message.get("from")
                if not isinstance(message_id, str) or not 1 <= len(message_id) <= 255:
                    continue
                if not isinstance(sender, str) or not sender:
                    continue
                sender_digest = hmac.new(
                    app_secret.encode("utf-8"),
                    ("whatsapp:" + sender).encode("utf-8"),
                    hashlib.sha256,
                ).hexdigest()
                result.append({
                    "message_id": message_id,
                    "phone_number_id": phone_id,
                    "sender_hash": sender_digest,
                    "message_type": str(message.get("type", "unknown"))[:32],
                })
    return result
