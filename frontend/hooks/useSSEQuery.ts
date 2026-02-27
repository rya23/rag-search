"use client";

import { useState, useCallback, useRef } from "react";
import { streamQuery } from "@/lib/sse";
import type { QueryRequest, Message, NodeProgress, NodeName } from "@/lib/types";

interface UseSSEQueryState {
  messages: Message[];
  isStreaming: boolean;
  error: string | null;
  traceId: string | null;
  threadId: string | null;
  nodeProgress: NodeProgress[];
  retrievalMethod: string | null;
}

interface UseSSEQueryReturn extends UseSSEQueryState {
  sendQuery: (query: string, k?: number) => Promise<void>;
  reset: () => void;
}

export function useSSEQuery(): UseSSEQueryReturn {
  const [state, setState] = useState<UseSSEQueryState>({
    messages: [],
    isStreaming: false,
    error: null,
    traceId: null,
    threadId: null,
    nodeProgress: [],
    retrievalMethod: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const currentMessageRef = useRef<string>("");

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setState({
      messages: [],
      isStreaming: false,
      error: null,
      traceId: null,
      threadId: null,
      nodeProgress: [],
      retrievalMethod: null,
    });
    currentMessageRef.current = "";
  }, []);

  const sendQuery = useCallback(
    async (query: string, k: number = 5) => {
      // Cancel any ongoing request
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      abortControllerRef.current = new AbortController();

      // Add user message
      const userMessage: Message = {
        id: `user-${Date.now()}`,
        role: "user",
        content: query,
        timestamp: new Date(),
      };

      setState((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
        isStreaming: true,
        error: null,
        nodeProgress: [],
        retrievalMethod: null,
      }));

      currentMessageRef.current = "";

      try {
        const request: QueryRequest = {
          query,
          k,
          thread_id: state.threadId,
        };

        for await (const event of streamQuery(request)) {
          // Check if aborted
          if (abortControllerRef.current?.signal.aborted) {
            break;
          }

          switch (event.type) {
            case "trace_id":
              setState((prev) => ({ ...prev, traceId: event.data }));
              break;

            case "thread_id":
              setState((prev) => ({ ...prev, threadId: event.data }));
              break;

            case "node":
              setState((prev) => ({
                ...prev,
                nodeProgress: [
                  ...prev.nodeProgress,
                  {
                    node: event.data as NodeName,
                    timestamp: new Date(),
                  },
                ],
              }));
              break;

            case "retrieval_method":
              setState((prev) => ({ ...prev, retrievalMethod: event.data }));
              break;

            case "token":
              currentMessageRef.current += event.data;
              setState((prev) => ({
                ...prev,
                messages: [
                  ...prev.messages.filter((m) => m.role !== "assistant" || m.content !== ""),
                  {
                    id: `assistant-${prev.traceId || Date.now()}`,
                    role: "assistant",
                    content: currentMessageRef.current,
                    timestamp: new Date(),
                  },
                ],
              }));
              break;

            case "error":
              setState((prev) => ({
                ...prev,
                error: event.data,
                isStreaming: false,
              }));
              break;

            case "done":
              setState((prev) => ({ ...prev, isStreaming: false }));
              currentMessageRef.current = "";
              break;
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          setState((prev) => ({
            ...prev,
            error: error.message,
            isStreaming: false,
          }));
        }
      }
    },
    [state.threadId]
  );

  return {
    ...state,
    sendQuery,
    reset,
  };
}
