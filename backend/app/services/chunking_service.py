class ChunkingService:
    def chunk_text(self, text: str, size: int = 1200, overlap: int = 180) -> list[str]:
        text = text.strip()
        if not text:
            return []

        chunks: list[str] = []
        start = 0

        while start < len(text):
            end = min(start + size, len(text))
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            if end == len(text):
                break
            start = max(end - overlap, start + 1)

        return chunks


chunking_service = ChunkingService()

