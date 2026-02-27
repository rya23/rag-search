"use client";

import { Message as MessageType } from "@/lib/types";
import { Card } from "@/components/ui/card";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { cn } from "@/lib/utils";

interface MessageProps {
  message: MessageType;
}

export function Message({ message }: MessageProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full mb-4",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      <Card
        className={cn(
          "max-w-[80%] p-4",
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-card text-card-foreground"
        )}
      >
        <div className="prose prose-invert prose-sm max-w-none">
          {isUser ? (
            <p className="m-0">{message.content}</p>
          ) : (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                code: ({ className, children, ...props }) => {
                  const match = /language-(\w+)/.exec(className || "");
                  return match ? (
                    <code
                      className={cn(
                        className,
                        "block bg-muted p-2 rounded my-2 overflow-x-auto"
                      )}
                      {...props}
                    >
                      {children}
                    </code>
                  ) : (
                    <code
                      className="bg-muted px-1.5 py-0.5 rounded text-sm"
                      {...props}
                    >
                      {children}
                    </code>
                  );
                },
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
        <div className="text-xs opacity-60 mt-2">
          {message.timestamp.toLocaleTimeString()}
        </div>
      </Card>
    </div>
  );
}
