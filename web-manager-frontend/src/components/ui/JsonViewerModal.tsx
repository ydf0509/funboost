"use client";

import { useCallback, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check, Maximize2, Minimize2 } from "lucide-react";
import { Modal } from "./Modal";
import { Button } from "./Button";

type JsonViewerModalProps = {
    open: boolean;
    title: string;
    content: unknown;
    onClose: () => void;
};

// Parse and format JSON safely
function parseJson(content: unknown): { data: unknown; error: string | null } {
    // Handle non-string content (objects, arrays, etc.)
    if (content !== null && typeof content === "object") {
        return { data: content, error: null };
    }
    
    // Convert to string for further processing
    const strContent = typeof content === "string" ? content : String(content ?? "");
    
    if (!strContent || strContent.trim() === "" || strContent === "-") {
        return { data: null, error: "No content" };
    }
    try {
        return { data: JSON.parse(strContent), error: null };
    } catch {
        // Try to unescape if it's a JSON string containing escaped JSON
        try {
            const unescaped = JSON.parse(`"${strContent.replace(/"/g, '\\"')}"`);
            return { data: JSON.parse(unescaped), error: null };
        } catch {
            return { data: strContent, error: null };
        }
    }
}

// Collapsible JSON node component
function JsonNode({
    data,
    path = "",
    level = 0,
    defaultExpanded = true,
}: {
    data: unknown;
    path?: string;
    level?: number;
    defaultExpanded?: boolean;
}) {
    const [expanded, setExpanded] = useState(defaultExpanded);

    if (data === null) {
        return <span className="text-[hsl(var(--danger))]">null</span>;
    }

    if (typeof data === "boolean") {
        return <span className="text-[hsl(var(--warning))]">{data.toString()}</span>;
    }

    if (typeof data === "number") {
        return <span className="text-[hsl(var(--success))]">{data}</span>;
    }

    if (typeof data === "string") {
        return (
            <span className="text-[hsl(var(--info))]">
                &quot;{data}&quot;
            </span>
        );
    }

    if (Array.isArray(data)) {
        if (data.length === 0) {
            return <span className="text-[hsl(var(--ink-muted))]">[]</span>;
        }

        return (
            <span>
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="inline-flex items-center text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--accent))] focus:outline-none"
                >
                    {expanded ? (
                        <ChevronDown className="h-3 w-3" />
                    ) : (
                        <ChevronRight className="h-3 w-3" />
                    )}
                </button>
                <span className="text-[hsl(var(--ink-muted))]">[</span>
                <span className="text-[hsl(var(--ink-muted))] italic ml-1">
                    {data.length} items
                </span>
                {expanded && (
                    <>
                        <div className="ml-4 pl-3 border-l border-[hsl(var(--line))]">
                            {data.map((item, index) => (
                                <div key={`${path}[${index}]`} className="leading-6">
                                    <JsonNode
                                        data={item}
                                        path={`${path}[${index}]`}
                                        level={level + 1}
                                        defaultExpanded={defaultExpanded}
                                    />
                                    {index < data.length - 1 && <span className="text-[hsl(var(--ink-muted))]">,</span>}
                                </div>
                            ))}
                        </div>
                        <span className="text-[hsl(var(--ink-muted))]">]</span>
                    </>
                )}
            </span>
        );
    }

    if (typeof data === "object") {
        const entries = Object.entries(data as Record<string, unknown>);
        if (entries.length === 0) {
            return <span className="text-[hsl(var(--ink-muted))]">{"{}"}</span>;
        }

        return (
            <span>
                <button
                    onClick={() => setExpanded(!expanded)}
                    className="inline-flex items-center text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--accent))] focus:outline-none"
                >
                    {expanded ? (
                        <ChevronDown className="h-3 w-3" />
                    ) : (
                        <ChevronRight className="h-3 w-3" />
                    )}
                </button>
                <span className="text-[hsl(var(--ink-muted))]">{"{"}</span>
                <span className="text-[hsl(var(--ink-muted))] italic ml-1">
                    {entries.length} keys
                </span>
                {expanded && (
                    <>
                        <div className="ml-4 pl-3 border-l border-[hsl(var(--line))]">
                            {entries.map(([key, value], index) => (
                                <div key={`${path}.${key}`} className="leading-6">
                                    <span className="text-[hsl(var(--accent-2))]">&quot;{key}&quot;</span>
                                    <span className="text-[hsl(var(--ink-muted))]">: </span>
                                    <JsonNode
                                        data={value}
                                        path={`${path}.${key}`}
                                        level={level + 1}
                                        defaultExpanded={defaultExpanded}
                                    />
                                    {index < entries.length - 1 && <span className="text-[hsl(var(--ink-muted))]">,</span>}
                                </div>
                            ))}
                        </div>
                        <span className="text-[hsl(var(--ink-muted))]">{"}"}</span>
                    </>
                )}
            </span>
        );
    }

    return <span className="text-[hsl(var(--ink))]">{String(data)}</span>;
}

export function JsonViewerModal({ open, title, content, onClose }: JsonViewerModalProps) {
    const [copied, setCopied] = useState(false);
    const [expandAll, setExpandAll] = useState(true);

    const { data, error } = useMemo(() => parseJson(content), [content]);

    const formattedJson = useMemo(() => {
        if (error || data === null) {
            return typeof content === "string" ? content : JSON.stringify(content, null, 2);
        }
        try {
            return JSON.stringify(data, null, 2);
        } catch {
            return typeof content === "string" ? content : String(content);
        }
    }, [data, error, content]);

    const handleCopy = useCallback(async () => {
        try {
            await navigator.clipboard.writeText(formattedJson);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch {
            // Fallback for older browsers
            const textArea = document.createElement("textarea");
            textArea.value = formattedJson;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand("copy");
            document.body.removeChild(textArea);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    }, [formattedJson]);

    const isJson = error === null && data !== null && typeof data === "object";

    return (
        <Modal open={open} title={title} onClose={onClose} size="xl">
            <div className="space-y-4">
                {/* Toolbar */}
                <div className="flex items-center justify-between gap-2 pb-3 border-b border-[hsl(var(--line))]">
                    <div className="flex items-center gap-2">
                        {isJson && (
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setExpandAll(!expandAll)}
                            >
                                {expandAll ? (
                                    <>
                                        <Minimize2 className="h-3 w-3" />
                                        折叠全部
                                    </>
                                ) : (
                                    <>
                                        <Maximize2 className="h-3 w-3" />
                                        展开全部
                                    </>
                                )}
                            </Button>
                        )}
                    </div>
                    <Button
                        variant={copied ? "primary" : "outline"}
                        size="sm"
                        onClick={handleCopy}
                    >
                        {copied ? (
                            <>
                                <Check className="h-3 w-3" />
                                已复制
                            </>
                        ) : (
                            <>
                                <Copy className="h-3 w-3" />
                                复制
                            </>
                        )}
                    </Button>
                </div>

                {/* Content */}
                <div className="rounded-xl bg-[hsl(var(--sand-2))] p-4 overflow-auto max-h-[60vh]">
                    {isJson ? (
                        <pre className="font-mono text-sm whitespace-pre-wrap break-all">
                            <JsonNode key={expandAll ? "expanded" : "collapsed"} data={data} defaultExpanded={expandAll} />
                        </pre>
                    ) : (
                        <pre className="font-mono text-sm whitespace-pre-wrap break-all text-[hsl(var(--ink))]">
                            {typeof content === "string" ? (content || "-") : JSON.stringify(content, null, 2)}
                        </pre>
                    )}
                </div>
            </div>
        </Modal>
    );
}
