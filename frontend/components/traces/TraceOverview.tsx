"use client";

import { TraceDetail } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Clock, CheckCircle2, XCircle, Zap } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface TraceOverviewProps {
  trace: TraceDetail;
}

export function TraceOverview({ trace }: TraceOverviewProps) {
  return (
    <div className="space-y-4 animate-in">
      {/* Query & Response */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="text-base text-display">Query & Response</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="text-sm font-medium mb-2 text-muted-foreground">Query</div>
            <div className="rounded-lg bg-muted/50 border border-border p-4">
              <p className="text-sm">{trace.query}</p>
            </div>
          </div>

          {trace.response && (
            <div>
              <div className="text-sm font-medium mb-2 text-muted-foreground">Response</div>
              <div className="rounded-lg bg-muted/50 border border-border p-4">
                <div className="prose prose-sm dark:prose-invert max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{trace.response}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}

          {trace.error && (
            <Alert variant="destructive">
              <XCircle className="h-4 w-4" />
              <AlertDescription>{trace.error}</AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      {/* Metadata */}
      <Card className="card-elevated">
        <CardHeader>
          <CardTitle className="text-base text-display">Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-muted-foreground mb-2">Status</div>
              <Badge
                variant={
                  trace.status === "completed" || trace.status === "complete"
                    ? "default"
                    : trace.status === "failed" || trace.status === "error"
                    ? "destructive"
                    : "secondary"
                }
                className="gap-1"
              >
                {(trace.status === "completed" || trace.status === "complete") && (
                  <CheckCircle2 className="w-3 h-3" />
                )}
                {(trace.status === "failed" || trace.status === "error") && (
                  <XCircle className="w-3 h-3" />
                )}
                {trace.status}
              </Badge>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-2">Retrieval Mode</div>
              <Badge variant="outline" className="font-medium">
                {trace.mode === "multi_query_retrieve" ? "Multi-Query" : "Simple"}
              </Badge>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-2">Documents (k)</div>
              <div className="font-mono text-lg font-semibold">{trace.k}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground mb-2">Created</div>
              <div className="text-sm flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {new Date(trace.created_at).toLocaleTimeString()}
              </div>
            </div>
          </div>

          <Separator className="my-4" />

          <div className="grid grid-cols-3 gap-4">
            {trace.retriever_ms !== undefined && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">Retrieval Time</div>
                <div className="flex items-baseline gap-1">
                  <span className="font-mono text-xl font-semibold">{trace.retriever_ms}</span>
                  <span className="text-sm text-muted-foreground">ms</span>
                </div>
              </div>
            )}
            {trace.generator_ms !== undefined && (
              <div>
                <div className="text-xs text-muted-foreground mb-2">Generation Time</div>
                <div className="flex items-baseline gap-1">
                  <span className="font-mono text-xl font-semibold">{trace.generator_ms}</span>
                  <span className="text-sm text-muted-foreground">ms</span>
                </div>
              </div>
            )}
            {trace.total_ms !== undefined && (
              <div>
                <div className="text-xs text-muted-foreground mb-2 flex items-center gap-1">
                  <Zap className="w-3 h-3" />
                  Total Time
                </div>
                <div className="flex items-baseline gap-1">
                  <span className="font-mono text-xl font-semibold text-chart-1">{trace.total_ms}</span>
                  <span className="text-sm text-muted-foreground">ms</span>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
