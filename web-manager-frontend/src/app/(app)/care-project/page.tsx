"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, CloudDownload, Layers, RefreshCw, Square, CheckSquare, Trash2, AlertTriangle } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { funboostFetch, apiFetch } from "@/lib/api";
import { useActionPermissions } from "@/hooks/useActionPermissions";

type ProjectInfo = {
  id: number;
  code: string;
  name: string;
  description?: string;
  status?: string;
};

export default function CareProjectPage() {
  const [current, setCurrent] = useState("");
  const [projects, setProjects] = useState<string[]>([]);
  const [dbProjects, setDbProjects] = useState<ProjectInfo[]>([]);
  const [status, setStatus] = useState<{ type: "success" | "error" | "info"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [mounted, setMounted] = useState(false);
  // 标记 Redis 项目是否加载成功
  const [redisLoaded, setRedisLoaded] = useState(false);
  const [redisError, setRedisError] = useState<string | null>(null);

  // 多选删除相关状态
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [deleting, setDeleting] = useState(false);

  const { canDelete } = useActionPermissions("project");

  // 解决 hydration 问题
  useEffect(() => {
    setMounted(true);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setRedisLoaded(false);
    setRedisError(null);
    try {
      const currentData = await funboostFetch<{ care_project_name?: string }>("/funboost/get_care_project_name", {
        cache: "no-store",
      });
      setCurrent(currentData?.care_project_name || "");

      // 加载 Redis 中的项目列表
      try {
        const listData = await funboostFetch<{ project_names: string[] }>("/funboost/get_all_project_names", {
          cache: "no-store",
        });
        const redisProjects = listData?.project_names || [];
        setProjects(redisProjects);
        setRedisLoaded(true);
        console.log("[CareProject] Redis projects loaded:", redisProjects);
      } catch (err) {
        console.error("[CareProject] Failed to load Redis projects:", err);
        setProjects([]);
        setRedisError(err instanceof Error ? err.message : "无法连接 Redis");
        // 即使 Redis 加载失败，也标记为已加载（空列表）
        setRedisLoaded(true);
      }

      // 加载用户授权的数据库项目（使用用户 API 而非管理员 API）
      const dbData = await apiFetch<{
        success: boolean;
        data?: { projects: ProjectInfo[] };
      }>("/api/user/projects", { cache: "no-store" });
      if (dbData.success && dbData.data) {
        setDbProjects(dbData.data.projects);
        console.log("[CareProject] User authorized DB projects loaded:", dbData.data.projects.map(p => p.code));
      }
    } catch (err) {
      setStatus({ type: "error", message: err instanceof Error ? err.message : "加载项目失败。" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleSelect = async (name: string) => {
    if (selectMode) return; // 选择模式下不切换项目
    setStatus(null);
    try {
      await funboostFetch("/funboost/set_care_project_name", {
        method: "POST",
        json: { care_project_name: name },
      });
      setCurrent(name);
      setStatus({ type: "success", message: name ? `已切换到项目: ${name}` : "已切换到全部项目" });
      
      // 通知全局状态刷新显示
      if (typeof window !== "undefined") {
        window.dispatchEvent(
          new CustomEvent("careProjectChanged", { detail: { careProjectName: name } })
        );
      }
    } catch (err) {
      setStatus({ type: "error", message: err instanceof Error ? err.message : "更新失败。" });
    }
  };

  // 从 Redis 同步项目到数据库
  const handleSyncToDatabase = async () => {
    if (syncing) return;
    setSyncing(true);
    setStatus(null);
    try {
      const response = await apiFetch<{
        success: boolean;
        data?: {
          created_count: number;
          existing_count: number;
          message: string;
        };
        error?: string;
      }>("/admin/api/projects/sync", { method: "POST" });

      if (response.success && response.data) {
        const { created_count, existing_count, message } = response.data;
        setStatus({
          type: "success",
          message: message || `同步完成：新建 ${created_count} 个项目，已存在 ${existing_count} 个项目`
        });
        await load();
      } else {
        throw new Error(response.error || "同步失败");
      }
    } catch (err) {
      setStatus({ type: "error", message: err instanceof Error ? err.message : "同步失败" });
    } finally {
      setSyncing(false);
    }
  };

  // 切换选择模式
  const toggleSelectMode = () => {
    if (!selectMode) {
      // 进入选择模式前检查 Redis 数据是否已加载
      if (!redisLoaded) {
        setStatus({ type: "error", message: "请等待数据加载完成后再进行删除操作" });
        return;
      }
      if (redisError) {
        setStatus({ type: "error", message: `无法进入删除模式：${redisError}。请刷新页面重试。` });
        return;
      }
    }
    setSelectMode(!selectMode);
    setSelectedIds(new Set());
  };

  // 切换单个项目选择
  const toggleProjectSelection = (projectId: number) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(projectId)) {
      newSelected.delete(projectId);
    } else {
      newSelected.add(projectId);
    }
    setSelectedIds(newSelected);
  };

  // 获取项目的数据库 ID
  const getProjectId = (projectCode: string): number | null => {
    const dbProject = dbProjects.find(p => p.code === projectCode);
    return dbProject?.id || null;
  };

  // 判断项目是否在 Redis 中有队列（如果在 projects 列表中说明有队列）
  const hasQueues = (projectCode: string): boolean => {
    return projects.includes(projectCode);
  };

  // 获取可删除的项目（在数据库中但不在 Redis 中，即没有队列的项目）
  const getEmptyProjects = (): ProjectInfo[] => {
    const empty = dbProjects.filter(p =>
      p.code !== 'default' && // 排除默认项目
      !projects.includes(p.code) // 不在 Redis 中（没有队列）
    );
    console.log("[CareProject] Empty projects (can delete):", empty.map(p => p.code));
    return empty;
  };

  // 全选空项目
  const selectAllEmpty = () => {
    const emptyProjects = getEmptyProjects();
    setSelectedIds(new Set(emptyProjects.map(p => p.id)));
  };

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedIds.size === 0) return;

    const confirmMsg = `确定要删除选中的 ${selectedIds.size} 个项目吗？\n此操作不可撤销！`;
    if (!confirm(confirmMsg)) return;

    setDeleting(true);
    setStatus(null);

    try {
      const response = await apiFetch<{
        success: boolean;
        data?: {
          deleted_count: number;
          failed_count: number;
          failed_projects: { id: number; name: string; error: string }[];
        };
        error?: string;
      }>("/admin/api/projects/batch-delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ project_ids: Array.from(selectedIds) }),
      });

      if (response.success && response.data) {
        const { deleted_count, failed_count, failed_projects } = response.data;

        if (failed_count > 0) {
          const failedNames = failed_projects.map(p => `${p.name}: ${p.error}`).join('\n');
          setStatus({
            type: "info",
            message: `删除完成：成功 ${deleted_count} 个，失败 ${failed_count} 个\n${failedNames}`
          });
        } else {
          setStatus({ type: "success", message: `成功删除 ${deleted_count} 个项目` });
        }

        setSelectMode(false);
        setSelectedIds(new Set());
        await load();
      } else {
        throw new Error(response.error || "删除失败");
      }
    } catch (err) {
      setStatus({ type: "error", message: err instanceof Error ? err.message : "删除失败" });
    } finally {
      setDeleting(false);
    }
  };

  const emptyProjects = getEmptyProjects();

  return (
    <>
      <div className="space-y-8">
        <SectionHeader
          title="关注项目"
          subtitle="限定监控范围到指定项目。"
          actions={
            <div className="flex items-center gap-2">
              {mounted && canDelete && (
                <Button
                  variant={selectMode ? "primary" : "outline"}
                  size="sm"
                  onClick={toggleSelectMode}
                  disabled={!redisLoaded || loading}
                  title={!redisLoaded ? "等待数据加载..." : redisError ? "Redis 连接失败" : "多选删除空项目"}
                >
                  {selectMode ? <CheckSquare className="h-4 w-4" /> : <Square className="h-4 w-4" />}
                  {selectMode ? "取消选择" : "多选删除"}
                </Button>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={handleSyncToDatabase}
                disabled={syncing || selectMode}
                title="将 Redis 中的项目同步到数据库"
              >
                <CloudDownload className={`h-4 w-4 ${syncing ? "animate-pulse" : ""}`} />
                {syncing ? "同步中..." : "同步到数据库"}
              </Button>
              <Button variant="outline" size="sm" onClick={load} disabled={loading || selectMode}>
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                刷新
              </Button>
            </div>
          }
        />

        {status ? (
          <Card className={`border text-sm whitespace-pre-wrap ${status.type === "success"
            ? "border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10 text-[hsl(var(--success))]"
            : status.type === "error"
              ? "border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 text-[hsl(var(--danger))]"
              : "border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-[hsl(var(--accent-2))]"
            }`}>
            {status.message}
          </Card>
        ) : null}

        {/* Redis 加载错误警告 */}
        {redisError && !status && (
          <Card className="border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10">
            <div className="flex items-center gap-2 text-sm text-[hsl(var(--warning))]">
              <AlertTriangle className="h-4 w-4" />
              <span>Redis 连接失败：{redisError}。删除功能可能不可用。</span>
            </div>
          </Card>
        )}

        {/* 选择模式操作栏 */}
        {selectMode && (
          <Card className="border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-5 w-5 text-[hsl(var(--warning))]" />
                <span className="text-sm font-medium text-[hsl(var(--ink))]">
                  已选择 {selectedIds.size} 个项目
                </span>
                {emptyProjects.length > 0 && (
                  <Button variant="outline" size="sm" onClick={selectAllEmpty}>
                    全选空项目 ({emptyProjects.length})
                  </Button>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSelectedIds(new Set())}
                  disabled={selectedIds.size === 0}
                >
                  清除选择
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleBatchDelete}
                  disabled={selectedIds.size === 0 || deleting}
                  className="bg-[hsl(var(--danger))] hover:bg-[hsl(var(--danger))]/90"
                >
                  <Trash2 className={`h-4 w-4 ${deleting ? "animate-pulse" : ""}`} />
                  {deleting ? "删除中..." : `删除 (${selectedIds.size})`}
                </Button>
              </div>
            </div>
            <p className="mt-2 text-xs text-[hsl(var(--ink-muted))]">
              提示：只能删除空项目（没有队列的项目）。有队列的项目显示为灰色，不可选择。默认项目不可删除。
            </p>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-2">
          <Card>
            <SectionHeader title="当前范围" subtitle="应用于所有监控页面。" />
            <div className="mt-4 flex items-center gap-3">
              <Badge tone={current ? "info" : "neutral"}>{current || "全部项目"}</Badge>
              <span className="text-sm text-[hsl(var(--ink-muted))]">
                {current ? "已启用项目筛选" : "显示所有项目数据"}
              </span>
            </div>
          </Card>
          <Card>
            <SectionHeader title="快捷操作" subtitle="一键切换为全部项目。" />
            <div className="mt-4 flex items-center gap-2">
              <Button
                variant={current ? "primary" : "outline"}
                size="sm"
                onClick={() => handleSelect("")}
                disabled={!current || selectMode}
              >
                清除筛选
              </Button>
              {current && (
                <span className="text-xs text-[hsl(var(--ink-muted))]">
                  当前筛选: {current}
                </span>
              )}
            </div>
          </Card>
        </div>

        <Card>
          <SectionHeader
            title="可选项目"
            subtitle={`共 ${projects.length} 个 Redis 项目，${dbProjects.length} 个数据库项目。项目来源于队列任务配置中的 project_name 参数。`}
          />
          {loading ? (
            <div className="mt-6 flex items-center justify-center py-8">
              <RefreshCw className="h-6 w-6 animate-spin text-[hsl(var(--accent))]" />
              <span className="ml-2 text-sm text-[hsl(var(--ink-muted))]">加载中...</span>
            </div>
          ) : projects.length === 0 && dbProjects.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-[hsl(var(--line))] bg-[hsl(var(--sand-2))]/50 px-6 py-8 text-center">
              <Layers className="mx-auto h-8 w-8 text-[hsl(var(--ink-muted))]" />
              <p className="mt-3 text-sm font-medium text-[hsl(var(--ink))]">暂无项目</p>
              <p className="mt-1 text-xs text-[hsl(var(--ink-muted))]">
                在队列任务的 @boost 装饰器中配置 project_name 参数后，项目会自动出现在这里。
              </p>
            </div>
          ) : (
            <div className="mt-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {/* 全部项目选项 */}
              {!selectMode && (
                <button
                  onClick={() => handleSelect("")}
                  className={`flex items-center justify-between rounded-2xl border px-4 py-3 text-left transition ${!current
                    ? "border-[hsl(var(--accent-2))] bg-[hsl(var(--accent-2))]/10"
                    : "border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 hover:border-[hsl(var(--accent))]"
                    }`}
                >
                  <div>
                    <p className="font-semibold text-[hsl(var(--ink))]">全部项目</p>
                    <p className="text-xs text-[hsl(var(--ink-muted))]">显示所有队列数据</p>
                  </div>
                  {!current ? <CheckCircle2 className="h-4 w-4 text-[hsl(var(--accent-2))]" /> : null}
                </button>
              )}

              {/* 项目列表 - 只显示用户授权的项目 */}
              {(() => {
                // 只显示用户有权限的项目（排除默认项目）
                const visibleCodes = dbProjects
                  .map(p => p.code)
                  .filter(code => code !== 'default');

                return visibleCodes.map((code) => {
                  const selected = current === code;
                  const projectId = getProjectId(code);
                  const hasQueue = hasQueues(code);
                  const isSelected = projectId ? selectedIds.has(projectId) : false;
                  const canSelect = selectMode && projectId && !hasQueue;

                  return (
                    <button
                      key={code}
                      onClick={() => {
                        if (selectMode) {
                          if (canSelect && projectId) {
                            toggleProjectSelection(projectId);
                          }
                        } else {
                          handleSelect(code);
                        }
                      }}
                      disabled={selectMode && !canSelect}
                      className={`flex items-center justify-between rounded-2xl border px-4 py-3 text-left transition ${selectMode
                        ? canSelect
                          ? isSelected
                            ? "border-[hsl(var(--danger))] bg-[hsl(var(--danger))]/10"
                            : "border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 hover:border-[hsl(var(--danger))]/50"
                          : "border-[hsl(var(--line))]/50 bg-[hsl(var(--sand-2))]/30 opacity-50 cursor-not-allowed"
                        : selected
                          ? "border-[hsl(var(--accent-2))] bg-[hsl(var(--accent-2))]/10"
                          : "border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 hover:border-[hsl(var(--accent))]"
                        }`}
                    >
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-semibold text-[hsl(var(--ink))] truncate">{code}</p>
                          {!hasQueue && (
                            <Badge tone="warning" className="text-xs">空</Badge>
                          )}
                          {!projectId && (
                            <Badge tone="neutral" className="text-xs">未同步</Badge>
                          )}
                        </div>
                        <p className="text-xs text-[hsl(var(--ink-muted))]">
                          {selectMode
                            ? (hasQueue ? "有队列，不可删除" : "可删除")
                            : "点击切换"
                          }
                        </p>
                      </div>
                      {selectMode ? (
                        canSelect ? (
                          isSelected ? (
                            <CheckSquare className="h-4 w-4 text-[hsl(var(--danger))]" />
                          ) : (
                            <Square className="h-4 w-4 text-[hsl(var(--ink-muted))]" />
                          )
                        ) : null
                      ) : (
                        selected ? <CheckCircle2 className="h-4 w-4 text-[hsl(var(--accent-2))]" /> : null
                      )}
                    </button>
                  );
                });
              })()}
            </div>
          )}
        </Card>

        {/* 说明卡片 */}
        <Card className="bg-[hsl(var(--sand-2))]/50">
          <SectionHeader title="使用说明" subtitle="关于项目筛选功能。" />
          <div className="mt-4 space-y-3 text-sm text-[hsl(var(--ink-muted))]">
            <p>
              <strong className="text-[hsl(var(--ink))]">项目来源：</strong>
              项目名称来自队列任务配置中的 <code className="rounded bg-[hsl(var(--card))] px-1.5 py-0.5 text-xs">project_name</code> 参数。
            </p>
            <p>
              <strong className="text-[hsl(var(--ink))]">筛选范围：</strong>
              选择项目后，队列运维、消费速率、运行中消费者等页面将只显示该项目的数据。
            </p>
            <p>
              <strong className="text-[hsl(var(--ink))]">同步到数据库：</strong>
              点击"同步到数据库"按钮可将 Redis 中的项目同步到数据库，用于项目管理和权限分配。
            </p>
            <p>
              <strong className="text-[hsl(var(--ink))]">删除空项目：</strong>
              点击"多选删除"可以批量删除没有队列的空项目。有队列的项目不可删除。
            </p>
          </div>
        </Card>
      </div>
    </>
  );
}
