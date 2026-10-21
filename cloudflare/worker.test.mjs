import test from "node:test";
import assert from "node:assert/strict";
import { createHmac, webcrypto } from "node:crypto";
import worker, { checkSignature } from "./worker.mjs";

if (!globalThis.crypto) globalThis.crypto = webcrypto;

const ENDPOINT = "https://example.workers.dev/api/webhooks/whatsapp";
const env = { WHATSAPP_VERIFY_TOKEN: "a-very-secret-verification-token", WHATSAPP_APP_SECRET: "app-secret-test" };
function request(path, init) { return new Request(path, init); }
function signedPost(payload = { object: "whatsapp_business_account", entry: [] }) {
  const bytes = JSON.stringify(payload);
  const hex = createHmac("sha256", env.WHATSAPP_APP_SECRET).update(bytes).digest("hex");
  return request(ENDPOINT, {
    method: "POST",
    headers: { "content-type": "application/json", "x-hub-signature-256": "sha256=" + hex },
    body: bytes,
  });
}
test("health endpoint is read-only and reports auto reply off", async () => {
  const res = await worker.fetch(request("https://example.workers.dev/health"), env);
  assert.equal(res.status, 200);
  assert.deepEqual(await res.json(), { service: "best-creations-whatsapp-webhook", status: "standby", auto_reply: false });
});
test("meta verification returns exact challenge", async () => {
  const url = ENDPOINT + "?hub.mode=subscribe&hub.verify_token=a-very-secret-verification-token&hub.challenge=12345678";
  const res = await worker.fetch(request(url), env);
  assert.equal(res.status, 200);
  assert.equal(await res.text(), "12345678");
});
test("rejects incorrect GET token", async () => {
  const res = await worker.fetch(request(ENDPOINT + "?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=100"), env);
  assert.equal(res.status, 403);
});
test("missing verify token fails closed", async () => {
  const res = await worker.fetch(request(ENDPOINT + "?hub.mode=subscribe&hub.verify_token=x&hub.challenge=100"), {});
  assert.equal(res.status, 503);
});
test("signed WhatsApp POST accepted without sending any message", async () => {
  const oldFetch = globalThis.fetch;
  globalThis.fetch = () => { throw new Error("Network calls are forbidden"); };
  try {
    const res = await worker.fetch(signedPost(), env);
    assert.equal(res.status, 200);
    assert.deepEqual(await res.json(), { status: "accepted", auto_reply: false });
  } finally {
    globalThis.fetch = oldFetch;
  }
});
test("rejects missing signature", async () => {
  const res = await worker.fetch(request(ENDPOINT, { method: "POST", body: "{}" }), env);
  assert.equal(res.status, 403);
});
test("rejects tampered payload", async () => {
  const signed = signedPost();
  const body = await signed.text();
  const res = await worker.fetch(request(ENDPOINT, {
    method: "POST", body: body + " ",
    headers: { "x-hub-signature-256": signed.headers.get("x-hub-signature-256") },
  }), env);
  assert.equal(res.status, 403);
});
test("invalid JSON with valid signature rejected", async () => {
  const raw = "not json";
  const hex = createHmac("sha256", env.WHATSAPP_APP_SECRET).update(raw).digest("hex");
  const res = await worker.fetch(request(ENDPOINT, {
    method: "POST", body: raw,
    headers: { "x-hub-signature-256": "sha256=" + hex },
  }), env);
  assert.equal(res.status, 400);
});
test("rejects signed unrelated webhook object", async () => {
  const res = await worker.fetch(signedPost({ object: "page", entry: [] }), env);
  assert.equal(res.status, 400);
});
test("missing app secret fails closed", async () => {
  const res = await worker.fetch(signedPost(), {});
  assert.equal(res.status, 503);
});
test("oversized payload rejected", async () => {
  const res = await worker.fetch(request(ENDPOINT, {
    method: "POST", headers: { "content-length": String(300_000) }, body: "{}",
  }), env);
  assert.equal(res.status, 413);
});
test("other methods or paths rejected", async () => {
  assert.equal((await worker.fetch(request("https://example.workers.dev/admin"), env)).status, 404);
  assert.equal((await worker.fetch(request(ENDPOINT, { method: "PUT" }), env)).status, 405);
});
test("signature helper rejects malformed signatures", async () => {
  assert.equal(await checkSignature(new ArrayBuffer(0), "sha256=deadbeef", env.WHATSAPP_APP_SECRET), false);
  assert.equal(await checkSignature(new ArrayBuffer(0), null, env.WHATSAPP_APP_SECRET), false);
});
