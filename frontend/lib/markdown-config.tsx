import { cn } from "@/lib/utils";
import { ComponentProps } from "react";
import remarkGfm from "remark-gfm";

type MarkdownComponents = ComponentProps<typeof import("react-markdown").default>["components"];

export const markdownPlugins = [remarkGfm];

export const markdownComponents: MarkdownComponents = {
    p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
    code: ({ className, children, ...props }) => {
        const match = /language-(\w+)/.exec(className || "");
        return match ? (
            <code className={cn(className, "block bg-card border border-border p-3 rounded-md my-2 overflow-x-auto text-xs font-mono")} {...props}>
                {children}
            </code>
        ) : (
            <code className="bg-card border border-border px-1.5 py-0.5 rounded text-xs font-mono" {...props}>
                {children}
            </code>
        );
    },
    ul: ({ children }) => <ul className="my-2 ml-4 list-disc space-y-1">{children}</ul>,
    ol: ({ children }) => <ol className="my-2 ml-4 list-decimal space-y-1">{children}</ol>,
    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
    h1: ({ children }) => <h1 className="text-lg font-semibold mt-4 mb-2 first:mt-0 text-display">{children}</h1>,
    h2: ({ children }) => <h2 className="text-base font-semibold mt-3 mb-2 first:mt-0 text-display">{children}</h2>,
    h3: ({ children }) => <h3 className="text-sm font-semibold mt-2 mb-1 first:mt-0 text-display">{children}</h3>,
    table: ({ children }) => (
        <div className="my-4 overflow-x-auto border border-border rounded-md">
            <table className="w-full border-collapse text-sm">{children}</table>
        </div>
    ),
    thead: ({ children }) => <thead className="bg-muted/50 border-b border-border">{children}</thead>,
    tbody: ({ children }) => <tbody className="divide-y divide-border">{children}</tbody>,
    tr: ({ children }) => <tr className="divide-x divide-border hover:bg-muted/25 transition-colors">{children}</tr>,
    th: ({ children }) => <th className="px-3 py-2 text-left font-semibold text-foreground">{children}</th>,
    td: ({ children }) => <td className="px-3 py-2 text-foreground">{children}</td>,
    blockquote: ({ children }) => <blockquote className="border-l-4 border-primary pl-4 my-2 italic text-muted-foreground">{children}</blockquote>,
};
