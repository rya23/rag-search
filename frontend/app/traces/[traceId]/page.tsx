"use client";

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api";
import { use } from "react";
import { Loader2, FileText, GitBranch, TrendingUp, Info } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { TraceOverview } from "@/components/traces/TraceOverview";
import { TraceDocuments } from "@/components/traces/TraceDocuments";
import { TraceTimeline } from "@/components/traces/TraceTimeline";
import { TracePerformance } from "@/components/traces/TracePerformance";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function TracePage({ params }: { params: Promise<{ traceId: string }> }) {
    const { traceId } = use(params);

    const {
        data: trace,
        isLoading,
        error,
    } = useQuery({
        queryKey: ["trace", traceId],
        queryFn: () => apiClient.getTrace(traceId),
    });

    return (
        <SidebarProvider>
            <AppSidebar />
            <SidebarInset>
                <div className="flex flex-col h-screen">
                    {/* Header */}
                    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 sticky top-0 z-10">
                        <SidebarTrigger className="-ml-1" />
                        <Separator orientation="vertical" className="mr-2 h-4" />
                        
                        <div className="flex flex-1 items-center justify-between">
                            <div className="flex items-center gap-3 min-w-0 flex-1">
                                <h1 className="text-lg font-semibold text-display flex items-center gap-2">
                                    <FileText className="w-5 h-5 text-chart-2 shrink-0" />
                                    Trace Details
                                </h1>
                                <Badge variant="outline" className="font-mono text-xs truncate">
                                    {traceId}
                                </Badge>
                            </div>

                            <div className="flex items-center gap-2">
                                <Link href="/traces">
                                    <Button variant="ghost" size="sm">
                                        View All Traces
                                    </Button>
                                </Link>
                                <ThemeToggle />
                            </div>
                        </div>
                    </header>

                    {/* Content */}
                    <div className="flex-1 overflow-auto">
                        <div className="container max-w-6xl mx-auto px-4 py-6">
                            {error && (
                                <Alert variant="destructive" className="mb-6 animate-in">
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
                                <Tabs defaultValue="overview" className="w-full">
                                    <TabsList className="grid w-full grid-cols-4 mb-6">
                                        <TabsTrigger value="overview" className="gap-2">
                                            <Info className="h-4 w-4" />
                                            Overview
                                        </TabsTrigger>
                                        <TabsTrigger value="documents" className="gap-2">
                                            <FileText className="h-4 w-4" />
                                            Documents
                                            {trace.docs && (
                                                <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-xs">
                                                    {trace.docs.length}
                                                </Badge>
                                            )}
                                        </TabsTrigger>
                                        <TabsTrigger value="timeline" className="gap-2">
                                            <GitBranch className="h-4 w-4" />
                                            Timeline
                                        </TabsTrigger>
                                        <TabsTrigger value="performance" className="gap-2">
                                            <TrendingUp className="h-4 w-4" />
                                            Performance
                                        </TabsTrigger>
                                    </TabsList>

                                    <TabsContent value="overview" className="mt-0">
                                        <TraceOverview trace={trace} />
                                    </TabsContent>

                                    <TabsContent value="documents" className="mt-0">
                                        <TraceDocuments trace={trace} />
                                    </TabsContent>

                                    <TabsContent value="timeline" className="mt-0">
                                        <TraceTimeline trace={trace} />
                                    </TabsContent>

                                    <TabsContent value="performance" className="mt-0">
                                        <TracePerformance trace={trace} />
                                    </TabsContent>
                                </Tabs>
                            )}
                        </div>
                    </div>
                </div>
            </SidebarInset>
        </SidebarProvider>
    );
}
