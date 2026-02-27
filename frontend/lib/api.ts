import { API_BASE_URL } from "./config";
import type { Trace, TraceDetail, RetrievedDocument } from "./types";

export class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  /**
   * Fetch list of traces
   */
  async getTraces(limit: number = 50): Promise<Trace[]> {
    const response = await fetch(
      `${this.baseURL}/api/traces?limit=${limit}`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch traces: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Fetch a single trace with details
   */
  async getTrace(traceId: string): Promise<TraceDetail> {
    const response = await fetch(`${this.baseURL}/api/traces/${traceId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch trace: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Fetch documents for a trace
   */
  async getTraceDocs(traceId: string): Promise<RetrievedDocument[]> {
    const response = await fetch(
      `${this.baseURL}/api/traces/${traceId}/docs`
    );
    if (!response.ok) {
      throw new Error(`Failed to fetch docs: ${response.statusText}`);
    }
    return response.json();
  }
}

// Singleton instance
export const apiClient = new APIClient();
