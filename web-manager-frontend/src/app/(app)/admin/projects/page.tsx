"use client";

import { useCallback, useEffect, useState } from "react";
import { CloudDownload, Edit2, FolderKanban, Plus, RefreshCw, Trash2, Users } from "lucide-react";
import { useRouter } from "next/navigation";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { apiFetch, funboostFetch } from "@/lib/api";
import { ProjectDialog, type ProjectFormData } from "./ProjectDialog";

// ============================================================================
// Types
// ============================================================================

type ProjectRow = {
  id: number;
  name: string;
  code: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
  user_count?: number;
};

// ============================================================================
// Constants
// ============================================================================

const statusToneMap: Record<string, "success" | "warning" | "danger" | "neutral"> = {
  active: "success",
  archived: "neutral",
};

const statusLabelMap: Record<string, string> = {
  active: "启用",
  archived: "已归档",
};

// ============================================================================
// Component
// ============================================================================

export default function AdminProjectsPage() {
  const router = useRouter();
  
  // 列表数据状态
  const [projects, setProjects] = useState<ProjectRow[]>([]);
  const [redisProjects, setRedisProjects] = useState<string[]>([]); // Redis 中的项目列表
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [notice, setNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  // 使用 useActionPermissions hook 获取操作权限
  const { canCreate, canUpdate, canDelete } = useActionPermissions("project");

  // 对话框状态
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingProject, setEditingProject] = useState<ProjectFormData | null>(null);
  
  // 同步状态
  const [syncing, setSyncing] = useState(false);

  // 判断项目是否有队列（在 Redis 中）
  const hasQueues = (projectCode: string): boolean => {
    return redisProjects.includes(projectCode);
  };

  // 打开创建对话框
  const openCreateDialog = () => {
    setEditingProject(null);
    setDialogOpen(true);
  };

  // 打开编辑对话框
  const openEditDialog = (project: ProjectRow) => {
    setEditingProject({
      id: project.id,
      name: project.name,
      code: project.code,
      description: project.description || "",
      status: project.status,
    });
    setDialogOpen(true);
  };

  // 关闭对话框
  const closeDialog = () => {
    setDialogOpen(false);
    setEditingProject(null);
  };

  // 对话框成功回调
  const handleDialogSuccess = (message: string) => {
    setNotice({ type: "success", message });
    loadProjects();
  };

  // 对话框错误回调
  const handleDialogError = (message: string) => {
    setNotice({ type: "error", message });
  };

  // 从 Redis 同步项目
  const handleSyncFromRedis = async () => {
    if (syncing) return;
    setSyncing(true);
    setNotice(null);
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
        if (created_count > 0) {
          setNotice({ type: "success", message: message || `同步完成：新建 ${created_count} 个项目` });
          loadProjects();
        } else {
          setNotice({ type: "success", message: message || `同步完成：无新项目，已存在 ${existing_count} 个项目` });
        }
      } else {
        throw new Error(response.error || "同步失败");
      }
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "同步失败" });
    } finally {
      setSyncing(false);
    }
  };

  // 加载 Redis 项目列表
  const loadRedisProjects = useCallback(async () => {
    try {
      const listData = await funboostFetch<{ project_names: string[] }>("/funboost/get_all_project_names");
      setRedisProjects(listData?.project_names || []);
    } catch (err) {
      console.error("Failed to load Redis projects:", err);
      setRedisProjects([]);
    }
  }, []);

  // 加载项目列表
  const loadProjects = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      const query = new URLSearchParams();
      query.set("page", String(page));
      query.set("page_size", String(pageSize));
      if (search) query.set("search", search);
      if (status) query.set("status", status);

      const response = await apiFetch<{
        success: boolean;
        data: {
          projects: ProjectRow[];
          page: number;
          page_size: number;
          total: number;
          total_pages: number;
        };
      }>(`/admin/api/projects?${query.toString()}`);

      if (response.success && response.data) {
        setProjects(response.data.projects);
        setTotal(response.data.total);
        setTotalPages(response.data.total_pages);
      }
      
      // 同时加载 Redis 项目列表
      await loadRedisProjects();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "加载项目失败。" });
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, status, loadRedisProjects]);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // 删除项目
  const handleDeleteProject = async (project: ProjectRow) => {
    // 前端再次检查：有队列的项目不能删除
    if (hasQueues(project.code)) {
      setNotice({ type: "error", message: `项目 "${project.name}" 有关联队列，不能删除！` });
      return;
    }
    
    const confirmMessage = `确定要删除项目 "${project.name}" 吗？`;
    if (!confirm(confirmMessage)) return;
    
    setNotice(null);
    try {
      const response = await apiFetch<{ 
        success: boolean; 
        error?: string;
        data?: { removed_user_count?: number };
      }>(`/admin/api/projects/${project.id}`, { method: "DELETE" });
      
      if (!response.success) {
        throw new Error(response.error || "删除失败");
      }
      
      const removedCount = response.data?.removed_user_count || 0;
      const message = removedCount > 0 
        ? `项目 "${project.name}" 已删除，同时移除了 ${removedCount} 个用户关联。`
        : `项目 "${project.name}" 已删除。`;
      setNotice({ type: "success", message });
      loadProjects();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "删除失败。";
      setNotice({ type: "error", message: errorMessage });
    }
  };

  // 格式化日期
  const formatDate = (dateStr: string) => {
    if (!dateStr) return "-";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("zh-CN", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <RequirePermission permissions={["project:read"]}>
      <div className="space-y-6">
        {/* 通知消息 - 浮动Toast */}
        {notice ? (
          <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
            <Card className={`shadow-lg max-w-md border-l-4 ${
              notice.type === "success"
                ? "border-l-green-500 bg-green-50 dark:bg-green-950/20"
                : "border-l-red-500 bg-red-50 dark:bg-red-950/20"
            }`}>
              <div className="flex items-start gap-3 p-4">
                <div className={`flex-shrink-0 ${notice.type === "success" ? "text-green-500" : "text-red-500"}`}>
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    {notice.type === "success" ? (
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    ) : (
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    )}
                  </svg>
                </div>
                <div className="flex-1">
                  <p className={`text-sm font-medium ${notice.type === "success" ? "text-green-800 dark:text-green-200" : "text-red-800 dark:text-red-200"}`}>
                    {notice.message}
                  </p>
                </div>
                <button 
                  onClick={() => setNotice(null)}
                  className={`flex-shrink-0 transition-colors ${notice.type === "success" ? "text-green-500 hover:text-green-700" : "text-red-500 hover:text-red-700"}`}
                >
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </Card>
          </div>
        ) : null}

        {/* 筛选和操作区域 */}
        <Card>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            {/* 左侧：筛选条件组 */}
            <div className="flex flex-1 items-center gap-2">
              <Input 
                placeholder="搜索项目名称或代码..." 
                value={search} 
                onChange={(e) => setSearch(e.target.value)} 
                className="flex-1 min-w-[200px]"
              />
              <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-28">
                <option value="">全部</option>
                <option value="active">启用</option>
                <option value="archived">已归档</option>
              </Select>
              <Button variant="primary" size="sm" onClick={loadProjects} className="cursor-pointer whitespace-nowrap">
                查询
              </Button>
            </div>
            
            {/* 右侧：操作按钮组 */}
            <div className="flex items-center gap-2 sm:border-l sm:border-[hsl(var(--line))] sm:pl-3">
              <span className="text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
                共 <span className="font-semibold text-[hsl(var(--ink))]">{total}</span> 个项目
              </span>
              <Button variant="outline" size="sm" onClick={loadProjects} className="cursor-pointer">
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              </Button>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleSyncFromRedis} 
                className="cursor-pointer whitespace-nowrap"
                disabled={syncing}
                title="从队列任务配置同步项目"
              >
                <CloudDownload className={`h-4 w-4 ${syncing ? "animate-pulse" : ""}`} />
                {syncing ? "同步中..." : "从队列同步"}
              </Button>
              {canCreate && (
                <Button size="sm" className="cursor-pointer whitespace-nowrap" onClick={openCreateDialog}>
                  <Plus className="h-4 w-4" />
                  创建项目
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* 项目表格 */}
        <Card>
          <div className="overflow-x-auto -mx-6 px-6">
            {loading ? (
              <div className="py-12 text-center">
                <RefreshCw className="h-8 w-8 mx-auto mb-3 animate-spin text-[hsl(var(--accent))]" />
                <p className="text-sm text-[hsl(var(--ink-muted))]">正在加载项目...</p>
              </div>
            ) : projects.length === 0 ? (
              <EmptyState title="暂无项目" subtitle="没有符合条件的项目。" />
            ) : (
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] border-b border-[hsl(var(--line))]">
                  <tr>
                    <th className="px-3 py-3 font-semibold">项目名称</th>
                    <th className="px-3 py-3 font-semibold">项目代码</th>
                    <th className="px-3 py-3 font-semibold">描述</th>
                    <th className="px-3 py-3 font-semibold">状态</th>
                    <th className="px-3 py-3 font-semibold">创建时间</th>
                    <th className="px-3 py-3 font-semibold text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--line))]">
                  {projects.map((project) => (
                    <tr key={project.id} className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors">
                      <td className="px-3 py-4">
                        <div className="flex items-center gap-2">
                          <FolderKanban className="h-4 w-4 text-[hsl(var(--accent))]" />
                          <span className="font-medium text-[hsl(var(--ink))]">{project.name}</span>
                          {hasQueues(project.code) && (
                            <Badge tone="info" className="text-xs">有队列</Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-4">
                        <Badge tone="info">{project.code}</Badge>
                      </td>
                      <td className="px-3 py-4 text-[hsl(var(--ink-muted))] text-xs max-w-xs truncate">
                        {project.description || "-"}
                      </td>
                      <td className="px-3 py-4">
                        <Badge tone={statusToneMap[project.status] || "neutral"}>
                          {statusLabelMap[project.status] ?? project.status}
                        </Badge>
                      </td>
                      <td className="px-3 py-4 text-xs text-[hsl(var(--ink-muted))]">
                        {formatDate(project.created_at)}
                      </td>
                      <td className="px-3 py-4">
                        <div className="flex justify-end gap-1.5">
                          <Button 
                            variant="outline" 
                            size="sm" 
                            className="cursor-pointer h-8 px-3"
                            onClick={() => router.push(`/admin/projects/${project.id}/users`)}
                            title="管理项目成员"
                          >
                            <Users className="h-3 w-3" />
                            成员
                          </Button>
                          {canUpdate && (
                            <Button 
                              variant="primary" 
                              size="sm" 
                              className="cursor-pointer h-8 px-3"
                              onClick={() => openEditDialog(project)}
                            >
                              <Edit2 className="h-3 w-3" />
                              编辑
                            </Button>
                          )}
                          {canDelete && (
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              onClick={() => handleDeleteProject(project)}
                              className="cursor-pointer h-8 px-2 text-[hsl(var(--danger))] hover:bg-[hsl(var(--danger))]/10 disabled:opacity-50 disabled:cursor-not-allowed"
                              disabled={project.code === "default" || hasQueues(project.code)}
                              title={
                                project.code === "default" 
                                  ? "默认项目不能删除" 
                                  : hasQueues(project.code)
                                  ? "有队列的项目不能删除"
                                  : "删除项目"
                              }
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
          {/* 分页 */}
          {totalPages > 1 && (
            <div className="mt-6 pt-4 border-t border-[hsl(var(--line))] flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-sm text-[hsl(var(--ink-muted))]">
                第 <span className="font-semibold text-[hsl(var(--ink))]">{page}</span> / <span className="font-semibold text-[hsl(var(--ink))]">{totalPages}</span> 页
              </span>
              <div className="flex gap-2">
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage((prev) => Math.max(prev - 1, 1))} 
                  disabled={page <= 1}
                  className="cursor-pointer"
                >
                  上一页
                </Button>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => setPage((prev) => Math.min(prev + 1, totalPages))} 
                  disabled={page >= totalPages}
                  className="cursor-pointer"
                >
                  下一页
                </Button>
              </div>
            </div>
          )}
        </Card>

        {/* 项目创建/编辑对话框 */}
        <ProjectDialog
          open={dialogOpen}
          onClose={closeDialog}
          onSuccess={handleDialogSuccess}
          onError={handleDialogError}
          project={editingProject}
        />
      </div>
    </RequirePermission>
  );
}
