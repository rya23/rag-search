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
    | { type: "retrieval_method"; data: string }
    | { type: "retrieval_quality"; data: string }
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
    retriever_mode?: string; // Actual retrieval method used
    k: number;
    created_at: string;
    response?: string;
    error?: string;
    retriever_ms?: number;
    generator_ms?: number;
    total_ms?: number;
    status: "pending" | "completed" | "failed" | "in_progress" | "complete" | "error";
}

export interface MultiQueryDoc {
    position: number;
    content: string;
    metadata: Record<string, any>;
}

export interface PerQueryDocs {
    query_index: number;
    generated_query: string;
    docs: MultiQueryDoc[];
}

export interface MultiQuerySteps {
    prompt_sent: string;
    generated_queries: string[];
    per_query_docs: PerQueryDocs[];
}

export interface TraceDetail extends Trace {
    docs?: RetrievedDocument[];
    multiquery_steps?: MultiQuerySteps;
}

export interface RetrievedDocument {
    content: string;
    metadata?: Record<string, any>;
    score?: number;
}

// Node execution progress
export type NodeName = "low_dim_retrieve" | "rerank" | "evaluate_retrieval" | "high_dim_multi_query_retrieve" | "rerank_final" | "generate_answer";

export interface NodeProgress {
    node: NodeName;
    timestamp: Date;
}
