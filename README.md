# AI Business Assistant

AI Business Assistant e um chatbot profissional com IA para atendimento de consultorios, clinicas, lojas, estetica e pequenos negocios. O projeto combina uma interface moderna em Next.js com um backend FastAPI, PostgreSQL com pgvector e RAG sobre PDFs enviados pelo administrador.

Foi pensado como projeto de portfolio: arquitetura clara, codigo modular, Docker, painel administrativo, historico de conversas e respostas baseadas em documentos.

## Modos de uso

- `AI_PROVIDER=mock`: modo demo gratuito. Nao exige chave OpenAI e permite testar upload, indexacao, busca vetorial, historico e chat.
- `AI_PROVIDER=openai`: modo real. Usa OpenAI API para embeddings, respostas naturais e OCR visual de PDFs escaneados.
- `AI_PROVIDER=gemini`: modo com Gemini API para gerar respostas finais e OCR visual de PDFs escaneados.

## Funcionalidades

- Chat com IA em estilo ChatGPT, responsivo e com dark mode.
- Upload de PDFs para FAQs, catalogos, procedimentos, politicas e tabelas de preco.
- Indexacao de documentos com chunking, embeddings e armazenamento vetorial.
- RAG com busca semantica em pgvector antes da resposta.
- Fallback de OCR para PDFs escaneados nos modos Gemini e OpenAI.
- OCR demonstrativo no modo mock para permitir testes sem custo.
- Historico de conversas com mensagens, contexto, fontes e timestamps.
- Painel administrativo para documentos, chunks e conversas.
- Ambiente completo com Docker e docker-compose.

## Stack

| Camada | Tecnologia |
| --- | --- |
| Frontend | Next.js, TypeScript, Tailwind CSS, componentes estilo shadcn/ui |
| Backend | FastAPI, Python, SQLAlchemy |
| Banco | PostgreSQL |
| Vetores | pgvector |
| IA | Provider mock no demo; Gemini API ou OpenAI API em producao |
| Infra | Docker, docker-compose |

## Arquitetura

```text
AI Business Assistant
+-- frontend/
|   +-- app/
|   +-- components/
|   +-- lib/
+-- backend/
|   +-- app/
|   |   +-- ai/
|   |   +-- core/
|   |   +-- models/
|   |   +-- repositories/
|   |   +-- routers/
|   |   +-- schemas/
|   |   +-- services/
|   +-- uploads/
+-- docker-compose.yml
+-- .env.example
```

## Fluxo RAG

1. O administrador envia um PDF no painel.
2. O backend salva o arquivo em `backend/uploads`.
3. O texto e extraido com `pypdf`.
4. Se o PDF nao tiver texto selecionavel, os modos Gemini/OpenAI usam OCR visual. O modo mock cria conteudo demonstrativo por pagina.
5. O conteudo e dividido em chunks com sobreposicao.
6. O provider configurado gera embeddings: OpenAI em producao ou vetores deterministicos locais no demo/Gemini.
7. Os chunks e vetores sao armazenados no PostgreSQL usando pgvector.
8. A pergunta do usuario tambem vira embedding.
9. O backend busca os chunks semanticamente mais proximos.
10. A resposta usa o contexto recuperado e a memoria recente da conversa.
11. Se `AI_PROVIDER=gemini`, o Gemini gera a resposta final com base no contexto recuperado.

## Instalacao

```bash
cp .env.example .env
```

O projeto ja vem configurado para modo demo:

```env
AI_PROVIDER=mock
OPENAI_API_KEY=
```

Para usar OpenAI real:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=sk-proj-sua-chave
```

Para usar Gemini API:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_gemini
GEMINI_MODEL=gemini-2.5-flash
```

## Integracao com Gemini API

O projeto pode usar Gemini API para gerar as respostas finais do chatbot e extrair texto visual de PDFs escaneados ou catalogos em imagem. A busca RAG, o chunking, o historico e o pgvector continuam preservados.

### Configurando a Gemini API

1. Acesse o Google AI Studio.
2. Gere uma API Key.
3. Crie ou edite o arquivo `.env` na raiz do projeto.
4. Adicione:

```env
AI_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_aqui
GEMINI_MODEL=gemini-2.5-flash
```

Nunca envie seu `.env` para o GitHub. O arquivo ja esta protegido pelo `.gitignore`.

### Testando a integracao

Com o backend rodando, acesse:

```text
http://localhost:8000/api/health/ai
```

Resposta esperada:

```json
{
  "provider": "gemini",
  "model": "gemini-2.5-flash",
  "configured": true
}
```

## Rodando com Docker

```bash
docker compose up --build
```

Servicos:

- Frontend: http://localhost:3000
- Admin: http://localhost:3000/admin
- Backend: http://localhost:8000
- Swagger/OpenAPI: http://localhost:8000/docs
- PostgreSQL: localhost:5432

## Rodando localmente

Backend:

```bash
docker compose up postgres
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

## Variaveis de ambiente

| Variavel | Descricao | Exemplo |
| --- | --- | --- |
| `AI_PROVIDER` | Provider de IA: `mock`, `gemini` ou `openai` | `mock` |
| `OPENAI_API_KEY` | Chave da OpenAI API quando `AI_PROVIDER=openai` | `sk-proj-...` |
| `GEMINI_API_KEY` | Chave da Gemini API quando `AI_PROVIDER=gemini` | `sua-chave` |
| `GEMINI_MODEL` | Modelo usado na Gemini API | `gemini-2.5-flash` |
| `DATABASE_URL` | URL SQLAlchemy do PostgreSQL | `postgresql+psycopg://postgres:postgres@postgres:5432/ai_business_assistant` |
| `FRONTEND_URL` | Origem liberada no CORS | `http://localhost:3000` |
| `CHAT_MODEL` | Modelo usado para resposta real | `gpt-4.1-mini` |
| `EMBEDDING_MODEL` | Modelo de embeddings real | `text-embedding-3-small` |
| `EMBEDDING_DIMENSIONS` | Dimensao dos vetores no pgvector | `1536` |
| `MAX_UPLOAD_MB` | Tamanho maximo de PDF aceito | `180` |
| `ENABLE_OCR_FALLBACK` | Ativa OCR quando o PDF nao tem texto | `true` |
| `OCR_MODEL` | Modelo usado para OCR visual real | `gpt-4.1-mini` |
| `NEXT_PUBLIC_API_URL` | URL publica da API para o frontend | `http://localhost:8000/api` |

## Como usar

1. Acesse `http://localhost:3000/admin`.
2. Envie um PDF.
3. Aguarde a indexacao.
4. Volte para `http://localhost:3000`.
5. Pergunte algo sobre o documento.
6. Veja as fontes recuperadas na lateral do chat.

No modo demo, as respostas indicam que sao simuladas. Isso permite que recrutadores testem o projeto sem billing externo. No modo OpenAI, a resposta e gerada por IA real.

## Endpoints principais

| Metodo | Rota | Descricao |
| --- | --- | --- |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/health/ai` | Verifica configuracao da Gemini API |
| `POST` | `/api/chat` | Envia mensagem e recebe resposta RAG |
| `GET` | `/api/documents` | Lista documentos indexados |
| `POST` | `/api/documents/upload` | Envia e indexa PDF |
| `GET` | `/api/conversations` | Lista conversas |
| `GET` | `/api/conversations/{id}` | Detalha conversa |

## Screenshots

Sugestao para o GitHub:

```text
docs/screenshots/chat.png
docs/screenshots/admin.png
```

## Roadmap

- Autenticacao para administradores.
- Multi-tenant para atender varios negocios na mesma instancia.
- Streaming de respostas no chat.
- Exclusao e reindexacao de documentos.
- Fila assincrona para PDFs grandes.
- Dashboard com metricas de atendimento.
- Integracoes com WhatsApp, Instagram e sites.
- Testes automatizados de backend e frontend.

## Licenca

Projeto criado para fins educacionais, portfolio e demonstracao tecnica.
