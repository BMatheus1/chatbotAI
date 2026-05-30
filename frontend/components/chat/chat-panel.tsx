"use client";

import { FormEvent, useMemo, useRef, useState } from "react";
import { FileText, Loader2, Send, Sparkles } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { ChatMessage } from "@/components/chat/chat-message";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { sendChatMessage } from "@/lib/api";
import type { ChatMessage as ChatMessageType, Source } from "@/lib/types";

const suggestions = [
  "Quais servicos estao disponiveis?",
  "Qual e a faixa de preco?",
  "Como funciona o agendamento?"
];

export function ChatPanel() {
  const [messages, setMessages] = useState<ChatMessageType[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Ola! Sou o assistente virtual da empresa. Posso responder com base nos documentos cadastrados no painel administrativo."
    }
  ]);
  const [conversationId, setConversationId] = useState<string>();
  const [input, setInput] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const canSend = useMemo(() => input.trim().length > 0 && !isLoading, [input, isLoading]);

  async function handleSubmit(event?: FormEvent) {
    event?.preventDefault();
    const content = input.trim();
    if (!content) return;

    setError(null);
    setInput("");
    setSources([]);
    setIsLoading(true);
    setMessages((current) => [
      ...current,
      { id: crypto.randomUUID(), role: "user", content }
    ]);

    try {
      const response = await sendChatMessage(content, conversationId);
      setConversationId(response.conversation_id);
      setSources(response.sources);
      setMessages((current) => [
        ...current,
        { id: crypto.randomUUID(), role: "assistant", content: response.message }
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro inesperado ao enviar mensagem.");
    } finally {
      setIsLoading(false);
      textareaRef.current?.focus();
    }
  }

  function applySuggestion(value: string) {
    setInput(value);
    textareaRef.current?.focus();
  }

  return (
    <AppShell>
      <section className="mx-auto grid min-h-[calc(100vh-4rem)] max-w-7xl grid-cols-1 gap-6 px-4 py-6 sm:px-6 lg:grid-cols-[1fr_340px]">
        <div className="flex min-h-[72vh] flex-col rounded-lg border bg-card">
          <div className="flex items-center justify-between border-b px-5 py-4">
            <div>
              <h1 className="text-lg font-semibold">Atendimento IA</h1>
              <p className="text-sm text-muted-foreground">Chat com RAG, memoria curta e fontes documentais.</p>
            </div>
            <Badge>
              <Sparkles className="mr-1 h-3 w-3" />
              Online
            </Badge>
          </div>

          <div className="flex-1 space-y-5 overflow-y-auto px-5 py-6">
            {messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Gerando resposta com base nos documentos...
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="border-t p-4">
            {error && (
              <div className="mb-3 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {error}
              </div>
            )}
            <div className="flex gap-3">
              <Textarea
                ref={textareaRef}
                value={input}
                placeholder="Digite a pergunta do cliente..."
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    void handleSubmit();
                  }
                }}
                className="min-h-[56px]"
              />
              <Button type="submit" size="icon" disabled={!canSend} aria-label="Enviar mensagem">
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
              </Button>
            </div>
          </form>
        </div>

        <aside className="space-y-4">
          <Card>
            <CardContent className="space-y-3 pt-5">
              <h2 className="font-semibold">Perguntas rapidas</h2>
              <div className="grid gap-2">
                {suggestions.map((suggestion) => (
                  <Button
                    key={suggestion}
                    type="button"
                    variant="outline"
                    className="justify-start text-left"
                    onClick={() => applySuggestion(suggestion)}
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="space-y-3 pt-5">
              <h2 className="font-semibold">Fontes usadas</h2>
              {sources.length === 0 ? (
                <p className="text-sm text-muted-foreground">As fontes aparecem aqui apos uma resposta.</p>
              ) : (
                <div className="space-y-3">
                  {sources.map((source, index) => (
                    <div key={`${source.document_id}-${index}`} className="rounded-md border p-3">
                      <div className="mb-2 flex items-center gap-2 text-sm font-medium">
                        <FileText className="h-4 w-4 text-primary" />
                        {source.filename}
                      </div>
                      <p className="text-xs text-muted-foreground">Pagina {source.page_number}</p>
                      <p className="mt-2 line-clamp-4 text-sm text-muted-foreground">{source.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </aside>
      </section>
    </AppShell>
  );
}

