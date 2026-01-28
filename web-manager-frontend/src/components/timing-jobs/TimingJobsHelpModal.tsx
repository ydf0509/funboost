"use client";

import type { ReactNode } from "react";
import { BookOpen, Clock, GraduationCap, PauseCircle, Rocket, Shield, Star } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";

type TimingJobsHelpModalProps = {
  open: boolean;
  onClose: () => void;
};

function HelpSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="rounded-2xl border border-[hsl(var(--line))] bg-[hsl(var(--card))]/75 p-4">
      <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-[hsl(var(--ink))]">
        <span className="inline-flex h-8 w-8 items-center justify-center rounded-xl bg-[hsl(var(--accent))]/15 text-[hsl(var(--accent))]">
          {icon}
        </span>
        {title}
      </div>
      <div className="space-y-2 text-sm text-[hsl(var(--ink-muted))]">{children}</div>
    </div>
  );
}

export function TimingJobsHelpModal({ open, onClose }: TimingJobsHelpModalProps) {
  return (
    <Modal
      open={open}
      title="定时任务使用说明"
      onClose={onClose}
      size="lg"
      footer={
        <div className="flex justify-end">
          <Button onClick={onClose}>我知道了</Button>
        </div>
      }
    >
      <div className="space-y-4">
        <HelpSection title="📚 重要提示：先学习 APScheduler！" icon={<GraduationCap className="h-4 w-4" />}>
          <p>
            <strong>
              Funboost 的定时任务功能是对 <span className="text-[hsl(var(--accent))]">APScheduler</span> 的轻度封装。
            </strong>
          </p>
          <p>APScheduler 是 Python 中最知名的定时任务调度库，Funboost 在其基础上进行了增强，支持分布式场景和消息队列集成。</p>
          <div className="rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--sand))] p-3">
            <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-[hsl(var(--ink))]">
              <BookOpen className="h-4 w-4" />
              学习资源
            </div>
            <p className="text-xs text-[hsl(var(--ink-muted))]">
              📖 官方文档：
              <a
                href="https://apscheduler.readthedocs.io/"
                target="_blank"
                rel="noreferrer"
                className="ml-1 text-[hsl(var(--info))]"
              >
                https://apscheduler.readthedocs.io/
              </a>
            </p>
          </div>
        </HelpSection>

        <HelpSection title="什么是「暂停 Scheduler（定时器）」？" icon={<Clock className="h-4 w-4" />}>
          <p>
            <span className="text-[hsl(var(--accent))]">Scheduler（调度器）</span> 是管理和触发所有定时任务的核心组件。
          </p>
          <p>
            暂停定时器意味着：<strong>该队列下的所有定时任务暂停调度</strong>，但任务配置保留。恢复后继续执行。
          </p>
        </HelpSection>

        <HelpSection title="什么是「暂停 Job（定时任务）」？" icon={<PauseCircle className="h-4 w-4" />}>
          <p>
            <span className="text-[hsl(var(--accent))]">Job（定时任务）</span> 是具体的一个定时执行单元。
          </p>
          <p>
            暂停某个 Job 意味着：<strong>仅该任务暂停</strong>，其他任务不受影响，可随时恢复。
          </p>
        </HelpSection>

        <HelpSection title="推荐使用方式" icon={<Star className="h-4 w-4" />}>
          <p>
            <strong className="text-[hsl(var(--success))]">💡 推荐在网页管理后台保持定时器为「暂停」状态！</strong>
          </p>
          <p>网页后台的定位是 <span className="text-[hsl(var(--accent))]">定时任务的管理工具</span>，用于增删改查。</p>
          <p>
            <strong>正确做法：</strong>在您的消费脚本中启动 booster 和定时器，网页后台保持暂停状态。
          </p>
          <div className="rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--sand))] p-3">
            <div className="mb-1 flex items-center gap-2 text-xs font-semibold text-[hsl(var(--ink))]">
              <Shield className="h-4 w-4" />
              不用担心重复执行！
            </div>
            <p className="text-xs text-[hsl(var(--ink-muted))]">
              Funboost 使用 <span className="rounded bg-[hsl(var(--line))] px-1">Redis 分布式锁</span>，
              即使 100 台机器部署也不会重复执行任务！
            </p>
          </div>
        </HelpSection>

        <HelpSection title="跨项目管理 —— 完爆传统方案！" icon={<Rocket className="h-4 w-4" />}>
          <p>
            <strong className="text-[hsl(var(--accent-2))]">🚀 Funboost Web Manager 可以管理任何项目的定时任务！</strong>
          </p>
          <p>
            管理定时任务 <strong>完全不依赖导入用户的任务函数</strong>，支持跨项目、跨仓库统一管理。
          </p>
        </HelpSection>
      </div>
    </Modal>
  );
}
