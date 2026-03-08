"use client";

import { useState, useRef, useEffect } from "react";
import { useSSEQuery } from "@/hooks/useSSEQuery";
import { Message } from "./Message";
import { NodeProgress } from "./NodeProgress";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Send, Loader2, AlertCircle, Sparkles, Settings2, RotateCcw } from "lucide-react";
import { DEFAULT_K } from "@/lib/config";
import Link from "next/link";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function ChatInterface() {
    const [query, setQuery] = useState("");
    const [k, setK] = useState(DEFAULT_K);
    const scrollRef = useRef<HTMLDivElement>(null);

    const { messages, isStreaming, error, traceId, threadId, nodeProgress, retrievalMethod, retrievalQuality, sendQuery, reset } = useSSEQuery();

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [messages, nodeProgress]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim() || isStreaming) return;

        await sendQuery(query, k);
        setQuery("");
    };

    return (
        <div className="flex flex-col h-screen">
            {/* Header */}
            <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 sticky top-0 z-10">
                <SidebarTrigger className="-ml-1" />
                <Separator orientation="vertical" className="mr-2 h-4" />

                <div className="flex flex-1 items-center justify-between">
                    <div className="flex items-center gap-3">
                        <h1 className="text-lg font-semibold text-display flex items-center gap-2">
                            <Sparkles className="w-5 h-5 text-chart-1" />
                            RAG Search
                        </h1>

                        <div className="flex items-center gap-2">
                            {retrievalMethod && (
                                <Badge variant="secondary" className="text-xs font-medium">
                                    {retrievalMethod === "low_dim"
                                        ? "128d · Fast Path"
                                        : retrievalMethod === "high_dim_multi"
                                          ? "768d · Full Retrieval"
                                          : retrievalMethod}
                                </Badge>
                            )}
                            {retrievalQuality === "strong" && (
                                <Badge className="text-xs font-medium bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30">
                                    Strong
                                </Badge>
                            )}
                            {retrievalQuality === "weak" && (
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Badge className="text-xs font-medium bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30 cursor-default">
                                            Upgraded
                                        </Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>128d retrieval scored below threshold — escalated to 768d + multi-query</p>
                                    </TooltipContent>
                                </Tooltip>
                            )}
                            {threadId && (
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Badge variant="outline" className="font-mono text-xs">
                                            {threadId.slice(0, 8)}
                                        </Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>Thread ID: {threadId}</p>
                                    </TooltipContent>
                                </Tooltip>
                            )}
                            {traceId && (
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <Badge variant="outline" className="font-mono text-xs">
                                            <Link href={`/traces/${traceId}`} className="hover:underline">
                                                Trace: {traceId.slice(0, 8)}
                                            </Link>
                                        </Badge>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        <p>Click to view trace details</p>
                                    </TooltipContent>
                                </Tooltip>
                            )}
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {messages.length > 0 && (
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button variant="ghost" size="icon" onClick={reset} disabled={isStreaming} className="h-9 w-9">
                                        <RotateCcw className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>
                                    <p>Clear conversation</p>
                                </TooltipContent>
                            </Tooltip>
                        )}

                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <Button variant="outline" size="icon" className="h-9 w-9">
                                    <Settings2 className="h-4 w-4" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-56">
                                <DropdownMenuLabel>Query Settings</DropdownMenuLabel>
                                <DropdownMenuSeparator />
                                <div className="p-2">
                                    <Label htmlFor="k-setting" className="text-xs text-muted-foreground">
                                        Documents to Retrieve (k)
                                    </Label>
                                    <div className="flex items-center gap-2 mt-2">
                                        <Input
                                            id="k-setting"
                                            type="number"
                                            min="1"
                                            max="20"
                                            value={k}
                                            onChange={(e) => setK(parseInt(e.target.value) || DEFAULT_K)}
                                            className="h-8"
                                            disabled={isStreaming}
                                        />
                                        <span className="text-sm text-muted-foreground">k = {k}</span>
                                    </div>
                                </div>
                            </DropdownMenuContent>
                        </DropdownMenu>

                        <ThemeToggle />
                    </div>
                </div>
            </header>

            {/* Messages Area */}
            <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full" ref={scrollRef}>
                    <div className="container max-w-4xl mx-auto px-4 py-6">
                        {messages.length === 0 && !isStreaming && (
                            <div className="flex items-center justify-center h-[calc(100vh-16rem)]">
                                <div className="text-center space-y-4">
                                    <div className="inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-muted">
                                        <Sparkles className="h-8 w-8 text-muted-foreground" />
                                    </div>
                                    <div className="space-y-2">
                                        <h2 className="text-xl font-semibold text-display">Start a Conversation</h2>
                                        <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                                            Ask questions about your documents and get intelligent answers powered by advanced retrieval.
                                        </p>
                                    </div>
                                    <div className="flex flex-wrap gap-2 justify-center pt-4">
                                        <Badge variant="outline" className="text-xs">
                                            Adaptive Retrieval
                                        </Badge>
                                        <Badge variant="outline" className="text-xs">
                                            Semantic Search
                                        </Badge>
                                        <Badge variant="outline" className="text-xs">
                                            Real-time Streaming
                                        </Badge>
                                    </div>
                                </div>
                            </div>
                        )}

                        {messages.map((message) => (
                            <Message key={message.id} message={message} />
                        ))}

                        {/* Node Progress */}
                        {isStreaming && <NodeProgress progress={nodeProgress} isStreaming={isStreaming} />}

                        {/* Error Display */}
                        {error && (
                            <Alert variant="destructive" className="mb-4 animate-in">
                                <AlertCircle className="h-4 w-4" />
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        )}
                    </div>
                </ScrollArea>
            </div>

            {/* Input Area */}
            <div className="shrink-0 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
                <div className="container max-w-4xl mx-auto px-4 py-4">
                    <form onSubmit={handleSubmit} className="flex items-end gap-2">
                        <div className="flex-1">
                            <Input
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                placeholder="Ask a question about your documents..."
                                disabled={isStreaming}
                                className="resize-none h-11 text-sm"
                            />
                        </div>
                        <Button type="submit" disabled={!query.trim() || isStreaming} size="icon" className="h-11 w-11 shrink-0">
                            {isStreaming ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                        </Button>
                    </form>
                    <p className="text-xs text-muted-foreground mt-2 text-center">Powered by LangGraph • FastAPI • Next.js</p>
                </div>
            </div>
        </div>
    );
}
