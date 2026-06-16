"use client";

import { useState } from "react";
import { Loader2, MessageSquareText, Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteAllConversations, getConversation } from "@/lib/api";
import type { ConversationDetail, ConversationSummary } from "@/lib/types";

export function ConversationList({
  conversations,
  isLoading,
  onCleared
}: {
  conversations: ConversationSummary[];
  isLoading: boolean;
  onCleared?: () => void;
}) {
  const [selected, setSelected] = useState<ConversationDetail | null>(null);
  const [isClearing, setIsClearing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openConversation(id: string) {
    const response = await getConversation(id);
    setSelected(response);
  }

  async function clearConversations() {
    if (conversations.length === 0) return;

    const confirmed = window.confirm("Remover todo o historico de conversas?");
    if (!confirmed) return;

    setIsClearing(true);
    setError(null);

    try {
      await deleteAllConversations();
      setSelected(null);
      onCleared?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nao foi possivel limpar as conversas.");
    } finally {
      setIsClearing(false);
    }
  }

  return (
    <Card>
      <CardHeader className="flex-row items-start justify-between gap-4">
        <div className="space-y-1.5">
          <CardTitle>Conversas</CardTitle>
          <CardDescription>Historico salvo com mensagens, contexto e timestamps.</CardDescription>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={isLoading || isClearing || conversations.length === 0}
          onClick={() => void clearConversations()}
        >
          {isClearing ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
          Limpar
        </Button>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-[320px_1fr]">
        {error && (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive lg:col-span-2">
            {error}
          </div>
        )}
        <div className="space-y-2">
          {isLoading ? (
            <p className="text-sm text-muted-foreground">Carregando conversas...</p>
          ) : conversations.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhuma conversa registrada.</p>
          ) : (
            conversations.map((conversation) => (
              <Button
                key={conversation.id}
                variant="outline"
                className="h-auto w-full justify-start p-3 text-left"
                onClick={() => void openConversation(conversation.id)}
              >
                <MessageSquareText className="h-4 w-4 shrink-0" />
                <span className="min-w-0">
                  <span className="block truncate font-medium">{conversation.title}</span>
                  <span className="block text-xs text-muted-foreground">
                    {conversation.message_count} mensagens
                  </span>
                </span>
              </Button>
            ))
          )}
        </div>

        <div className="min-h-[280px] rounded-md border p-4">
          {!selected ? (
            <p className="text-sm text-muted-foreground">Selecione uma conversa para visualizar o conteudo.</p>
          ) : (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold">{selected.title}</h3>
                <p className="text-xs text-muted-foreground">
                  Atualizada em {new Date(selected.updated_at).toLocaleString("pt-BR")}
                </p>
              </div>
              <div className="space-y-3">
                {selected.messages.map((message) => (
                  <div key={message.id} className="rounded-md bg-secondary p-3">
                    <p className="mb-1 text-xs font-medium uppercase text-muted-foreground">{message.role}</p>
                    <p className="whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
