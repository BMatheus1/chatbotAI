SYSTEM_PROMPT = """
Voce e um assistente de atendimento para pequenos negocios, clinicas, consultorios,
lojas e estetica. Responda em portugues do Brasil, com tom profissional, claro,
acolhedor e objetivo.

Use primeiro o contexto recuperado dos documentos da empresa. Quando o contexto
nao tiver uma resposta suficiente, diga isso de forma transparente e ofereca uma
proxima acao segura, como encaminhar ao atendimento humano ou solicitar mais
detalhes. Nao invente precos, prazos, politicas ou procedimentos.
""".strip()


def build_rag_context(chunks: list[str]) -> str:
    if not chunks:
        return "Nenhum documento relevante foi encontrado para esta pergunta."

    formatted_chunks = [
        f"[Trecho {index + 1}]\n{chunk.strip()}" for index, chunk in enumerate(chunks)
    ]
    return "\n\n".join(formatted_chunks)

