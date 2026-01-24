"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { RefreshCw, Send } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { JsonViewer } from "@/components/ui/JsonViewer";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Toggle } from "@/components/ui/Toggle";

import { funboostFetch } from "@/lib/api";

import type { ParamInfo } from "../types";

type RpcTabProps = {
  queueName: string;
  canOperateQueue: boolean;
};

export function RpcTab({ queueName, canOperateQueue }: RpcTabProps) {
  const [payload, setPayload] = useState("{}");
  const [needResult, setNeedResult] = useState(true);
  const [timeout, setTimeoutValue] = useState(60);
  const [taskQuery, setTaskQuery] = useState("");
  const [taskTimeout, setTaskTimeout] = useState(30);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [sending, setSending] = useState(false);
  const [querying, setQuerying] = useState(false);
  const [funcName, setFuncName] = useState<string>("-");
  const [paramInfo, setParamInfo] = useState<ParamInfo | null>(null);
  const [runInfo, setRunInfo] = useState<Record<string, unknown> | null>(null);

  const hasConsumers = useMemo(() => {
    return ((runInfo as { active_consumers?: unknown[] })?.active_consumers ?? []).length > 0;
  }, [runInfo]);

  const loadRpcInfo = useCallback(async () => {
    if (!queueName) return;
    const configData = await funboostFetch<Record<string, unknown>>(
      `/funboost/get_one_queue_config?queue_name=${encodeURIComponent(queueName)}`
    );
    const funcNameFromConfig =
      (configData as { queue_params?: { consuming_function_name?: string } })?.queue_params?.consuming_function_name ||
      (configData as { auto_generate_info?: { function_name?: string } })?.auto_generate_info?.function_name ||
      "-";
    setFuncName(funcNameFromConfig);

    const runData = await funboostFetch<Record<string, unknown>>(
      `/funboost/get_queue_run_info?queue_name=${encodeURIComponent(queueName)}`
    );
    setRunInfo(runData);

    const autoInfo = (configData as { auto_generate_info?: { final_func_input_params_info?: ParamInfo } })
      .auto_generate_info?.final_func_input_params_info;
    setParamInfo(autoInfo || null);

    if (autoInfo) {
      const template: Record<string, string | number | null> = {};
      autoInfo.must_arg_name_list?.forEach((name) => {
        template[name] = "";
      });
      autoInfo.optional_arg_name_list?.forEach((name) => {
        template[name] = null;
      });
      setPayload(JSON.stringify(template, null, 2));
    } else {
      setPayload("{}");
    }
  }, [queueName]);

  useEffect(() => {
    if (!queueName) return;
    setResult(null);
    setTaskQuery("");
    loadRpcInfo();
  }, [queueName, loadRpcInfo]);

  const handleSend = async () => {
    if (!canOperateQueue) return;
    try {
      setSending(true);
      setResult(null);
      const msgBody = JSON.parse(payload || "{}");
      const data = await funboostFetch<{ task_id: string; status_and_result: Record<string, unknown> }>(
        "/funboost/publish",
        {
          method: "POST",
          json: {
            queue_name: queueName,
            msg_body: msgBody,
            need_result: needResult,
            timeout,
          },
        }
      );
      setResult({ task_id: data.task_id, ...data.status_and_result });
      setTaskQuery(data.task_id);
    } finally {
      setSending(false);
    }
  };

  const handleQuery = async () => {
    if (!taskQuery) return;
    try {
      setQuerying(true);
      const data = await funboostFetch<{ task_id: string; status_and_result: Record<string, unknown> }>(
        `/funboost/get_result?task_id=${encodeURIComponent(taskQuery)}&timeout=${taskTimeout}`
      );
      setResult({ task_id: data.task_id, ...data.status_and_result });
    } finally {
      setQuerying(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <SectionHeader title="RPC 参数" subtitle="输入 JSON 参数并发送" />
          <div className="mt-3 space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <Badge tone="info">函数: {funcName}</Badge>
              <Badge tone={hasConsumers ? "success" : "warning"}>{hasConsumers ? "消费者在线" : "无消费者"}</Badge>
            </div>
            {paramInfo && (
              <div className="text-xs text-[hsl(var(--ink-muted))]">
                必填: {(paramInfo.must_arg_name_list ?? []).join(", ") || "-"} | 可选: {(paramInfo.optional_arg_name_list ?? []).join(", ") || "-"}
              </div>
            )}
            <div className="space-y-2">
              <label className="text-xs font-medium text-[hsl(var(--ink-muted))]">JSON 参数</label>
              <textarea
                className="w-full min-h-[180px] rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--sand))] p-3 text-xs font-mono"
                value={payload}
                onChange={(e) => setPayload(e.target.value)}
              />
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Toggle checked={needResult} onChange={setNeedResult} label="需要结果" />
              <div className="flex items-center gap-2">
                <label className="text-xs text-[hsl(var(--ink-muted))]">超时</label>
                <Input type="number" className="w-20" value={timeout} onChange={(e) => setTimeoutValue(Number(e.target.value))} />
              </div>
              <Button variant="primary" onClick={handleSend} disabled={sending || !canOperateQueue}>
                <Send className="h-4 w-4" />
                发送 RPC
              </Button>
            </div>
          </div>
        </Card>

        <Card>
          <SectionHeader title="结果" subtitle="执行回执" />
          <div className="mt-3 space-y-3">
            <div className="flex items-center gap-2">
              <label className="text-xs text-[hsl(var(--ink-muted))]">Task ID</label>
              <Input value={taskQuery} onChange={(e) => setTaskQuery(e.target.value)} placeholder="任务ID" />
              <Input
                type="number"
                className="w-20"
                value={taskTimeout}
                onChange={(e) => setTaskTimeout(Number(e.target.value))}
                placeholder="超时"
              />
              <Button variant="outline" size="sm" onClick={handleQuery} disabled={querying}>
                <RefreshCw className={`h-4 w-4 ${querying ? "animate-spin" : ""}`} />
                查询
              </Button>
            </div>
            <JsonViewer data={result} maxHeight="320px" />
          </div>
        </Card>
      </div>
    </div>
  );
}
