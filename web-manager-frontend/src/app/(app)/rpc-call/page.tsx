"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AlertTriangle, ChevronRight, Code, Copy, Play, RefreshCw, Search, Send, Terminal, Zap } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { JsonViewer } from "@/components/ui/JsonViewer";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Select } from "@/components/ui/Select";
import { StatCard } from "@/components/ui/StatCard";
import { TextArea } from "@/components/ui/TextArea";
import { Toggle } from "@/components/ui/Toggle";
import { apiFetch, funboostFetch } from "@/lib/api";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { useProject } from "@/contexts/ProjectContext";

const DEFAULT_TIMEOUT = 60;

type ParamInfo = {
  must_arg_name_list?: string[];
  optional_arg_name_list?: string[];
};

export default function RpcCallPage() {
  const [queueList, setQueueList] = useState<{ name: string; count: number }[]>([]);
  const [queue, setQueue] = useState("");
  const [payload, setPayload] = useState("{}");
  const [needResult, setNeedResult] = useState(true);
  const [timeout, setTimeoutValue] = useState(DEFAULT_TIMEOUT);
  const [runInfo, setRunInfo] = useState<Record<string, unknown> | null>(null);
  const [queueConfig, setQueueConfig] = useState<Record<string, unknown> | null>(null);
  const [funcName, setFuncName] = useState<string>("-");
  const [paramInfo, setParamInfo] = useState<ParamInfo | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  const [taskQuery, setTaskQuery] = useState("");
  const [taskTimeout, setTaskTimeout] = useState(30);
  const [notice, setNotice] = useState<{ type: "success" | "error" | "warning"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [sending, setSending] = useState(false);
  const [querying, setQuerying] = useState(false);

  const { currentProject, careProjectName } = useProject();
  const { canExecute } = useActionPermissions("queue");
  // 当未选择具体项目时默认有写权限（全部项目模式）
  const projectLevel = currentProject?.permission_level ?? "admin";
  const canWriteProject = !currentProject || projectLevel === "write" || projectLevel === "admin";
  const canOperateQueue = canExecute && canWriteProject;

  const loadQueues = useCallback(async () => {
    setLoading(true);
    try {
      let url = "/queue/get_msg_num_all_queues";
      if (currentProject?.id) {
        url += `?project_id=${currentProject.id}`;
      }
      const data = await apiFetch<Record<string, number>>(url);
      const list = Object.entries(data).map(([name, count]) => ({ name, count }));
      setQueueList(list);
      if (!queue && list.length > 0) {
        setQueue(list[0].name);
      }
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "加载队列失败");
    } finally {
      setLoading(false);
    }
  }, [queue, currentProject?.id, careProjectName]);

  const loadQueueConfig = useCallback(async () => {
    if (!queue) return;
    try {
      const configData = await funboostFetch<Record<string, unknown>>(
        `/funboost/get_one_queue_config?queue_name=${encodeURIComponent(queue)}`
      );
      setQueueConfig(configData);

      // Extract function name
      const funcNameFromConfig =
        (configData as { queue_params?: { consuming_function_name?: string } })?.queue_params?.consuming_function_name ||
        (configData as { auto_generate_info?: { function_name?: string } })?.auto_generate_info?.function_name ||
        "-";
      setFuncName(funcNameFromConfig);

      const runData = await funboostFetch<Record<string, unknown>>(
        `/funboost/get_queue_run_info?queue_name=${encodeURIComponent(queue)}`
      );
      setRunInfo(runData);

      const autoInfo = (configData as { auto_generate_info?: { final_func_input_params_info?: ParamInfo } })
        .auto_generate_info?.final_func_input_params_info;

      setParamInfo(autoInfo || null);

      // Generate template without <必填> labels - just use empty values
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
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "加载队列信息失败");
    }
  }, [queue]);

  useEffect(() => {
    loadQueues();
  }, [loadQueues]);

  useEffect(() => {
    loadQueueConfig();
  }, [loadQueueConfig]);

  const hasConsumers = useMemo(() => {
    const consumers = (runInfo as { active_consumers?: unknown[] })?.active_consumers ?? [];
    return consumers.length > 0;
  }, [runInfo]);

  const consumerCount = useMemo(() => {
    return (runInfo as { active_consumers?: unknown[] })?.active_consumers?.length ?? 0;
  }, [runInfo]);

  const showNotice = (type: "success" | "error" | "warning", message: string) => {
    setNotice({ type, message });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    showNotice("success", "已复制到剪贴板");
  };

  const handleSend = async () => {
    setNotice(null);
    setResult(null);
    try {
      if (!canOperateQueue) {
        showNotice("warning", "当前项目无写权限，无法发布消息");
        return;
      }
      setSending(true);
      const msgBody = JSON.parse(payload || "{}");
      const data = await funboostFetch<{ task_id: string; status_and_result: Record<string, unknown> }>(
        "/funboost/publish",
        {
          method: "POST",
          json: {
            queue_name: queue,
            msg_body: msgBody,
            need_result: needResult,
            timeout,
          },
        }
      );
      setResult({ task_id: data.task_id, ...data.status_and_result });
      setTaskQuery(data.task_id);  // Auto-fill task ID for later query
      showNotice("success", "消息发布成功");
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "发布失败");
    } finally {
      setSending(false);
    }
  };

  const handleQuery = async () => {
    setNotice(null);
    setResult(null);
    if (!taskQuery) {
      showNotice("warning", "请输入任务ID");
      return;
    }
    setQuerying(true);
    try {
      const data = await funboostFetch<{ task_id: string; status_and_result: Record<string, unknown> }>(
        `/funboost/get_result?task_id=${encodeURIComponent(taskQuery)}&timeout=${taskTimeout}`
      );
      setResult({ task_id: data.task_id, ...data.status_and_result });
      showNotice("success", "查询成功");
    } catch (err) {
      showNotice("error", err instanceof Error ? err.message : "查询失败");
    } finally {
      setQuerying(false);
    }
  };

  const getResultStatus = () => {
    if (!result) return null;
    if (result.run_status === "running") return { tone: "info" as const, text: "运行中" };
    if (result.success) return { tone: "success" as const, text: "成功" };
    return { tone: "danger" as const, text: "失败" };
  };

  return (
    <RequirePermission permissions={["queue:read"]} projectLevel="read">
      <div className="space-y-6">
        {/* Action Bar */}
        <div className="flex items-center justify-end">
          <Button variant="outline" size="sm" onClick={loadQueues} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            刷新队列
          </Button>
        </div>

        {/* Notice */}
        {notice && (
          <Card className={`border text-sm ${notice.type === "success"
            ? "border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10 text-[hsl(var(--success))]"
            : notice.type === "warning"
              ? "border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10 text-[hsl(var(--warning))]"
              : "border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 text-[hsl(var(--danger))]"
            }`}>
            {notice.message}
          </Card>
        )}

        {/* Stats Bar */}
        <div className="grid gap-4 grid-cols-2 md:grid-cols-4">
          <StatCard
            label="目标队列"
            value={queue || "-"}
            helper={`${queueList.find((item) => item.name === queue)?.count ?? 0} 条消息`}
          />
          <StatCard
            label="消费函数"
            value={funcName}
            helper="处理函数"
          />
          <StatCard
            label="消费者状态"
            value={
              <span className={hasConsumers ? "text-[hsl(var(--success))]" : "text-[hsl(var(--danger))]"}>
                {hasConsumers ? `${consumerCount} 个活跃` : "无消费者"}
              </span>
            }
            helper={hasConsumers ? "正常运行" : "注意检查"}
          />
          <StatCard
            label="RPC超时"
            value={`${timeout}s`}
            helper="等待响应时间"
          />
        </div>

        {/* Warning if no consumers */}
        {!hasConsumers && queue && (
          <Card className="border border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10">
            <div className="flex items-center gap-3 text-[hsl(var(--warning))]">
              <AlertTriangle className="h-5 w-5 flex-shrink-0" />
              <div>
                <p className="font-medium">未检测到活跃消费者</p>
                <p className="text-xs opacity-80">该队列可能无法处理消息，请检查消费者是否已启动</p>
              </div>
            </div>
          </Card>
        )}

        {/* Main Content - Two Column Layout */}
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Left: Send Message */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Send className="h-5 w-5 text-[hsl(var(--accent))]" />
              <SectionHeader title="发送消息" subtitle="" />
            </div>

            <div className="space-y-4">
              {/* Queue Selection */}
              <div className="space-y-2">
                <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                  目标队列
                </label>
                <Select value={queue} onChange={(e) => setQueue(e.target.value)}>
                  {queueList.length === 0 ? (
                    <option value="">暂无队列</option>
                  ) : (
                    queueList.map((item) => (
                      <option key={item.name} value={item.name}>
                        {item.name} ({item.count} 条)
                      </option>
                    ))
                  )}
                </Select>
              </div>

              {/* Function Parameters Info */}
              {paramInfo && (
                <div className="rounded-xl bg-[hsl(var(--sand))] p-3 space-y-2">
                  <div className="flex items-center gap-2 text-xs font-medium text-[hsl(var(--ink))]">
                    <Code className="h-4 w-4" />
                    函数参数说明
                  </div>
                  {paramInfo.must_arg_name_list && paramInfo.must_arg_name_list.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {paramInfo.must_arg_name_list.map((name) => (
                        <Badge key={name} tone="danger" className="text-xs">
                          {name}
                        </Badge>
                      ))}
                      <span className="text-xs text-[hsl(var(--ink-muted))] self-center ml-1">必填</span>
                    </div>
                  )}
                  {paramInfo.optional_arg_name_list && paramInfo.optional_arg_name_list.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {paramInfo.optional_arg_name_list.map((name) => (
                        <Badge key={name} tone="neutral" className="text-xs">
                          {name}
                        </Badge>
                      ))}
                      <span className="text-xs text-[hsl(var(--ink-muted))] self-center ml-1">可选</span>
                    </div>
                  )}
                </div>
              )}

              {/* Payload Editor */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                    消息内容 (JSON)
                  </label>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 px-2 text-xs"
                    onClick={() => copyToClipboard(payload)}
                  >
                    <Copy className="h-3 w-3" />
                    复制
                  </Button>
                </div>
                <TextArea
                  value={payload}
                  onChange={(e) => setPayload(e.target.value)}
                  className="min-h-[180px] font-mono text-sm"
                  placeholder='{"param1": "value1", "param2": "value2"}'
                />
              </div>

              {/* Options Row */}
              <div className="flex flex-wrap items-center gap-4">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-[hsl(var(--ink-muted))]">超时</label>
                  <Input
                    type="number"
                    value={timeout}
                    onChange={(e) => setTimeoutValue(Number(e.target.value))}
                    className="w-20 h-8 text-sm"
                    min={1}
                    max={3600}
                  />
                  <span className="text-xs text-[hsl(var(--ink-muted))]">秒</span>
                </div>
                <div className="flex items-center gap-2">
                  <Toggle
                    checked={needResult}
                    onChange={setNeedResult}
                    label="等待结果返回"
                  />
                </div>
              </div>

              {/* Send Button */}
              <Button
                onClick={handleSend}
                disabled={sending || !queue || !canOperateQueue}
                className="w-full"
              >
                {sending ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    发送中...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4" />
                    发布消息
                  </>
                )}
              </Button>
            </div>
          </Card>

          {/* Right: Query & Result */}
          <div className="space-y-6">
            {/* Query Task */}
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Search className="h-5 w-5 text-[hsl(var(--accent))]" />
                <SectionHeader title="查询任务" subtitle="" />
              </div>

              <div className="flex flex-wrap items-end gap-3">
                <div className="flex-1 min-w-[200px] space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                    任务 ID
                  </label>
                  <Input
                    placeholder="输入任务ID查询结果"
                    value={taskQuery}
                    onChange={(e) => setTaskQuery(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-[hsl(var(--ink-muted))]">超时(秒)</label>
                  <Input
                    type="number"
                    value={taskTimeout}
                    onChange={(e) => setTaskTimeout(Number(e.target.value))}
                    className="w-20"
                    min={1}
                  />
                </div>
                <Button variant="primary" onClick={handleQuery} disabled={querying}>
                  {querying ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Play className="h-4 w-4" />
                  )}
                  查询
                </Button>
              </div>
            </Card>

            {/* Result Display */}
            <Card>
              <div className="flex items-center gap-2 mb-4">
                <Terminal className="h-5 w-5 text-[hsl(var(--accent))]" />
                <SectionHeader title="执行结果" subtitle="" />
                {result && getResultStatus() && (
                  <Badge tone={getResultStatus()!.tone} className="ml-auto">
                    {getResultStatus()!.text}
                  </Badge>
                )}
              </div>

              {result ? (
                <div className="space-y-3">
                  {typeof result.task_id === 'string' && result.task_id && (
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-[hsl(var(--ink-muted))]">Task ID:</span>
                      <code className="bg-[hsl(var(--sand-2))] px-2 py-0.5 rounded font-mono">
                        {result.task_id}
                      </code>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-5 px-1"
                        onClick={() => copyToClipboard(result.task_id as string)}
                      >
                        <Copy className="h-3 w-3" />
                      </Button>
                    </div>
                  )}
                  <JsonViewer
                    data={result as Record<string, unknown>}
                    defaultExpanded={true}
                    maxHeight="300px"
                  />
                </div>
              ) : (
                <EmptyState
                  title="暂无结果"
                  subtitle="发布消息或查询任务后，结果将显示在这里"
                />
              )}
            </Card>
          </div>
        </div>

        {/* Bottom: Queue Info (Collapsible) */}
        <details className="group">
          <summary className="cursor-pointer list-none">
            <Card className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <ChevronRight className="h-4 w-4 text-[hsl(var(--ink-muted))] transition-transform group-open:rotate-90" />
                <span className="font-medium text-[hsl(var(--ink))]">队列详细配置</span>
              </div>
              <Badge tone="neutral">{queue || "-"}</Badge>
            </Card>
          </summary>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <Card>
              <SectionHeader title="队列配置" subtitle="参数与输入结构" />
              <div className="mt-4">
                <JsonViewer
                  data={queueConfig ?? {}}
                  defaultExpanded={true}
                  maxHeight="300px"
                />
              </div>
            </Card>
            <Card>
              <SectionHeader title="运行信息" subtitle="消费者与运行指标" />
              <div className="mt-4">
                <JsonViewer
                  data={runInfo ?? {}}
                  defaultExpanded={true}
                  maxHeight="300px"
                />
              </div>
            </Card>
          </div>
        </details>
      </div>
    </RequirePermission>
  );
}
