export type Role = "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: Role;
  content: string;
  createdAt?: string;
};

export type Source = {
  document_id: string;
  filename: string;
  page_number: number;
  content: string;
  score: number | null;
};

export type ChatResponse = {
  conversation_id: string;
  message: string;
  sources: Source[];
};

export type DocumentItem = {
  id: string;
  filename: string;
  original_filename: string;
  content_type: string;
  status: string;
  chunk_count: number;
  created_at: string;
};

export type ConversationSummary = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type ConversationDetail = {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Array<{
    id: string;
    role: Role;
    content: string;
    created_at: string;
    message_metadata?: Record<string, unknown>;
  }>;
};
