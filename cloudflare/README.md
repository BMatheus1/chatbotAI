# Cloudflare Worker — WhatsApp webhook (somente testes)

Este Worker resolve o erro de deploy **"Could not detect a directory containing static files"** quando o Cloudflare Workers Builds tenta executar `npx wrangler deploy` na raiz do repositório.

- `wrangler.jsonc`: arquivo de configuração com `main: cloudflare/worker.mjs`.
- `cloudflare/worker.mjs`: endpoint HTTP público, sem dependências, independente de FastAPI/Docker/PostgreSQL.
- `GET /health`: retorna `status: standby`, `auto_reply: false`.
- `GET /api/webhooks/whatsapp`: confirma `hub.challenge` se `hub.verify_token` coincidir com o Secret do Worker.
- `POST /api/webhooks/whatsapp`: verifica `X-Hub-Signature-256` contra o corpo bruto e o App Secret da Meta. Aceita eventos válidos e retorna somente confirmação.
- **Não chama FastAPI**, **não envia mensagens**, **não chama modelos de IA**, **não armazena mensagens** nem o telefone de clientes.

## Cloudflare Workers Builds — configurações

Conecte o repositório `BMatheus1/chatbotAI`, branch `main`.

- **Root directory:** raiz do repositório (`/`, `.` ou valor vazio no painel, conforme a interface).
- **Build command:** deixe vazio.
- **Deploy command:** `npx wrangler deploy`.
- O nome definido em `wrangler.jsonc` é `best-creations-whatsapp-webhook`; se já existir um Worker configurado com outro nome, ajuste para o nome desejado antes de publicar.

O deploy exige autorização normal da Cloudflare na sua conta, mas **não exige instalar FastAPI ou PostgreSQL**.

## Secrets do Worker

Após o primeiro deploy, na Cloudflare abra **Workers & Pages > best-creations-whatsapp-webhook > Settings > Variables and Secrets > Add**. Adicione como **Secret** (não texto simples):

- `WHATSAPP_VERIFY_TOKEN`: escolha um valor aleatório forte. Repita exatamente o mesmo valor no campo "Verify token" dos Webhooks da Meta. Esse token é escolhido por você, não precisa gerar token de acesso da API.
- `WHATSAPP_APP_SECRET`: App Secret do **novo aplicativo Meta** (Meta Developers > App Settings > Basic).

Nunca cole essas informações no repositório, em logs, issues, screenshots ou chats. **Não precisa configurar token de acesso ao WhatsApp** neste estágio; este Worker não envia mensagens.

## URL para a Meta

Após um deploy bem-sucedido, copie o endereço público do Worker exibido pela Cloudflare e anexe:

`/api/webhooks/whatsapp`

A URL final será semelhante a:

`https://best-creations-whatsapp-webhook.<seu-subdominio>.workers.dev/api/webhooks/whatsapp`

Use o endereço **real** do seu painel, não o exemplo acima.

Em Meta Developers > WhatsApp > Configuração > Webhooks, informe:

- **Callback URL:** URL completa do Worker.
- **Verify token:** exatamente o Secret `WHATSAPP_VERIFY_TOKEN` cadastrado na Cloudflare.

Depois de verificar, é possível assinar o campo `messages` usando apenas a **conta e o número de teste** da Meta, para avaliar o recebimento sem tocar no número comercial.

## Testes locais

Com Node.js moderno:

```bash
node --test cloudflare/worker.test.mjs
```

Os testes usam eventos artificiais e não realizam chamadas para Meta.

## Limitações e segurança

A confirmação de um webhook não significa integração com IA. O Worker apenas **reconhece eventos autenticados** e não encaminha mensagens. A implementação FastAPI anterior continua separada, não é exposta por este Worker.

Não configure o número real antes de verificar formalmente a opção de **WhatsApp Business App Coexistence** para mantê-lo funcionando no celular.

Não publique a aplicação FastAPI, painel administrativo ou banco PostgreSQL sem autenticação de produção, proteção de documentos e controles de privacidade.

No próximo estágio, criar integração Worker → backend com autorização entre serviços, filas, idempotência persistente e modo de teste, sem responder clientes automaticamente.
