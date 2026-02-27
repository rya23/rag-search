"use client";

import { MultiQuerySteps as MultiQueryStepsType } from "@/lib/types";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { FileSearch, Sparkles } from "lucide-react";

interface MultiQueryStepsProps {
  steps: MultiQueryStepsType;
}

export function MultiQuerySteps({ steps }: MultiQueryStepsProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5" />
          Multi-Query Retrieval Breakdown
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Prompt Sent to LLM */}
        <div>
          <div className="text-sm font-medium mb-2">Prompt Sent to LLM</div>
          <Card className="bg-muted">
            <CardContent className="pt-4">
              <pre className="text-xs whitespace-pre-wrap font-mono">
                {steps.prompt_sent}
              </pre>
            </CardContent>
          </Card>
        </div>

        <Separator />

        {/* Generated Queries */}
        <div>
          <div className="text-sm font-medium mb-3">
            Generated Queries ({steps.generated_queries.length})
          </div>
          <div className="space-y-2">
            {steps.generated_queries.map((query, index) => (
              <Card key={index} className="bg-muted/50">
                <CardContent className="pt-4 flex items-start gap-2">
                  <Badge variant="outline" className="mt-0.5">
                    {index + 1}
                  </Badge>
                  <p className="flex-1 text-sm">{query}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        <Separator />

        {/* Per-Query Documents */}
        <div>
          <div className="text-sm font-medium mb-3">
            Documents Retrieved Per Query
          </div>
          <ScrollArea className="h-[500px]">
            <div className="space-y-4">
              {steps.per_query_docs.map((queryDoc, queryIndex) => (
                <Card key={queryIndex} className="bg-muted/30">
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="secondary">
                            Query {queryDoc.query_index + 1}
                          </Badge>
                          <Badge variant="outline">
                            <FileSearch className="w-3 h-3 mr-1" />
                            {queryDoc.docs.length} docs
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">
                          {queryDoc.generated_query}
                        </p>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {queryDoc.docs.map((doc, docIndex) => (
                      <Card key={docIndex} className="bg-background">
                        <CardContent className="pt-4">
                          <div className="flex items-center justify-between mb-2">
                            <Badge variant="outline" className="text-xs">
                              Doc {doc.position + 1}
                            </Badge>
                          </div>
                          <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                            {doc.content.substring(0, 300)}
                            {doc.content.length > 300 && "..."}
                          </p>
                          {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                            <details className="mt-2">
                              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                                Metadata
                              </summary>
                              <pre className="text-xs mt-1 p-2 bg-muted rounded overflow-x-auto">
                                {JSON.stringify(doc.metadata, null, 2)}
                              </pre>
                            </details>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </CardContent>
                </Card>
              ))}
            </div>
          </ScrollArea>
        </div>
      </CardContent>
    </Card>
  );
}
