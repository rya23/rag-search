"use client";

import { NodeProgress as NodeProgressType } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Loader2 } from "lucide-react";

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

  const currentNode = progress[progress.length - 1];

  return (
    <div className="flex items-center gap-2 mb-4">
      {progress.map((node, index) => {
        const isComplete = index < progress.length - 1 || !isStreaming;
        const label = NODE_LABELS[node.node] || node.node;

        return (
          <Badge
            key={`${node.node}-${index}`}
            variant={isComplete ? "default" : "secondary"}
            className="gap-1"
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
  );
}
