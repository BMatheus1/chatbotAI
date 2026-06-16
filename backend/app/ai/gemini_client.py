import logging

from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self) -> None:
        self.client = genai.Client(api_key=settings.gemini_api_key) if settings.gemini_api_key else None

    @property
    def configured(self) -> bool:
        return bool(settings.gemini_api_key)

    def generate_answer(
        self,
        message: str,
        context_chunks: list[str],
        history: list[tuple[str, str]],
    ) -> str:
        if not self.client:
            raise RuntimeError(
                "Gemini API key nao configurada. Defina GEMINI_API_KEY no arquivo .env."
            )

        prompt = self._build_prompt(message, context_chunks, history)

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )
        except Exception as exc:
            logger.exception("Gemini generation failed")
            raise RuntimeError(
                "Nao consegui gerar uma resposta agora. Tente novamente em instantes."
            ) from exc

        text = getattr(response, "text", None)
        if not text or not text.strip():
            logger.warning("Gemini returned an empty response")
            raise RuntimeError(
                "Nao consegui gerar uma resposta agora. Tente novamente em instantes."
            )

        return text.strip()

    def extract_text_from_image(self, image_bytes: bytes, page_number: int) -> str:
        if not self.client:
            raise RuntimeError(
                "Gemini API key nao configurada. Defina GEMINI_API_KEY no arquivo .env."
            )

        prompt = (
            f"Extraia fielmente todo texto legivel da pagina {page_number} deste PDF/catalogo. "
            "Preserve nomes de produtos, codigos, medidas, precos, listas, tabelas e observacoes. "
            "Nao invente texto ausente. Nao descreva imagens decorativas. "
            "Se nao houver texto legivel, responda apenas: SEM_TEXTO_LEGIVEL."
        )

        try:
            response = self.client.models.generate_content(
                model=settings.gemini_model,
                contents=[
                    prompt,
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                ],
            )
        except Exception as exc:
            logger.exception("Gemini OCR failed")
            raise RuntimeError(
                "Nao consegui extrair texto visual do PDF agora. Tente novamente em instantes."
            ) from exc

        text = (getattr(response, "text", None) or "").strip()
        if not text or text == "SEM_TEXTO_LEGIVEL":
            return ""

        return text

    def _build_prompt(
        self,
        message: str,
        context_chunks: list[str],
        history: list[tuple[str, str]],
    ) -> str:
        context = "\n\n".join(
            f"[Trecho {index + 1}]\n{chunk.strip()}"
            for index, chunk in enumerate(context_chunks)
            if chunk.strip()
        )
        formatted_history = "\n".join(
            f"{role}: {content}" for role, content in history if content.strip()
        )

        return f"""
Voce e um assistente virtual de atendimento para pequenos negocios, consultorios,
clinicas, lojas e estetica.

Regras:
- responda em portugues do Brasil;
- seja claro, educado, objetivo e profissional;
- organize a resposta para leitura em WhatsApp/chat;
- use paragrafos curtos e listas quando houver muitos itens;
- use Markdown simples: **negrito** para categorias importantes e bullets com "-";
- nao entregue listas em uma unica linha;
- pule linha entre introducao, lista e fechamento;
- use o contexto dos documentos quando disponivel;
- nao invente precos, prazos, politicas ou procedimentos;
- se a resposta nao estiver no contexto, diga que nao encontrou essa informacao na base disponivel;
- sugira contato humano quando necessario.

Base de conhecimento:
{context or "Nenhum trecho relevante foi encontrado."}

Historico recente da conversa:
{formatted_history or "Sem historico anterior."}

Pergunta do cliente:
{message}

Responda de forma educada, objetiva e util, em formato bonito para o cliente final.
""".strip()


gemini_service = GeminiService()
