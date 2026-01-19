"use client";

import type { Dispatch, SetStateAction } from "react";
import { CalendarClock, Code, Info, Layers, Timer } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { TextArea } from "@/components/ui/TextArea";

import { TIME_FIELD_LABELS } from "./constants";
import type { FuncParamsInfo, JobForm } from "./types";

type TimingJobsFormModalProps = {
  open: boolean;
  editingJobId: string | null;
  form: JobForm;
  availableQueues: string[];
  funcParamsInfo: FuncParamsInfo | null;
  loadingParams: boolean;
  formError: string | null;
  onClose: () => void;
  onSubmit: () => void;
  onQueueChange: (queueName: string) => void;
  setForm: Dispatch<SetStateAction<JobForm>>;
};

export function TimingJobsFormModal({
  open,
  editingJobId,
  form,
  availableQueues,
  funcParamsInfo,
  loadingParams,
  formError,
  onClose,
  onSubmit,
  onQueueChange,
  setForm,
}: TimingJobsFormModalProps) {
  return (
    <Modal
      open={open}
      title={editingJobId ? `编辑任务 ${editingJobId}` : "添加定时任务"}
      onClose={onClose}
      size="lg"
      footer={
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            取消
          </Button>
          <Button onClick={onSubmit}>{editingJobId ? "保存修改" : "添加任务"}</Button>
        </div>
      }
    >
      <div className="space-y-6">
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            <Code className="mr-1 inline h-4 w-4" />
            队列名称 *
          </label>
          <Select value={form.queue_name} onChange={(event) => onQueueChange(event.target.value)}>
            <option value="">-- 请选择队列 --</option>
            {availableQueues.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            任务 ID（可选，留空自动生成）
          </label>
          <Input
            value={form.job_id}
            onChange={(event) => setForm((prev) => ({ ...prev, job_id: event.target.value }))}
            placeholder="自动生成UUID"
          />
        </div>

        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            <Code className="mr-1 inline h-4 w-4" />
            函数参数 (kwargs) (JSON 格式)
          </label>
          <TextArea
            value={form.kwargs}
            onChange={(event) => setForm((prev) => ({ ...prev, kwargs: event.target.value }))}
            className="min-h-[160px] font-mono text-sm"
            placeholder={form.queue_name ? "正在加载参数模板..." : "请先选择队列名称"}
          />

          {formError ? (
            <div className="text-xs text-[hsl(var(--danger))]" role="alert">
              {formError}
            </div>
          ) : null}

          {loadingParams ? (
            <div className="flex items-center gap-2 text-xs text-[hsl(var(--ink-muted))]">
              <span className="inline-flex h-3 w-3 animate-spin rounded-full border-2 border-[hsl(var(--accent))] border-t-transparent" />
              正在加载函数参数信息...
            </div>
          ) : funcParamsInfo ? (
            <div className="rounded-xl bg-[hsl(var(--sand))] p-4 text-sm">
              <div className="mb-2 flex items-center gap-2">
                <Info className="h-4 w-4 text-[hsl(var(--accent-2))]" />
                <span className="font-semibold text-[hsl(var(--accent-2))]">
                  函数: {funcParamsInfo.func_name || "未知"}
                </span>
              </div>
              {funcParamsInfo.must_arg_name_list && funcParamsInfo.must_arg_name_list.length > 0 && (
                <div className="mb-1">
                  <span className="text-xs text-[hsl(var(--danger))]">必填参数: </span>
                  {funcParamsInfo.must_arg_name_list.map((arg) => (
                    <code
                      key={arg}
                      className="mx-0.5 rounded bg-[hsl(var(--danger))]/10 px-1.5 py-0.5 text-xs text-[hsl(var(--danger))]"
                    >
                      {arg}
                    </code>
                  ))}
                </div>
              )}
              {funcParamsInfo.optional_arg_name_list && funcParamsInfo.optional_arg_name_list.length > 0 && (
                <div>
                  <span className="text-xs text-[hsl(var(--warning))]">可选参数: </span>
                  {funcParamsInfo.optional_arg_name_list.map((arg) => (
                    <code
                      key={arg}
                      className="mx-0.5 rounded bg-[hsl(var(--warning))]/10 px-1.5 py-0.5 text-xs text-[hsl(var(--warning))]"
                    >
                      {arg}
                    </code>
                  ))}
                </div>
              )}
              {(!funcParamsInfo.must_arg_name_list || funcParamsInfo.must_arg_name_list.length === 0) &&
                (!funcParamsInfo.optional_arg_name_list || funcParamsInfo.optional_arg_name_list.length === 0) && (
                  <span className="text-xs text-[hsl(var(--success))]">无必填参数</span>
                )}
            </div>
          ) : form.queue_name ? (
            <div className="text-xs text-[hsl(var(--ink-muted))]">无法获取函数参数信息</div>
          ) : null}
        </div>

        <div className="space-y-3">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            <CalendarClock className="mr-1 inline h-4 w-4" />
            触发器类型 *
          </label>
          <div className="flex flex-wrap gap-4">
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="triggerType"
                checked={form.triggerType === "date"}
                onChange={() => setForm((prev) => ({ ...prev, triggerType: "date" }))}
                className="h-4 w-4"
              />
              <span className="text-sm">一次性任务</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="triggerType"
                checked={form.triggerType === "interval"}
                onChange={() => setForm((prev) => ({ ...prev, triggerType: "interval" }))}
                className="h-4 w-4"
              />
              <span className="text-sm">间隔执行</span>
            </label>
            <label className="flex cursor-pointer items-center gap-2">
              <input
                type="radio"
                name="triggerType"
                checked={form.triggerType === "cron"}
                onChange={() => setForm((prev) => ({ ...prev, triggerType: "cron" }))}
                className="h-4 w-4"
              />
              <span className="text-sm">定时执行</span>
            </label>
          </div>
        </div>

        {form.triggerType === "date" && (
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              执行时间
            </label>
            <Input
              type="datetime-local"
              value={form.run_date}
              onChange={(event) => setForm((prev) => ({ ...prev, run_date: event.target.value }))}
            />
          </div>
        )}

        {form.triggerType === "interval" && (
          <div className="space-y-3">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              <Timer className="mr-1 inline h-4 w-4" />
              间隔执行配置 <span className="font-normal text-[hsl(var(--ink-muted))]">(至少填写一个)</span>
            </label>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
              {Object.entries(form.interval).map(([key, value]) => (
                <div key={key} className="space-y-1">
                  <label className="text-xs text-[hsl(var(--ink-muted))]">{TIME_FIELD_LABELS[key]}</label>
                  <Input
                    type="number"
                    min="0"
                    value={value}
                    onChange={(event) =>
                      setForm((prev) => ({
                        ...prev,
                        interval: { ...prev.interval, [key]: event.target.value },
                      }))
                    }
                  />
                </div>
              ))}
            </div>
            <div className="rounded-lg bg-[hsl(var(--sand))] p-3 text-xs text-[hsl(var(--ink-muted))]">
              示例: 每10分钟 → 分钟填 10 | 每2小时 → 小时填 2 | 每天 → 天填 1
            </div>
          </div>
        )}

        {form.triggerType === "cron" && (
          <div className="space-y-3">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              定时执行配置 (Cron)
            </label>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {Object.entries(form.cron).map(([key, value]) => (
                <div key={key} className="space-y-1">
                  <label className="text-xs text-[hsl(var(--ink-muted))]">{TIME_FIELD_LABELS[key]}</label>
                  <Input
                    value={value}
                    placeholder="*"
                    onChange={(event) =>
                      setForm((prev) => ({
                        ...prev,
                        cron: { ...prev.cron, [key]: event.target.value },
                      }))
                    }
                  />
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="space-y-3">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            <Layers className="mr-1 inline h-4 w-4" />
            存储方式
          </label>
          <div className="flex flex-wrap gap-4">
            <label className="flex cursor-pointer items-center gap-2">
              <input type="radio" checked readOnly className="h-4 w-4" />
              <span className="text-sm">Redis (推荐，支持分布式)</span>
            </label>
            <label className="flex cursor-not-allowed items-center gap-2 opacity-50">
              <input type="radio" disabled className="h-4 w-4" />
              <span className="text-sm">内存 (单机，重启丢失)</span>
            </label>
          </div>
        </div>

        <label className="flex items-center gap-2 text-sm text-[hsl(var(--ink-muted))]">
          <input
            type="checkbox"
            checked={form.replace_existing}
            onChange={(event) => setForm((prev) => ({ ...prev, replace_existing: event.target.checked }))}
            className="h-4 w-4 rounded border-[hsl(var(--line))]"
          />
          如果任务ID已存在，则替换
        </label>
      </div>
    </Modal>
  );
}
