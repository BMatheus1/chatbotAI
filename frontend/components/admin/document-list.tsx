import { FileText } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { DocumentItem } from "@/lib/types";

export function DocumentList({ documents, isLoading }: { documents: DocumentItem[]; isLoading: boolean }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Documentos indexados</CardTitle>
        <CardDescription>{documents.length} documento(s) disponiveis para busca semantica.</CardDescription>
      </CardHeader>
      <CardContent>
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
                <Badge>{document.status}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

