// API Request/Response Types
export interface QueryRequest {
  query: string;
  k?: number;
  thread_id?: string | null;
}

// SSE Event Types
export type SSEEvent =
  | { type: "trace_id"; data: string }
  | { type: "thread_id"; data: string }
  | { type: "node"; data: string }
  | { type: "token"; data: string }
  | { type: "error"; data: string }
  | { type: "done" };

// Chat Message Types
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

// Trace Types
export interface Trace {
  trace_id: string;
  query: string;
  mode: string;
  k: number;
  created_at: string;
  response?: string;
  error?: string;
  retriever_ms?: number;
  generator_ms?: number;
  total_ms?: number;
  status: "pending" | "completed" | "failed";
}

export interface TraceDetail extends Trace {
  docs?: RetrievedDocument[];
}

export interface RetrievedDocument {
  content: string;
  metadata?: Record<string, any>;
  score?: number;
}

// Node execution progress
export type NodeName =
  | "analyze_query"
  | "simple_retrieve"
  | "multi_query_retrieve"
  | "generate_answer";

export interface NodeProgress {
  node: NodeName;
  timestamp: Date;
}
