"use client";

import { useState } from "react";
import { FileText, Loader2, Trash2 } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { deleteDocument } from "@/lib/api";
import type { DocumentItem } from "@/lib/types";

export function DocumentList({
  documents,
  isLoading,
  onDeleted
}: {
  documents: DocumentItem[];
  isLoading: boolean;
  onDeleted: () => void;
}) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDelete(document: DocumentItem) {
    const confirmed = window.confirm(`Remover "${document.original_filename}" da base de conhecimento?`);
    if (!confirmed) return;

    setDeletingId(document.id);
    setError(null);

    try {
      await deleteDocument(document.id);
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Nao foi possivel remover o documento.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Documentos indexados</CardTitle>
        <CardDescription>{documents.length} documento(s) disponiveis para busca semantica.</CardDescription>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="mb-3 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </div>
        )}
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Carregando documentos...</p>
        ) : documents.length === 0 ? (
          <p className="text-sm text-muted-foreground">Nenhum PDF cadastrado ainda.</p>
        ) : (
          <div className="space-y-3">
            {documents.map((document) => (
              <div key={document.id} className="flex items-start justify-between gap-3 rounded-md border p-3">
                <div className="flex min-w-0 gap-3">
                  <FileText className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{document.original_filename}</p>
                    <p className="text-xs text-muted-foreground">{document.chunk_count} chunks gerados</p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Badge>{document.status}</Badge>
                  <Button
                    aria-label="Remover documento"
                    title="Remover documento"
                    variant="ghost"
                    size="icon"
                    disabled={deletingId === document.id}
                    onClick={() => void handleDelete(document)}
                  >
                    {deletingId === document.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4 text-destructive" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
