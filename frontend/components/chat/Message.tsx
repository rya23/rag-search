"use client";

import { Message as MessageType } from "@/lib/types";
import ReactMarkdown from "react-markdown";
import rehypeRaw from "rehype-raw";
import { markdownPlugins, markdownComponents } from "@/lib/markdown-config";
import { cn } from "@/lib/utils";
import { User, Bot, Copy, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useState } from "react";

interface MessageProps {
    message: MessageType;
}

export function Message({ message }: MessageProps) {
    const isUser = message.role === "user";
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(message.content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className={cn("flex gap-3 mb-3 group animate-in", isUser ? "flex-row-reverse" : "flex-row")}>
            {/* Avatar */}
            <div
                className={cn(
                    "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-sm font-medium",
                    isUser ? "bg-primary text-primary-foreground" : "bg-muted text-foreground",
                )}
            >
                {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
            </div>

            {/* Message Content */}
            <div className={cn("flex-1 space-y-2 overflow-hidden", isUser ? "text-right" : "text-left")}>
                <div
                    className={cn(
                        "inline-block rounded-lg px-4 py-2.5 text-sm",
                        isUser ? "bg-primary text-primary-foreground" : "bg-muted/60 text-foreground border border-border",
                    )}
                >
                    {isUser ? (
                        <p className="m-0 whitespace-pre-wrap break-words">{message.content}</p>
                    ) : (
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                            <ReactMarkdown remarkPlugins={markdownPlugins} rehypePlugins={[rehypeRaw]} components={markdownComponents}>
                                {message.content}
                            </ReactMarkdown>
                        </div>
                    )}
                </div>

                {/* Metadata */}
                <div className={cn("flex items-center gap-2 text-xs text-muted-foreground px-1", isUser ? "justify-end" : "justify-start")}>
                    <span>{message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                    {!isUser && (
                        <Tooltip>
                            <TooltipTrigger asChild>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
                                    onClick={handleCopy}
                                >
                                    {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                                </Button>
                            </TooltipTrigger>
                            <TooltipContent>
                                <p>{copied ? "Copied!" : "Copy message"}</p>
                            </TooltipContent>
                        </Tooltip>
                    )}
                </div>
            </div>
        </div>
    );
}
