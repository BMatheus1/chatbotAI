import base64
import hashlib
import math
import re

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings


class OpenAIService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key) if self.uses_openai else None

    @property
    def uses_openai(self) -> bool:
        return settings.ai_provider.lower() == "openai"

    def _ensure_api_key(self) -> None:
        if not self.client:
            raise RuntimeError("OpenAI nao esta ativa. Configure AI_PROVIDER=openai.")
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY nao configurada.")

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not self.uses_openai:
            return [self._mock_embedding(text) for text in texts]

        self._ensure_api_key()
        embeddings: list[list[float]] = []

        for start in range(0, len(texts), 64):
            response = self.client.embeddings.create(
                model=settings.embedding_model,
                input=texts[start : start + 64],
                dimensions=settings.embedding_dimensions,
            )
            embeddings.extend(item.embedding for item in response.data)

        return embeddings

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def generate_answer(self, instructions: str, input_text: str) -> str:
        if not self.uses_openai:
            return self._mock_answer(input_text)

        self._ensure_api_key()
        assert self.client is not None
        response = self.client.chat.completions.create(
            model=settings.chat_model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": input_text},
            ],
        )
        return response.choices[0].message.content or ""

    @retry(wait=wait_exponential(multiplier=1, min=1, max=8), stop=stop_after_attempt(3))
    def extract_text_from_image(self, image_bytes: bytes, page_number: int) -> str:
        if not self.uses_openai:
            return self._mock_ocr(page_number)

        self._ensure_api_key()
        assert self.client is not None
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        response = self.client.chat.completions.create(
            model=settings.ocr_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extraia fielmente todo texto legivel desta pagina de catalogo em portugues. "
                        "Preserve nomes de produtos, codigos, medidas, precos e listas. "
                        "Nao descreva imagens decorativas e nao invente texto ausente."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": f"Extraia o texto da pagina {page_number}.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
        )
        return (response.choices[0].message.content or "").strip()

    def _mock_embedding(self, text: str) -> list[float]:
        tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", text.lower())
        vector = [0.0] * settings.embedding_dimensions

        for token in tokens or ["demo"]:
            digest = hashlib.sha256(token.encode("utf-8", errors="ignore")).digest()
            index = int.from_bytes(digest[:4], "big") % settings.embedding_dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _mock_answer(self, input_text: str) -> str:
        context = self._extract_section(
            input_text,
            "Contexto dos documentos:",
            "Historico recente:",
        )
        question = self._extract_section(input_text, "Mensagem atual do cliente:", None)
        snippets = [
            line.strip()
            for line in context.splitlines()
            if line.strip() and not line.strip().startswith("[Trecho")
        ][:3]

        if not snippets:
            return (
                "Modo demo ativo: nao encontrei trechos indexados suficientes para responder. "
                "Envie um PDF no painel administrativo ou use AI_PROVIDER=openai para IA real."
            )

        evidence = " ".join(snippets)
        return (
            "Modo demo ativo. Com base nos documentos indexados, a resposta mais provavel para "
            f"'{question[:180]}' e: {evidence[:700]} "
            "Para uma resposta natural com raciocinio completo, configure AI_PROVIDER=openai."
        )

    def _mock_ocr(self, page_number: int) -> str:
        return (
            f"Pagina {page_number} extraida em modo demo. Este PDF parece ser escaneado ou composto "
            "por imagens, entao o OCR real depende da OpenAI API. Para fins de portfolio, esta pagina "
            "foi indexada com conteudo demonstrativo para validar upload, chunking, embeddings locais, "
            "busca vetorial, historico e painel administrativo."
        )

    def _extract_section(self, text: str, start: str, end: str | None) -> str:
        pattern = re.escape(start) + r"(.*?)" + (re.escape(end) if end else r"\Z")
        match = re.search(pattern, text, flags=re.DOTALL)
        return match.group(1).strip() if match else ""


openai_service = OpenAIService()
