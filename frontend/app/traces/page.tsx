"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import Link from "next/link";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Loader2, Clock, Database, Sparkles } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export default function TracesPage() {
    const {
        data: traces,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["traces"],
        queryFn: () => apiClient.getTraces(50),
        refetchInterval: 5000, // Poll every 5 seconds
    });

    return (
        <SidebarProvider>
            <AppSidebar />
            <SidebarInset>
                <div className="flex flex-col h-screen">
                    {/* Header */}
                    <header className="flex h-16 shrink-0 items-center gap-2 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-6 sticky top-0 z-10">
                        <SidebarTrigger className="-ml-1" />
                        <Separator orientation="vertical" className="mr-3 h-4" />

                        <div className="flex flex-1 items-center justify-between">
                            <div className="flex items-center gap-4">
                                <h1 className="text-xl font-semibold text-display flex items-center gap-3">
                                    <Database className="w-5 h-5 text-chart-2" />
                                    Query Traces
                                </h1>
                                <span className="text-sm text-muted-foreground hidden sm:inline">Performance & retrieval insights</span>
                            </div>

                            <ThemeToggle />
                        </div>
                    </header>

                    {/* Content */}
                    <div className="flex-1 overflow-auto bg-background">
                        <div className="container max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                            {error && (
                                <Alert variant="destructive" className="mb-8 animate-in">
                                    <AlertDescription>
                                        Failed to load traces: {error instanceof Error ? error.message : "Unknown error"}
                                    </AlertDescription>
                                </Alert>
                            )}

                            {isLoading && (
                                <div className="flex items-center justify-center py-16">
                                    <div className="flex flex-col items-center gap-3">
                                        <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
                                        <p className="text-sm text-muted-foreground">Loading traces...</p>
                                    </div>
                                </div>
                            )}

                            {traces && traces.length === 0 && (
                                <Card className="card-elevated">
                                    <CardContent className="py-16 text-center">
                                        <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted mb-6">
                                            <Database className="w-8 h-8 text-muted-foreground" />
                                        </div>
                                        <h3 className="text-lg font-semibold text-display mb-2">No Traces Yet</h3>
                                        <p className="text-sm text-muted-foreground max-w-xs mx-auto">
                                            Start querying to see performance traces here.
                                        </p>
                                    </CardContent>
                                </Card>
                            )}

                            {traces && traces.length > 0 && (
                                <div className="space-y-4">
                                    {traces.map((trace) => (
                                        <Link key={trace.trace_id} href={`/traces/${trace.trace_id}`}>
                                            <Card className="mb-4 hover:bg-accent/50 transition-all duration-200 cursor-pointer card-elevated hover:shadow-lg animate-in">
                                                {" "}
                                                <CardHeader className="pb-4">
                                                    <div className="flex items-start justify-between gap-6">
                                                        <div className="flex-1 min-w-0">
                                                            <CardTitle className="text-base mb-3 line-clamp-2">{trace.query}</CardTitle>
                                                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                                                <Clock className="w-3.5 h-3.5 flex-shrink-0" />
                                                                {new Date(trace.created_at).toLocaleString()}
                                                            </div>
                                                        </div>
                                                        <div className="flex flex-col items-end gap-3 shrink-0">
                                                            <div className="flex items-center gap-2 flex-wrap justify-end">
                                                                <Badge
                                                                    variant={
                                                                        trace.status === "completed" || trace.status === "complete"
                                                                            ? "default"
                                                                            : trace.status === "failed" || trace.status === "error"
                                                                              ? "destructive"
                                                                              : "secondary"
                                                                    }
                                                                    className="text-xs"
                                                                >
                                                                    {trace.status}
                                                                </Badge>
                                                                {(trace.retriever_mode || trace.mode) && (
                                                                    <Badge variant="outline" className="text-xs">
                                                                        {(trace.retriever_mode || trace.mode).replace("_", " ")}
                                                                    </Badge>
                                                                )}
                                                            </div>
                                                            {trace.total_ms && (
                                                                <Badge variant="secondary" className="text-xs font-mono">
                                                                    {trace.total_ms}ms
                                                                </Badge>
                                                            )}
                                                        </div>
                                                    </div>
                                                </CardHeader>
                                                {trace.response && (
                                                    <CardContent className="pt-0">
                                                        <p className="text-sm text-muted-foreground line-clamp-2">{trace.response}</p>
                                                    </CardContent>
                                                )}
                                            </Card>
                                        </Link>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}
