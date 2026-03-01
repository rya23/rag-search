"use client";

import { TraceDetail } from "@/lib/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { FileText, ChevronDown, ChevronRight, GitBranch } from "lucide-react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { useState, useMemo } from "react";
import { Separator } from "@/components/ui/separator";

interface TraceDocumentsProps {
    trace: TraceDetail;
}

interface QueryInfo {
    queryIndex: number;
    query: string;
}

function getDocumentSignature(doc: { content?: string; metadata?: Record<string, any> }) {
    const normalizedContent = (doc.content || "").trim();
    const normalizedMetadata = JSON.stringify(doc.metadata || {});
    return `${normalizedContent}::${normalizedMetadata}`;
}

// Helper to map documents to their source queries for multi-query retrieval
function mapDocsToQueries(trace: TraceDetail) {
    if (!trace.multiquery_steps || !trace.docs) return null;

    const docToQueryMap = new Map<string, QueryInfo[]>();

    // Build a map of document signatures to all source queries
    trace.multiquery_steps.per_query_docs.forEach((queryDocs) => {
        queryDocs.docs.forEach((doc) => {
            const key = getDocumentSignature(doc);
            const existing = docToQueryMap.get(key) || [];
            if (existing.some((item) => item.queryIndex === queryDocs.query_index)) {
                return;
            }

            existing.push({
                queryIndex: queryDocs.query_index,
                query: queryDocs.generated_query,
            });
            docToQueryMap.set(key, existing);
        });
    });

    return docToQueryMap;
}

export function TraceDocuments({ trace }: TraceDocumentsProps) {
    const docToQueryMap = useMemo(() => mapDocsToQueries(trace), [trace]);
    const isMultiQuery = !!trace.multiquery_steps;

    if (!trace.docs || trace.docs.length === 0) {
        return (
            <Card className="card-elevated">
                <CardContent className="py-12 text-center">
                    <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-4">
                        <FileText className="w-8 h-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-semibold text-display mb-2">No Documents</h3>
                    <p className="text-sm text-muted-foreground">No documents were retrieved for this query.</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-3 animate-in">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-chart-3" />
                    <h3 className="text-base font-semibold text-display">Retrieved Documents</h3>
                    <Badge variant="secondary" className="text-xs">
                        {trace.docs.length} {trace.docs.length === 1 ? "document" : "documents"}
                    </Badge>
                    {isMultiQuery && (
                        <Badge variant="outline" className="text-xs gap-1">
                            <GitBranch className="w-3 h-3" />
                            Multi-Query
                        </Badge>
                    )}
                </div>
            </div>

            <ScrollArea className="h-[calc(100vh-20rem)]">
                <div className="space-y-3 pr-4">
                    {trace.docs.map((doc, index) => (
                        <DocumentCard key={index} doc={doc} index={index} queryInfos={docToQueryMap?.get(getDocumentSignature(doc))} />
                    ))}
                </div>
            </ScrollArea>
        </div>
    );
}

function DocumentCard({ doc, index, queryInfos }: { doc: any; index: number; queryInfos?: QueryInfo[] }) {
    const [isOpen, setIsOpen] = useState(index === 0); // First document open by default
    const hasQueryInfo = !!queryInfos && queryInfos.length > 0;

    return (
        <Collapsible open={isOpen} onOpenChange={setIsOpen}>
            <Card className="card-elevated hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                    <CollapsibleTrigger asChild>
                        <Button variant="ghost" className="w-full justify-between p-0 h-auto hover:bg-transparent">
                            <div className="flex items-center gap-2 flex-wrap">
                                <Badge variant="outline" className="shrink-0">
                                    Doc {index + 1}
                                </Badge>
                                {doc.score !== undefined && (
                                    <Badge variant="secondary" className="font-mono text-xs">
                                        Score: {doc.score.toFixed(4)}
                                    </Badge>
                                )}
                                {hasQueryInfo && (
                                    <Badge variant="default" className="text-xs font-medium">
                                        From {queryInfos.map((info) => `Q${info.queryIndex + 1}`).join(", ")}
                                    </Badge>
                                )}
                            </div>
                            {isOpen ? (
                                <ChevronDown className="h-4 w-4 text-muted-foreground shrink-0" />
                            ) : (
                                <ChevronRight className="h-4 w-4 text-muted-foreground shrink-0" />
                            )}
                        </Button>
                    </CollapsibleTrigger>
                </CardHeader>

                <CollapsibleContent>
                    <CardContent className="space-y-4">
                        {hasQueryInfo && (
                            <>
                                {queryInfos.map((queryInfo) => (
                                    <div key={`${queryInfo.queryIndex}-${queryInfo.query}`}>
                                        <div className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-2">
                                            <GitBranch className="w-3 h-3" />
                                            Retrieved by Query {queryInfo.queryIndex + 1}
                                        </div>
                                        <div className="rounded-lg border p-3 bg-accent">
                                            <p className="text-xs font-medium">{queryInfo.query}</p>
                                        </div>
                                    </div>
                                ))}
                                <Separator />
                            </>
                        )}

                        <div>
                            <div className="text-xs font-medium text-muted-foreground mb-2">Content</div>
                            <div className="rounded-lg bg-muted/50 border border-border p-3">
                                <p className="text-sm whitespace-pre-wrap leading-relaxed">{doc.content}</p>
                            </div>
                        </div>

                        {doc.metadata && Object.keys(doc.metadata).length > 0 && (
                            <div>
                                <div className="text-xs font-medium text-muted-foreground mb-2">Metadata</div>
                                <div className="rounded-lg bg-muted/50 border border-border p-3">
                                    <pre className="text-xs overflow-x-auto">{JSON.stringify(doc.metadata, null, 2)}</pre>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </CollapsibleContent>
            </Card>
        </Collapsible>
    );
}
