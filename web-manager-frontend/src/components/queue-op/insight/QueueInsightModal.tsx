"use client";

import { useState } from "react";
import { Activity, BarChart3, Gauge, Terminal, Users } from "lucide-react";

import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { JsonViewerModal } from "@/components/ui/JsonViewerModal";

import { useActionPermissions } from "@/hooks/useActionPermissions";
import { useProject } from "@/contexts/ProjectContext";

import type { QueueRow } from "@/components/queue-op/types";
import type { InsightTab } from "./types";
import { OverviewTab } from "./tabs/OverviewTab";
import { ResultsTab } from "./tabs/ResultsTab";
import { SpeedTab } from "./tabs/SpeedTab";
import { RpcTab } from "./tabs/RpcTab";
import { ConsumersTab } from "./tabs/ConsumersTab";

export type QueueInsightModalProps = {
  open: boolean;
  queue: QueueRow | null;
  activeTab: InsightTab;
  onTabChange: (tab: InsightTab) => void;
  onClose: () => void;
};

export function QueueInsightModal({ open, queue, activeTab, onTabChange, onClose }: QueueInsightModalProps) {
  const { currentProject } = useProject();
  const { canExecute } = useActionPermissions("queue");
  const projectLevel = currentProject?.permission_level ?? "admin";
  const canWriteProject = !currentProject || projectLevel === "write" || projectLevel === "admin";
  const canOperateQueue = canExecute && canWriteProject;

  const [jsonModalOpen, setJsonModalOpen] = useState(false);
  const [jsonModalTitle, setJsonModalTitle] = useState("");
  const [jsonModalContent, setJsonModalContent] = useState("");

  const openJsonModal = (title: string, content: string) => {
    setJsonModalTitle(title);
    setJsonModalContent(content);
    setJsonModalOpen(true);
  };

  if (!queue) return null;

  const tabs: Array<{ id: InsightTab; label: string; icon: React.ReactNode }> = [
    { id: "overview", label: "概览", icon: <Gauge className="h-4 w-4" /> },
    { id: "results", label: "结果", icon: <Activity className="h-4 w-4" /> },
    { id: "speed", label: "速率", icon: <BarChart3 className="h-4 w-4" /> },
    { id: "rpc", label: "RPC", icon: <Terminal className="h-4 w-4" /> },
    { id: "consumers", label: "消费者", icon: <Users className="h-4 w-4" /> },
  ];

  return (
    <>
      <Modal
        open={open}
        title={`队列洞察 · ${queue.queue_name}`}
        subtitle={queue.queue_params?.consuming_function_name || ""}
        onClose={onClose}
        size="xxl"
        contentMaxHeight="78vh"
        footer={
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-[hsl(var(--ink-muted))]">
              <span>状态:</span>
              {queue.pause_flag === 1 ? (
                <Badge tone="warning">暂停</Badge>
              ) : (queue.active_consumers?.length ?? 0) > 0 ? (
                <Badge tone="success">运行中</Badge>
              ) : (
                <Badge tone="neutral">空闲</Badge>
              )}
              <span className="ml-2">消费者:</span>
              <Badge tone={(queue.active_consumers?.length ?? 0) > 0 ? "success" : "neutral"}>
                {queue.active_consumers?.length ?? 0}
              </Badge>
              <span className="ml-2">消息:</span>
              <Badge tone="warning">{queue.msg_num_in_broker ?? 0}</Badge>
            </div>
            <Button variant="outline" onClick={onClose}>关闭</Button>
          </div>
        }
      >
        <div className="space-y-6">
          <div className="flex flex-wrap items-center gap-2 border-b border-[hsl(var(--line))]/60 pb-3">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => onTabChange(tab.id)}
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs transition ${
                  activeTab === tab.id
                    ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))] text-white"
                    : "border-[hsl(var(--line))] text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))]"
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === "overview" && (
            <OverviewTab queue={queue} onOpenJson={openJsonModal} />
          )}

          {activeTab === "results" && (
            <ResultsTab
              queueName={queue.queue_name}
              projectId={currentProject?.id?.toString()}
              canOperateQueue={canOperateQueue}
              onOpenJson={openJsonModal}
            />
          )}

          {activeTab === "speed" && (
            <SpeedTab
              queueName={queue.queue_name}
              projectId={currentProject?.id?.toString()}
            />
          )}

          {activeTab === "rpc" && (
            <RpcTab
              queueName={queue.queue_name}
              canOperateQueue={canOperateQueue}
            />
          )}

          {activeTab === "consumers" && (
            <ConsumersTab
              queueName={queue.queue_name}
              projectId={currentProject?.id?.toString()}
              onOpenJson={openJsonModal}
            />
          )}
        </div>
      </Modal>

      <JsonViewerModal
        open={jsonModalOpen}
        title={jsonModalTitle}
        content={jsonModalContent}
        onClose={() => setJsonModalOpen(false)}
      />
    </>
  );
}
