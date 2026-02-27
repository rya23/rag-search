import { API_BASE_URL } from "./config";
import type { QueryRequest, SSEEvent } from "./types";

/**
 * Parse SSE data line into an event object
 */
export function parseSSEEvent(line: string): SSEEvent | null {
  if (!line.startsWith("data: ")) return null;

  try {
    const jsonStr = line.slice(6); // Remove "data: " prefix
    return JSON.parse(jsonStr) as SSEEvent;
  } catch (error) {
    console.error("Failed to parse SSE event:", line, error);
    return null;
  }
}

/**
 * Create an SSE connection for streaming query responses
 */
export async function* streamQuery(
  request: QueryRequest
): AsyncGenerator<SSEEvent, void, unknown> {
  const response = await fetch(`${API_BASE_URL}/api/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: request.query,
      k: request.k || 5,
      thread_id: request.thread_id,
    }),
  });

  if (!response.ok) {
    throw new Error(`Query failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  if (!reader) {
    throw new Error("Response body is not readable");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Decode chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Split by double newline (SSE delimiter)
      const lines = buffer.split("\n\n");

      // Keep the last incomplete line in buffer
      buffer = lines.pop() || "";

      // Process complete events
      for (const line of lines) {
        if (line.trim()) {
          const event = parseSSEEvent(line);
          if (event) {
            yield event;
          }
        }
      }
    }

    // Process any remaining data in buffer
    if (buffer.trim()) {
      const event = parseSSEEvent(buffer);
      if (event) {
        yield event;
      }
    }
  } finally {
    reader.releaseLock();
  }
}
