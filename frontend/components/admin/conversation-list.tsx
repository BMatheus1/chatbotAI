"use client";

import { useState } from "react";
import { MessageSquareText } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getConversation } from "@/lib/api";
import type { ConversationDetail, ConversationSummary } from "@/lib/types";

export function ConversationList({
  conversations,
  isLoading
}: {
  conversations: ConversationSummary[];
  isLoading: boolean;
}) {
  const [selected, setSelected] = useState<ConversationDetail | null>(null);

  async function openConversation(id: string) {
    const response = await getConversation(id);
    setSelected(response);
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Conversas</CardTitle>
        <CardDescription>Historico salvo com mensagens, contexto e timestamps.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 lg:grid-cols-[320px_1fr]">
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

