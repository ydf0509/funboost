"use client";

import { useCallback, useMemo, useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check, Maximize2, Minimize2 } from "lucide-react";
import { Button } from "./Button";

// Collapsible JSON node component - same style as JsonViewerModal
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

interface JsonViewerProps {
    data: unknown;
    defaultExpanded?: boolean;
    className?: string;
    maxHeight?: string;
    showCopy?: boolean;
    showExpandToggle?: boolean;
}

export function JsonViewer({
    data,
    defaultExpanded = true,
    className = "",
    maxHeight = "400px",
    showCopy = true,
    showExpandToggle = true,
}: JsonViewerProps) {
    const [copied, setCopied] = useState(false);
    const [expandAll, setExpandAll] = useState(defaultExpanded);

    const jsonString = useMemo(() => {
        try {
            return JSON.stringify(data, null, 2);
        } catch {
            return String(data);
        }
    }, [data]);

    const handleCopy = useCallback(() => {
        navigator.clipboard.writeText(jsonString);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }, [jsonString]);

    if (data === null || data === undefined) {
        return (
            <div className={`rounded-xl bg-[hsl(var(--sand))] p-4 text-sm text-[hsl(var(--ink-muted))] ${className}`}>
                暂无数据
            </div>
        );
    }

    return (
        <div className={`relative rounded-xl bg-[hsl(var(--sand))] ${className}`}>
            {/* Toolbar */}
            <div className="absolute top-2 right-2 z-10 flex items-center gap-1">
                {showExpandToggle && (
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2"
                        onClick={() => setExpandAll(!expandAll)}
                    >
                        {expandAll ? (
                            <>
                                <Minimize2 className="h-3 w-3" />
                                <span className="text-xs ml-1">折叠</span>
                            </>
                        ) : (
                            <>
                                <Maximize2 className="h-3 w-3" />
                                <span className="text-xs ml-1">展开</span>
                            </>
                        )}
                    </Button>
                )}
                {showCopy && (
                    <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 px-2"
                        onClick={handleCopy}
                    >
                        {copied ? (
                            <>
                                <Check className="h-3 w-3 text-[hsl(var(--success))]" />
                                <span className="text-xs ml-1">已复制</span>
                            </>
                        ) : (
                            <>
                                <Copy className="h-3 w-3" />
                                <span className="text-xs ml-1">复制</span>
                            </>
                        )}
                    </Button>
                )}
            </div>

            {/* JSON Content */}
            <div
                className="p-4 pt-10 overflow-auto font-mono text-sm"
                style={{ maxHeight }}
            >
                <JsonNode data={data} defaultExpanded={expandAll} key={String(expandAll)} />
            </div>
        </div>
    );
}
