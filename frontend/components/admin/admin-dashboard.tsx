"use client";

import { useEffect, useState } from "react";
import type { ComponentType } from "react";
import { Database, FileText, MessagesSquare } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { ConversationList } from "@/components/admin/conversation-list";
import { DocumentList } from "@/components/admin/document-list";
import { DocumentUploader } from "@/components/admin/document-uploader";
import { Card, CardContent } from "@/components/ui/card";
import { listConversations, listDocuments } from "@/lib/api";
import type { ConversationSummary, DocumentItem } from "@/lib/types";

export function AdminDashboard() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refreshData() {
    setIsLoading(true);
    setError(null);
    try {
      const [documentData, conversationData] = await Promise.all([
        listDocuments(),
        listConversations()
      ]);
      setDocuments(documentData);
      setConversations(conversationData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nao foi possivel carregar o painel.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void refreshData();
  }, []);

  return (
    <AppShell>
      <section className="mx-auto max-w-7xl px-4 py-8 sm:px-6">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold tracking-normal">Painel administrativo</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Gerencie conhecimento, documentos e historico de atendimento.
          </p>
        </div>

        {error && (
          <div className="mb-5 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <div className="mb-6 grid gap-4 md:grid-cols-3">
          <MetricCard icon={FileText} label="Documentos" value={documents.length.toString()} />
          <MetricCard icon={Database} label="Chunks vetoriais" value={documents.reduce((sum, item) => sum + item.chunk_count, 0).toString()} />
          <MetricCard icon={MessagesSquare} label="Conversas" value={conversations.length.toString()} />
        </div>

        <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
          <div className="space-y-6">
            <DocumentUploader onUploaded={() => void refreshData()} />
            <DocumentList documents={documents} isLoading={isLoading} />
          </div>
          <ConversationList conversations={conversations} isLoading={isLoading} />
        </div>
      </section>
    </AppShell>
  );
}

function MetricCard({
  icon: Icon,
  label,
  value
}: {
  icon: ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <Card>
      <CardContent className="flex items-center justify-between pt-5">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-1 text-2xl font-semibold">{value}</p>
        </div>
        <span className="flex h-10 w-10 items-center justify-center rounded-md bg-secondary">
          <Icon className="h-5 w-5 text-primary" />
        </span>
      </CardContent>
    </Card>
  );
}
