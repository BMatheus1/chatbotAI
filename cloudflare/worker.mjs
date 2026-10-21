/**
 * Best Creations — WhatsApp Cloud API webhook EDGE (somente recebimento).
 * Não envia mensagens, não aciona IA, não registra conteúdo, não faz proxy
 * para serviços internos nem acessa o WhatsApp Business no celular.
 */
const WEBHOOK_PATH = "/api/webhooks/whatsapp";
const BODY_LIMIT = 256 * 1024;

function reply(body, status = 200, contentType = "text/plain; charset=utf-8") {
  return new Response(body, {
    status,
    headers: {
      "content-type": contentType,
      "cache-control": "no-store",
      "x-content-type-options": "nosniff",
    },
  });
}

function jsonReply(data, status = 200) {
  return reply(JSON.stringify(data), status, "application/json; charset=utf-8");
}

function decodeHexSignature(value) {
  if (typeof value !== "string" || !/^sha256=[a-f0-9]{64}$/i.test(value)) {
    return null;
  }
  const hex = value.substring(7);
  return Uint8Array.from(hex.match(/.{2}/g), (pair) => Number.parseInt(pair, 16));
}

export async function checkSignature(body, header, secret) {
  if (!secret || typeof secret !== "string") return false;
  const signature = decodeHexSignature(header);
  if (!signature) return false;
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" },
    false, ["verify"],
  );
  return crypto.subtle.verify("HMAC", key, signature, body);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if ((url.pathname === "/" || url.pathname === "/health") && request.method === "GET") {
      return jsonReply({ service: "best-creations-whatsapp-webhook", status: "standby", auto_reply: false });
    }

    if (url.pathname !== WEBHOOK_PATH) return reply("Not found", 404);

    if (request.method === "GET") {
      if (!env?.WHATSAPP_VERIFY_TOKEN) return reply("Webhook not configured", 503);

      const mode = url.searchParams.get("hub.mode");
      const token = url.searchParams.get("hub.verify_token");
      const challenge = url.searchParams.get("hub.challenge");
      if (mode !== "subscribe" || !token || token !== env.WHATSAPP_VERIFY_TOKEN) {
        return reply("Forbidden", 403);
      }
      if (!challenge || challenge.length > 1024) return reply("Missing challenge", 400);
      return reply(challenge);
    }

    if (request.method !== "POST") return reply("Method not allowed", 405);

    if (!env?.WHATSAPP_APP_SECRET) return reply("Webhook not configured", 503);

    const announcedSize = Number(request.headers.get("content-length"));
    if (Number.isFinite(announcedSize) && announcedSize > BODY_LIMIT) {
      return reply("Payload too large", 413);
    }
    const body = await request.arrayBuffer();
    if (body.byteLength > BODY_LIMIT) return reply("Payload too large", 413);

    let valid = false;
    try {
      valid = await checkSignature(
        body, request.headers.get("x-hub-signature-256"), env.WHATSAPP_APP_SECRET,
      );
    } catch {
      return reply("Signature verification unavailable", 503);
    }
    if (!valid) return reply("Invalid signature", 403);

    let payload;
    try {
      payload = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(body));
    } catch {
      return reply("Invalid JSON", 400);
    }
    if (!payload || payload.object !== "whatsapp_business_account") {
      return reply("Unexpected event", 400);
    }

    // ACK apenas: não armazena conteúdo, não dispara IA nem envia respostas.
    // O estágio seguinte integrará processamento e persistência de forma segura.
    return jsonReply({ status: "accepted", auto_reply: false });
  },
};
