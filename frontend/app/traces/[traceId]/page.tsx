"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import Link from "next/link";
import { use } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, ArrowLeft, Clock, FileText } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function TracePage({
  params,
}: {
  params: Promise<{ traceId: string }>;
}) {
  const { traceId } = use(params);

  const { data: trace, isLoading, error } = useQuery({
    queryKey: ["trace", traceId],
    queryFn: () => apiClient.getTrace(traceId),
  });

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-2">
          <Link href="/traces">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <h1 className="text-3xl font-bold">Trace Details</h1>
        </div>
        <p className="text-muted-foreground font-mono text-sm">
          {traceId}
        </p>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertDescription>
            Failed to load trace: {error instanceof Error ? error.message : "Unknown error"}
          </AlertDescription>
        </Alert>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin" />
        </div>
      )}

      {trace && (
        <div className="space-y-6">
          {/* Query & Response */}
          <Card>
            <CardHeader>
              <CardTitle>Query & Response</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <div className="text-sm font-medium mb-2">Query</div>
                <Card className="bg-muted p-4">
                  <p>{trace.query}</p>
                </Card>
              </div>

              {trace.response && (
                <div>
                  <div className="text-sm font-medium mb-2">Response</div>
                  <Card className="bg-muted p-4">
                    <div className="prose prose-invert prose-sm max-w-none">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {trace.response}
                      </ReactMarkdown>
                    </div>
                  </Card>
                </div>
              )}

              {trace.error && (
                <div>
                  <div className="text-sm font-medium mb-2 text-destructive">
                    Error
                  </div>
                  <Alert variant="destructive">
                    <AlertDescription>{trace.error}</AlertDescription>
                  </Alert>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Metadata</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-muted-foreground mb-1">
                    Status
                  </div>
                  <Badge
                    variant={
                      trace.status === "completed"
                        ? "default"
                        : trace.status === "failed"
                        ? "destructive"
                        : "secondary"
                    }
                  >
                    {trace.status}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">
                    Mode
                  </div>
                  <Badge variant="outline">{trace.mode}</Badge>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">
                    Documents (k)
                  </div>
                  <div className="font-mono">{trace.k}</div>
                </div>
                <div>
                  <div className="text-sm text-muted-foreground mb-1">
                    Created
                  </div>
                  <div className="text-sm flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(trace.created_at).toLocaleString()}
                  </div>
                </div>
              </div>

              <Separator className="my-4" />

              <div className="grid grid-cols-3 gap-4">
                {trace.retriever_ms !== undefined && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">
                      Retrieval Time
                    </div>
                    <div className="font-mono text-lg">
                      {trace.retriever_ms}ms
                    </div>
                  </div>
                )}
                {trace.generator_ms !== undefined && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">
                      Generation Time
                    </div>
                    <div className="font-mono text-lg">
                      {trace.generator_ms}ms
                    </div>
                  </div>
                )}
                {trace.total_ms !== undefined && (
                  <div>
                    <div className="text-sm text-muted-foreground mb-1">
                      Total Time
                    </div>
                    <div className="font-mono text-lg">{trace.total_ms}ms</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Retrieved Documents */}
          {trace.docs && trace.docs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Retrieved Documents ({trace.docs.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  <div className="space-y-4">
                    {trace.docs.map((doc, index) => (
                      <Card key={index} className="bg-muted">
                        <CardHeader>
                          <div className="flex items-center justify-between">
                            <Badge variant="outline">Document {index + 1}</Badge>
                            {doc.score !== undefined && (
                              <Badge variant="secondary">
                                Score: {doc.score.toFixed(4)}
                              </Badge>
                            )}
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-sm whitespace-pre-wrap">
                            {doc.content}
                          </p>
                          {doc.metadata && (
                            <div className="mt-4 pt-4 border-t border-border">
                              <div className="text-xs text-muted-foreground">
                                Metadata
                              </div>
                              <pre className="text-xs mt-1 overflow-x-auto">
                                {JSON.stringify(doc.metadata, null, 2)}
                              </pre>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
