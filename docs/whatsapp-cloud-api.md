# WhatsApp Cloud API — modo de teste sem respostas automáticas

## Situação

Este repositório possui agora um **webhook de entrada** para a API oficial da Meta.
**Não está conectado a nenhum número real e NÃO envia respostas.**
O projeto mantém o WhatsApp Business do celular intacto: não registra, migra nem desconecta números.

A implementação deste estágio é propositalmente **receive-only**:

- `GET /api/webhooks/whatsapp` responde ao desafio de verificação com token.
- `POST /api/webhooks/whatsapp` aceita apenas eventos com HMAC-SHA256 válido em `X-Hub-Signature-256`.
- Somente mensagens recebidas (campo `messages`) são consideradas.
- Eventos de status e `smb_message_echoes` são ignorados; não causam resposta.
- Mensagens repetidas com o mesmo ID são ignoradas pela chave primária da tabela `whatsapp_webhook_events`.
- Armazena apenas ID do evento, ID do número comercial, hash HMAC do remetente, tipo e data. NÃO persiste texto, número do cliente, anexos ou payload bruto.
- Nenhuma chamada HTTP de saída para WhatsApp, Gemini ou OpenAI é feita no webhook.
- `WHATSAPP_AUTO_REPLY_ENABLED=false` é reservada para fase futura; a função de resposta automática **não existe** nesta etapa, mesmo que a variável seja alterada.

## Configuração futura (não preencher com o número real neste estágio)

Variáveis de ambiente no servidor, **nunca em arquivos commitados**:

```dotenv
WHATSAPP_WEBHOOK_VERIFY_TOKEN=gerar-um-valor-aleatorio-forte
WHATSAPP_APP_SECRET=secreto-do-app-da-meta
WHATSAPP_TEST_PHONE_NUMBER_ID=id-do-numero-de-teste-da-meta
WHATSAPP_AUTO_REPLY_ENABLED=false
```

- O token de verificação do webhook é definido por você e repetido no painel da Meta.
- `WHATSAPP_APP_SECRET` é o segredo privado do aplicativo Meta; não é o access token.
- Para enviar mensagens no futuro serão necessários `WHATSAPP_ACCESS_TOKEN` e `WHATSAPP_PHONE_NUMBER_ID`, que não são utilizados agora.
- O token do Instagram da outra automação não serve para WhatsApp.

O ambiente Python precisa de PostgreSQL com a extensão pgvector, como já definido no `docker-compose.yml`. A tabela `whatsapp_webhook_events` é adicionada na inicialização da aplicação. Antes de uso comercial, substituir `create_all` por migrações Alembic.

## Passo a passo de testes seguros

1. GitHub → Actions → **Testar webhook WhatsApp (sem mensagens reais)** → Run workflow.
2. Confira o resultado verde: os testes simulam GET, assinaturas POST, conteúdo privado e deduplicação.
3. Depois, para testar uma verificação real de webhook, configure backend HTTPS e use apenas o **número de teste** disponibilizado pela Meta.
4. Exemplo de URL de callback após deploy: `https://SEU-DOMINIO/api/webhooks/whatsapp`.
5. Configure os secrets somente no host do backend. **Nunca cole chaves em issues, README, screenshots ou chats.**
6. Não associe o número comercial real ainda.

## Coexistência — não migrar inadvertidamente o WhatsApp do celular

Para manter o **mesmo número ativo no WhatsApp Business do celular e na Cloud API**, é preciso fluxo de **WhatsApp Business App Coexistence**, normalmente via Embedded Signup compatível oferecido por parceiro da Meta (Tech Provider/Solution Partner). O fluxo de registro normal de número na Cloud API é diferente e pode impedir o uso simultâneo no aplicativo.

Antes de qualquer conexão do número real, verifique oficialmente:

- Se a conta é elegível.
- Se o fluxo suporta coexistência no seu caso.
- Se há restrições para recursos do aplicativo ou dispositivos conectados.
- Se a conexão exige um parceiro e quais são seus custos.
- Se há consentimento para sincronizar histórico e contatos.

**Não desinstale o WhatsApp Business, não exclua a conta e não faça registro convencional desse número.**

## Bloqueadores antes de expor o backend ao público

O repositório existente ainda precisa de revisão de segurança:
- `/api/documents`, `/api/conversations` e o painel `/admin` não têm autenticação adequada para produção.
- É necessário proteger rotas administrativas, limitar upload e acesso a documentos.
- Definir retenção e privacidade dos metadados recebidos pelo webhook.
- Implementar observabilidade, limites e migrações de banco.
- Para responder clientes no futuro, criar processamento assíncrono, associação de conversa por contato, transferência ao humano, cumprimento da janela de atendimento e regras de opt-in.
- Um GitHub Actions não substitui um backend HTTPS sempre disponível para webhooks.

**Este teste não certifica um deploy público nem autoriza respostas automáticas.**
