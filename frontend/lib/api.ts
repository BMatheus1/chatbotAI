import type { ChatResponse, ConversationDetail, ConversationSummary, DocumentItem } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...options?.headers
    }
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    throw new Error(payload?.detail ?? "Nao foi possivel concluir a operacao.");
  }

  return response.json() as Promise<T>;
}

export function sendChatMessage(message: string, conversationId?: string) {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify({ message, conversation_id: conversationId })
  });
}

export function listDocuments() {
  return request<DocumentItem[]>("/documents", { cache: "no-store" });
}

export function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  return request<{ document: DocumentItem; message: string }>("/documents/upload", {
    method: "POST",
    body: formData
  });
}

export function deleteDocument(id: string) {
  return request<{ message: string }>(`/documents/${id}`, {
    method: "DELETE"
  });
}

export function listConversations() {
  return request<ConversationSummary[]>("/conversations", { cache: "no-store" });
}

export function getConversation(id: string) {
  return request<ConversationDetail>(`/conversations/${id}`, { cache: "no-store" });
}

export function deleteConversation(id: string) {
  return request<{ message: string }>(`/conversations/${id}`, {
    method: "DELETE"
  });
}

export function deleteAllConversations() {
  return request<{ message: string; deleted_count: number }>("/conversations", {
    method: "DELETE"
  });
}
