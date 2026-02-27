"use client";

import { useState, useRef, useEffect } from "react";
import { useSSEQuery } from "@/hooks/useSSEQuery";
import { Message } from "./Message";
import { NodeProgress } from "./NodeProgress";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Send, Loader2, AlertCircle, Sparkles, History } from "lucide-react";
import { DEFAULT_K } from "@/lib/config";
import Link from "next/link";

export function ChatInterface() {
  const [query, setQuery] = useState("");
  const [k, setK] = useState(DEFAULT_K);
  const scrollRef = useRef<HTMLDivElement>(null);

  const { messages, isStreaming, error, traceId, threadId, nodeProgress, sendQuery, reset } =
    useSSEQuery();

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
    <div className="flex flex-col h-screen max-w-5xl mx-auto p-4">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="w-8 h-8" />
            RAG Search
          </h1>
          <div className="flex items-center gap-2">
            <Link href="/traces">
              <Button variant="outline" size="sm">
                <History className="w-4 h-4 mr-2" />
                View Traces
              </Button>
            </Link>
            {threadId && (
              <Badge variant="outline" className="font-mono text-xs">
                Thread: {threadId.slice(0, 8)}...
              </Badge>
            )}
            {traceId && (
              <Badge variant="outline" className="font-mono text-xs">
                Trace: {traceId.slice(0, 8)}...
              </Badge>
            )}
          </div>
        </div>
        <p className="text-muted-foreground">
          Ask questions about your documents with intelligent query routing
        </p>
      </div>

      {/* Chat Messages */}
      <Card className="flex-1 mb-4 overflow-hidden flex flex-col">
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          {messages.length === 0 && !isStreaming && (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <div className="text-center">
                <Sparkles className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p className="text-lg">Start a conversation</p>
                <p className="text-sm mt-2">
                  Ask anything about your documents
                </p>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <Message key={message.id} message={message} />
          ))}

          {/* Node Progress */}
          {isStreaming && (
            <NodeProgress progress={nodeProgress} isStreaming={isStreaming} />
          )}

          {/* Error Display */}
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
        </ScrollArea>

        <Separator />

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="p-4">
          <div className="flex items-end gap-2">
            <div className="flex-1">
              <Input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask a question..."
                disabled={isStreaming}
                className="resize-none"
              />
            </div>
            <div className="flex items-center gap-2">
              <div className="text-sm text-muted-foreground whitespace-nowrap">
                k = {k}
              </div>
              <Input
                type="number"
                min="1"
                max="20"
                value={k}
                onChange={(e) => setK(parseInt(e.target.value) || DEFAULT_K)}
                className="w-16"
                disabled={isStreaming}
              />
              <Button
                type="submit"
                disabled={!query.trim() || isStreaming}
                size="icon"
              >
                {isStreaming ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Send className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            {messages.length > 0 && (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={reset}
                disabled={isStreaming}
              >
                Clear conversation
              </Button>
            )}
          </div>
        </form>
      </Card>

      {/* Footer */}
      <div className="text-center text-xs text-muted-foreground">
        Powered by LangGraph • FastAPI • Next.js
      </div>
    </div>
  );
}
