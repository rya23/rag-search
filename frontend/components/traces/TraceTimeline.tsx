"use client";

import { TraceDetail } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { GitBranch, ArrowRight, FileSearch, Sparkles } from "lucide-react";
import { MultiQuerySteps } from "./MultiQuerySteps";

interface TraceTimelineProps {
  trace: TraceDetail;
}

export function TraceTimeline({ trace }: TraceTimelineProps) {
  if (!trace.multiquery_steps) {
    return (
      <Card className="card-elevated">
        <CardContent className="py-12 text-center">
          <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-4">
            <GitBranch className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-semibold text-display mb-2">Simple Retrieval</h3>
          <p className="text-sm text-muted-foreground max-w-sm mx-auto">
            This query used simple retrieval. Multi-query timeline is only available for multi-query retrieval mode.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4 animate-in">
      <div className="flex items-center gap-2 mb-4">
        <GitBranch className="w-5 h-5 text-chart-4" />
        <h3 className="text-base font-semibold text-display">Multi-Query Execution Timeline</h3>
        <Badge variant="secondary" className="text-xs">
          {trace.multiquery_steps.generated_queries.length} queries generated
        </Badge>
      </div>

      <ScrollArea className="h-[calc(100vh-20rem)]">
        <div className="space-y-6 pr-4">
          {/* Step 1: Query Analysis */}
          <Card className="card-elevated">
            <CardHeader>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-chart-1/20 text-chart-1">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <CardTitle className="text-sm">Step 1: Query Analysis</CardTitle>
                  <p className="text-xs text-muted-foreground">LLM analyzes the original query</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="rounded-lg bg-muted/50 border border-border p-3">
                <div className="text-xs font-medium text-muted-foreground mb-2">Prompt Sent to LLM</div>
                <p className="text-sm whitespace-pre-wrap font-mono text-muted-foreground leading-relaxed">
                  {trace.multiquery_steps.prompt_sent}
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-muted-foreground" />
          </div>

          {/* Step 2: Query Generation */}
          <Card className="card-elevated">
            <CardHeader>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-chart-2/20 text-chart-2">
                  <GitBranch className="h-4 w-4" />
                </div>
                <div>
                  <CardTitle className="text-sm">Step 2: Query Generation</CardTitle>
                  <p className="text-xs text-muted-foreground">Multiple search queries created</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {trace.multiquery_steps.generated_queries.map((query, index) => (
                  <div key={index} className="rounded-lg bg-muted/50 border border-border p-3">
                    <div className="flex items-start gap-2">
                      <Badge variant="outline" className="shrink-0 mt-0.5">
                        Q{index + 1}
                      </Badge>
                      <p className="text-sm flex-1">{query}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-center">
            <ArrowRight className="h-6 w-6 text-muted-foreground" />
          </div>

          {/* Step 3: Document Retrieval */}
          <Card className="card-elevated">
            <CardHeader>
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-chart-3/20 text-chart-3">
                  <FileSearch className="h-4 w-4" />
                </div>
                <div>
                  <CardTitle className="text-sm">Step 3: Document Retrieval</CardTitle>
                  <p className="text-xs text-muted-foreground">Documents retrieved for each query</p>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {trace.multiquery_steps.per_query_docs.map((queryDocs, index) => {
                  // Alternate between default and secondary badge variants
                  const badgeVariant = index % 2 === 0 ? "default" : "secondary";

                  return (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Badge variant={badgeVariant}>
                          Query {index + 1}
                        </Badge>
                        <Badge variant="outline" className="text-xs">
                          {queryDocs.docs.length} docs
                        </Badge>
                      </div>
                      <div className="rounded-lg border p-3 bg-accent">
                        <p className="text-xs font-medium mb-3">{queryDocs.generated_query}</p>
                        <div className="space-y-1.5">
                          {queryDocs.docs.slice(0, 3).map((doc, docIndex) => (
                            <div key={docIndex} className="flex items-start gap-2 text-xs">
                              <Badge variant="outline" className="shrink-0 mt-0.5">
                                Doc {doc.position + 1}
                              </Badge>
                              <span className="text-muted-foreground truncate flex-1">
                                {doc.content.substring(0, 100)}...
                              </span>
                            </div>
                          ))}
                          {queryDocs.docs.length > 3 && (
                            <div className="text-xs text-muted-foreground pl-2">
                              + {queryDocs.docs.length - 3} more documents
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
