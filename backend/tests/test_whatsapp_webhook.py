"""Testes locais do webhook WhatsApp; nenhuma chamada externa ou envio real."""
import hashlib
import hmac
import json
import os
import unittest
from contextlib import nullcontext
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.core.database import get_db
from app.routers.whatsapp import router
from app.services.whatsapp_webhook import (
    extract_incoming_metadata,
    verify_challenge,
    verify_meta_signature,
)

SECRET = "whatsapp-unit-test-secret"
VERIFY_TOKEN = "token-apenas-testes"


def sample_payload():
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "waba-demo",
            "changes": [{
                "field": "messages",
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"phone_number_id": "test-phone-id"},
                    "messages": [{
                        "from": "5511999999999",
                        "id": "wamid.test-001",
                        "timestamp": "1720000000",
                        "type": "text",
                        "text": {"body": "Conteúdo privado que NÃO deve ser salvo"},
                    }],
                },
            }],
        }],
    }


class FakeDb:
    def __init__(self):
        self.events = {}
        self.pending = None
        self.commits = 0

    def begin_nested(self):
        return nullcontext()

    def add(self, event):
        self.pending = event

    def flush(self):
        if self.pending.message_id in self.events:
            raise IntegrityError("duplicate", {}, Exception("duplicate"))
        self.events[self.pending.message_id] = self.pending

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.pending = None


class WhatsAppWebhookUnitTests(unittest.TestCase):
    def setUp(self):
        self.db = FakeDb()
        app = FastAPI()
        app.include_router(router, prefix="/api")
        app.dependency_overrides[get_db] = lambda: self.db
        self.client = TestClient(app)
        self.patches = [
            patch.object(settings, "whatsapp_app_secret", SECRET),
            patch.object(settings, "whatsapp_webhook_verify_token", VERIFY_TOKEN),
            patch.object(settings, "whatsapp_test_phone_number_id", ""),
            patch.object(settings, "whatsapp_auto_reply_enabled", False),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.client.close()

    def sign(self, data):
        body = json.dumps(data, separators=(",", ":")).encode("utf-8")
        mac = hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()
        return body, {"X-Hub-Signature-256": "sha256=" + mac}

    def test_meta_signature_valid(self):
        body, headers = self.sign(sample_payload())
        self.assertTrue(verify_meta_signature(body, headers["X-Hub-Signature-256"], SECRET))
        self.assertFalse(verify_meta_signature(body + b" ", headers["X-Hub-Signature-256"], SECRET))

    def test_meta_signature_missing_or_invalid(self):
        self.assertFalse(verify_meta_signature(b"abc", None, SECRET))
        self.assertFalse(verify_meta_signature(b"abc", "sha256=incorrect", SECRET))
        self.assertFalse(verify_meta_signature(b"abc", "sha256=abc", ""))

    def test_challenge_verification(self):
        self.assertTrue(verify_challenge("subscribe", VERIFY_TOKEN, VERIFY_TOKEN))
        self.assertFalse(verify_challenge("subscribe", "wrong", VERIFY_TOKEN))
        self.assertFalse(verify_challenge("subscribe", VERIFY_TOKEN, ""))

    def test_get_verification_success(self):
        result = self.client.get("/api/webhooks/whatsapp", params={
            "hub.mode": "subscribe",
            "hub.verify_token": VERIFY_TOKEN,
            "hub.challenge": "123456",
        })
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.text, "123456")

    def test_get_verification_invalid(self):
        result = self.client.get("/api/webhooks/whatsapp", params={
            "hub.mode": "subscribe", "hub.verify_token": "wrong",
            "hub.challenge": "123",
        })
        self.assertEqual(result.status_code, 403)

    def test_post_without_signature_rejected(self):
        result = self.client.post("/api/webhooks/whatsapp", json=sample_payload())
        self.assertEqual(result.status_code, 403)
        self.assertEqual(len(self.db.events), 0)

    def test_post_bad_signature_rejected(self):
        result = self.client.post("/api/webhooks/whatsapp",
            content=b"{}",
            headers={"X-Hub-Signature-256": "sha256=" + "a" * 64})
        self.assertEqual(result.status_code, 403)

    def test_post_valid_signed_event_never_replies(self):
        body, headers = self.sign(sample_payload())
        result = self.client.post("/api/webhooks/whatsapp", content=body, headers=headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["new_events"], 1)
        self.assertFalse(result.json()["auto_reply"])
        event = self.db.events["wamid.test-001"]
        self.assertEqual(event.message_type, "text")
        self.assertNotIn("5511999999999", str(event.__dict__))
        self.assertNotIn("Conteúdo privado", str(event.__dict__))

    def test_post_is_idempotent(self):
        body, headers = self.sign(sample_payload())
        a = self.client.post("/api/webhooks/whatsapp", content=body, headers=headers)
        b = self.client.post("/api/webhooks/whatsapp", content=body, headers=headers)
        self.assertEqual(a.json()["new_events"], 1)
        self.assertEqual(b.json()["new_events"], 0)
        self.assertEqual(len(self.db.events), 1)

    def test_status_events_and_echoes_not_ingested(self):
        data = sample_payload()
        data["entry"][0]["changes"] = [
            {"field": "messages", "value": {"statuses": [{"id": "msg-status"}]}},
            {"field": "smb_message_echoes", "value": {"messages": [{"id": "echo"}]}},
        ]
        body, headers = self.sign(data)
        res = self.client.post("/api/webhooks/whatsapp", content=body, headers=headers)
        self.assertEqual(res.json()["new_events"], 0)
        self.assertFalse(self.db.events)

    def test_phone_filter_blocks_other_numbers(self):
        with patch.object(settings, "whatsapp_test_phone_number_id", "other-phone"):
            body, headers = self.sign(sample_payload())
            res = self.client.post("/api/webhooks/whatsapp", content=body, headers=headers)
            self.assertEqual(res.json()["new_events"], 0)

    def test_malformed_json_rejected(self):
        raw = b"not json"
        sig = hmac.new(SECRET.encode(), raw, hashlib.sha256).hexdigest()
        res = self.client.post("/api/webhooks/whatsapp", content=raw,
            headers={"X-Hub-Signature-256": "sha256=" + sig})
        self.assertEqual(res.status_code, 400)

    def test_missing_app_secret_fails_closed(self):
        with patch.object(settings, "whatsapp_app_secret", ""):
            body, headers = self.sign(sample_payload())
            res = self.client.post("/api/webhooks/whatsapp", content=body, headers=headers)
            self.assertEqual(res.status_code, 503)

    def test_extraction_returns_no_plaintext(self):
        metadata = extract_incoming_metadata(sample_payload(), SECRET)
        self.assertEqual(len(metadata), 1)
        self.assertEqual(set(metadata[0]), {
            "message_id", "phone_number_id", "sender_hash", "message_type"
        })
        self.assertEqual(len(metadata[0]["sender_hash"]), 64)

    def test_ignores_unrecognized_event(self):
        self.assertEqual(extract_incoming_metadata({"object":"page"}, SECRET), [])


if __name__ == "__main__":
    unittest.main()
