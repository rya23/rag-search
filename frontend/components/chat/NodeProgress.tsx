"use client";

import { NodeProgress as NodeProgressType } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Loader2, Bot } from "lucide-react";
import { cn } from "@/lib/utils";

interface NodeProgressProps {
  progress: NodeProgressType[];
  isStreaming: boolean;
}

const NODE_LABELS: Record<string, string> = {
  analyze_query: "Analyzing Query",
  simple_retrieve: "Retrieving Documents",
  multi_query_retrieve: "Multi-Query Retrieval",
  generate_answer: "Generating Answer",
};

export function NodeProgress({ progress, isStreaming }: NodeProgressProps) {
  if (progress.length === 0) return null;

  return (
    <div className="flex gap-3 mb-3 animate-in">
      {/* Avatar */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted text-foreground">
        <Bot className="h-4 w-4" />
      </div>

      {/* Progress Pills */}
      <div className="flex-1">
        <div className="inline-block rounded-lg px-4 py-2.5 bg-muted/60 border border-border">
          <div className="flex items-center gap-2 flex-wrap">
            {progress.map((node, index) => {
              const isComplete = index < progress.length - 1 || !isStreaming;
              const label = NODE_LABELS[node.node] || node.node;

              return (
                <Badge
                  key={`${node.node}-${index}`}
                  variant={isComplete ? "default" : "secondary"}
                  className={cn(
                    "gap-1.5 text-xs font-medium transition-all",
                    isComplete && "bg-chart-1/20 text-chart-1 border-chart-1/30"
                  )}
                >
                  {isComplete ? (
                    <CheckCircle2 className="w-3 h-3" />
                  ) : (
                    <Loader2 className="w-3 h-3 animate-spin" />
                  )}
                  {label}
                </Badge>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
