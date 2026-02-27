"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft, Clock, Database } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function TracesPage() {
  const { data: traces, isLoading, error } = useQuery({
    queryKey: ["traces"],
    queryFn: () => apiClient.getTraces(50),
    refetchInterval: 5000, // Poll every 5 seconds
  });

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-2">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <h1 className="text-3xl font-bold">Query Traces</h1>
        </div>
        <p className="text-muted-foreground">
          View all query traces with performance metrics
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>
            Failed to load traces: {error instanceof Error ? error.message : "Unknown error"}
          </AlertDescription>
        </Alert>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      )}

      {traces && traces.length === 0 && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No traces found. Start querying to see results here.</p>
          </CardContent>
        </Card>
      )}

      {traces && traces.length > 0 && (
        <div className="space-y-4">
          {traces.map((trace) => (
            <Link key={trace.trace_id} href={`/traces/${trace.trace_id}`}>
              <Card className="hover:bg-accent/50 transition-colors cursor-pointer">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg mb-2">
                        {trace.query}
                      </CardTitle>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        {new Date(trace.created_at).toLocaleString()}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          trace.status === "completed" || trace.status === "complete"
                            ? "default"
                            : trace.status === "failed" || trace.status === "error"
                            ? "destructive"
                            : "secondary"
                        }
                      >
                        {trace.status}
                      </Badge>
                      {(trace.retriever_mode || trace.mode) && (
                        <Badge variant="outline">
                          {(trace.retriever_mode || trace.mode).replace("_", " ")}
                        </Badge>
                      )}
                      {trace.total_ms && (
                        <Badge variant="outline">{trace.total_ms}ms</Badge>
                      )}
                    </div>
                  </div>
                </CardHeader>
                {trace.response && (
                  <CardContent>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {trace.response}
                    </p>
                  </CardContent>
                )}
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
