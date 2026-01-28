"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { 
  ArrowLeft, 
  Edit2, 
  FolderKanban, 
  RefreshCw, 
  Trash2, 
  UserPlus, 
  Users,
  X,
  Save,
  AlertCircle
} from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { apiFetch } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

type Project = {
  id: number;
  name: string;
  code: string;
  description: string;
  status: string;
};

type ProjectUser = {
  id: number;
  user_id: number;
  username: string;
  email: string;
  permission_level: string;
  created_at: string;
};

type AvailableUser = {
  id: number;
  user_name: string;
  email: string;
};

// ============================================================================
// Constants
// ============================================================================

const permissionLevelToneMap: Record<string, "success" | "warning" | "info" | "neutral"> = {
  admin: "success",
  write: "info",
  read: "neutral",
};

const permissionLevelLabelMap: Record<string, string> = {
  admin: "管理员",
  write: "读写",
  read: "只读",
};

// ============================================================================
// Component
// ============================================================================

export default function ProjectUsersPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  // 项目信息状态
  const [project, setProject] = useState<Project | null>(null);
  const [projectLoading, setProjectLoading] = useState(true);

  // 用户列表状态
  const [users, setUsers] = useState<ProjectUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);

  // 添加用户对话框状态
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [availableUsers, setAvailableUsers] = useState<AvailableUser[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [selectedPermissionLevel, setSelectedPermissionLevel] = useState<string>("read");
  const [addLoading, setAddLoading] = useState(false);
  const [loadingAvailableUsers, setLoadingAvailableUsers] = useState(false);

  // 编辑权限对话框状态
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<ProjectUser | null>(null);
  const [editPermissionLevel, setEditPermissionLevel] = useState<string>("read");
  const [editLoading, setEditLoading] = useState(false);

  // 删除确认对话框状态
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deletingUser, setDeletingUser] = useState<ProjectUser | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // 加载项目信息
  const loadProject = useCallback(async () => {
    setProjectLoading(true);
    try {
      const response = await apiFetch<{
        success: boolean;
        data: { project: Project };
        error?: string;
      }>(`/admin/api/projects/${projectId}`);

      if (response.success && response.data) {
        setProject(response.data.project);
      } else {
        throw new Error(response.error || "加载项目失败");
      }
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "加载项目失败" });
    } finally {
      setProjectLoading(false);
    }
  }, [projectId]);

  // 加载项目用户列表
  const loadUsers = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      const response = await apiFetch<{
        success: boolean;
        data: { users: ProjectUser[] };
        error?: string;
      }>(`/admin/api/projects/${projectId}/users`);

      if (response.success && response.data) {
        setUsers(response.data.users);
      } else {
        throw new Error(response.error || "加载用户列表失败");
      }
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "加载用户列表失败" });
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  // 加载可添加的用户列表
  const loadAvailableUsers = useCallback(async () => {
    setLoadingAvailableUsers(true);
    try {
      // 获取所有用户
      const response = await apiFetch<{
        success: boolean;
        data: { users: AvailableUser[] };
      }>(`/admin/api/users?page_size=1000`);

      if (response.success && response.data) {
        // 过滤掉已经在项目中的用户
        const existingUserIds = new Set(users.map((u) => u.user_id));
        const available = response.data.users.filter(
          (u) => !existingUserIds.has(u.id)
        );
        setAvailableUsers(available);
      }
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "加载用户列表失败" });
    } finally {
      setLoadingAvailableUsers(false);
    }
  }, [users]);

  // 初始加载
  useEffect(() => {
    loadProject();
    loadUsers();
  }, [loadProject, loadUsers]);

  // 打开添加用户对话框
  const openAddDialog = () => {
    setSelectedUserId("");
    setSelectedPermissionLevel("read");
    setAddDialogOpen(true);
    loadAvailableUsers();
  };

  // 关闭添加用户对话框
  const closeAddDialog = () => {
    setAddDialogOpen(false);
    setSelectedUserId("");
    setSelectedPermissionLevel("read");
  };

  // 添加用户到项目
  const handleAddUser = async () => {
    if (!selectedUserId) {
      setNotice({ type: "error", message: "请选择要添加的用户" });
      return;
    }

    setAddLoading(true);
    try {
      const response = await apiFetch<{ success: boolean; error?: string }>(
        `/admin/api/projects/${projectId}/users`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_id: parseInt(selectedUserId),
            permission_level: selectedPermissionLevel,
          }),
        }
      );

      if (!response.success) {
        throw new Error(response.error || "添加用户失败");
      }

      setNotice({ type: "success", message: "用户添加成功" });
      closeAddDialog();
      loadUsers();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "添加用户失败" });
    } finally {
      setAddLoading(false);
    }
  };

  // 打开编辑权限对话框
  const openEditDialog = (user: ProjectUser) => {
    setEditingUser(user);
    setEditPermissionLevel(user.permission_level);
    setEditDialogOpen(true);
  };

  // 关闭编辑权限对话框
  const closeEditDialog = () => {
    setEditDialogOpen(false);
    setEditingUser(null);
    setEditPermissionLevel("read");
  };

  // 更新用户权限
  const handleUpdatePermission = async () => {
    if (!editingUser) return;

    setEditLoading(true);
    try {
      const response = await apiFetch<{ success: boolean; error?: string }>(
        `/admin/api/projects/${projectId}/users/${editingUser.user_id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            permission_level: editPermissionLevel,
          }),
        }
      );

      if (!response.success) {
        throw new Error(response.error || "更新权限失败");
      }

      setNotice({ type: "success", message: `用户 "${editingUser.username}" 的权限已更新` });
      closeEditDialog();
      loadUsers();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "更新权限失败" });
    } finally {
      setEditLoading(false);
    }
  };

  // 打开删除确认对话框
  const openDeleteDialog = (user: ProjectUser) => {
    setDeletingUser(user);
    setDeleteDialogOpen(true);
  };

  // 关闭删除确认对话框
  const closeDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setDeletingUser(null);
  };

  // 从项目移除用户
  const handleRemoveUser = async () => {
    if (!deletingUser) return;

    setDeleteLoading(true);
    try {
      const response = await apiFetch<{ success: boolean; error?: string }>(
        `/admin/api/projects/${projectId}/users/${deletingUser.user_id}`,
        { method: "DELETE" }
      );

      if (!response.success) {
        throw new Error(response.error || "移除用户失败");
      }

      setNotice({ type: "success", message: `用户 "${deletingUser.username}" 已从项目中移除` });
      closeDeleteDialog();
      loadUsers();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "移除用户失败" });
    } finally {
      setDeleteLoading(false);
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
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return dateStr;
    }
  };

  // 返回项目列表
  const handleBack = () => {
    router.push("/admin/projects");
  };

  return (
    <RequirePermission permissions={["project:admin"]}>
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

        {/* 项目信息头部 */}
        <Card>
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleBack}
                className="cursor-pointer"
              >
                <ArrowLeft className="h-4 w-4" />
                返回
              </Button>
              {projectLoading ? (
                <div className="flex items-center gap-2">
                  <RefreshCw className="h-4 w-4 animate-spin text-[hsl(var(--accent))]" />
                  <span className="text-sm text-[hsl(var(--ink-muted))]">加载项目信息...</span>
                </div>
              ) : project ? (
                <div className="flex items-center gap-3">
                  <FolderKanban className="h-5 w-5 text-[hsl(var(--accent))]" />
                  <div>
                    <h1 className="font-display text-lg text-[hsl(var(--ink))]">{project.name}</h1>
                    <p className="text-xs text-[hsl(var(--ink-muted))]">
                      项目代码: <Badge tone="info">{project.code}</Badge>
                      {project.description && <span className="ml-2">· {project.description}</span>}
                    </p>
                  </div>
                </div>
              ) : (
                <span className="text-sm text-[hsl(var(--danger))]">项目不存在</span>
              )}
            </div>
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-[hsl(var(--ink-muted))]" />
              <span className="text-sm text-[hsl(var(--ink-muted))]">
                项目成员管理
              </span>
            </div>
          </div>
        </Card>

        {/* 操作区域 */}
        <Card>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <span className="text-xs text-[hsl(var(--ink-muted))]">
                共 <span className="font-semibold text-[hsl(var(--ink))]">{users.length}</span> 名成员
              </span>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                onClick={loadUsers} 
                className="cursor-pointer"
              >
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              </Button>
              <Button 
                size="sm" 
                className="cursor-pointer whitespace-nowrap" 
                onClick={openAddDialog}
              >
                <UserPlus className="h-4 w-4" />
                添加用户
              </Button>
            </div>
          </div>
        </Card>

        {/* 用户列表表格 */}
        <Card>
          <div className="overflow-x-auto -mx-6 px-6">
            {loading ? (
              <div className="py-12 text-center">
                <RefreshCw className="h-8 w-8 mx-auto mb-3 animate-spin text-[hsl(var(--accent))]" />
                <p className="text-sm text-[hsl(var(--ink-muted))]">正在加载用户...</p>
              </div>
            ) : users.length === 0 ? (
              <EmptyState 
                title="暂无成员" 
                subtitle="该项目还没有添加任何成员，点击上方按钮添加用户。" 
              />
            ) : (
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] border-b border-[hsl(var(--line))]">
                  <tr>
                    <th className="px-3 py-3 font-semibold">用户名</th>
                    <th className="px-3 py-3 font-semibold">邮箱</th>
                    <th className="px-3 py-3 font-semibold">权限级别</th>
                    <th className="px-3 py-3 font-semibold">添加时间</th>
                    <th className="px-3 py-3 font-semibold text-right">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--line))]">
                  {users.map((user) => (
                    <tr key={user.id} className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors">
                      <td className="px-3 py-4 font-medium text-[hsl(var(--ink))]">
                        {user.username}
                      </td>
                      <td className="px-3 py-4 text-[hsl(var(--ink-muted))] text-xs">
                        {user.email || "-"}
                      </td>
                      <td className="px-3 py-4">
                        <Badge tone={permissionLevelToneMap[user.permission_level] || "neutral"}>
                          {permissionLevelLabelMap[user.permission_level] || user.permission_level}
                        </Badge>
                      </td>
                      <td className="px-3 py-4 text-xs text-[hsl(var(--ink-muted))]">
                        {formatDate(user.created_at)}
                      </td>
                      <td className="px-3 py-4">
                        <div className="flex justify-end gap-1.5">
                          <Button 
                            variant="primary" 
                            size="sm" 
                            className="cursor-pointer h-8 px-3"
                            onClick={() => openEditDialog(user)}
                          >
                            <Edit2 className="h-3 w-3" />
                            编辑权限
                          </Button>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => openDeleteDialog(user)}
                            className="cursor-pointer h-8 px-2 text-[hsl(var(--danger))] hover:bg-[hsl(var(--danger))]/10"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </Card>

        {/* 添加用户对话框 */}
        <Modal
          open={addDialogOpen}
          title="添加用户到项目"
          onClose={closeAddDialog}
          size="md"
          footer={
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={closeAddDialog}
                disabled={addLoading}
                className="cursor-pointer"
              >
                <X className="h-4 w-4" />
                取消
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleAddUser}
                disabled={addLoading || !selectedUserId}
                className="cursor-pointer"
              >
                {addLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    添加中...
                  </>
                ) : (
                  <>
                    <UserPlus className="h-4 w-4" />
                    添加用户
                  </>
                )}
              </Button>
            </div>
          }
        >
          <div className="space-y-5">
            {/* 选择用户 */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                选择用户 <span className="text-[hsl(var(--danger))]">*</span>
              </label>
              {loadingAvailableUsers ? (
                <div className="flex items-center gap-2 py-2">
                  <RefreshCw className="h-4 w-4 animate-spin text-[hsl(var(--accent))]" />
                  <span className="text-sm text-[hsl(var(--ink-muted))]">加载用户列表...</span>
                </div>
              ) : availableUsers.length === 0 ? (
                <div className="flex items-center gap-2 py-2 text-[hsl(var(--warning))]">
                  <AlertCircle className="h-4 w-4" />
                  <span className="text-sm">没有可添加的用户，所有用户都已在项目中</span>
                </div>
              ) : (
                <Select
                  value={selectedUserId}
                  onChange={(e) => setSelectedUserId(e.target.value)}
                >
                  <option value="">请选择用户...</option>
                  {availableUsers.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.user_name} {user.email ? `(${user.email})` : ""}
                    </option>
                  ))}
                </Select>
              )}
            </div>

            {/* 选择权限级别 */}
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                权限级别 <span className="text-[hsl(var(--danger))]">*</span>
              </label>
              <Select
                value={selectedPermissionLevel}
                onChange={(e) => setSelectedPermissionLevel(e.target.value)}
              >
                <option value="read">只读 - 只能查看项目数据</option>
                <option value="write">读写 - 可以查看和操作项目数据</option>
                <option value="admin">管理员 - 完全控制项目</option>
              </Select>
              <p className="text-xs text-[hsl(var(--ink-muted))]">
                权限级别决定用户在该项目中可以执行的操作
              </p>
            </div>
          </div>
        </Modal>

        {/* 编辑权限对话框 */}
        <Modal
          open={editDialogOpen}
          title={`编辑用户权限: ${editingUser?.username ?? ""}`}
          onClose={closeEditDialog}
          size="sm"
          footer={
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={closeEditDialog}
                disabled={editLoading}
                className="cursor-pointer"
              >
                <X className="h-4 w-4" />
                取消
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleUpdatePermission}
                disabled={editLoading}
                className="cursor-pointer"
              >
                {editLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    保存修改
                  </>
                )}
              </Button>
            </div>
          }
        >
          <div className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                权限级别
              </label>
              <Select
                value={editPermissionLevel}
                onChange={(e) => setEditPermissionLevel(e.target.value)}
              >
                <option value="read">只读 - 只能查看项目数据</option>
                <option value="write">读写 - 可以查看和操作项目数据</option>
                <option value="admin">管理员 - 完全控制项目</option>
              </Select>
              <p className="text-xs text-[hsl(var(--ink-muted))]">
                修改后用户的权限将立即生效
              </p>
            </div>
          </div>
        </Modal>

        {/* 删除确认对话框 */}
        <Modal
          open={deleteDialogOpen}
          title="确认移除用户"
          onClose={closeDeleteDialog}
          size="sm"
          footer={
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={closeDeleteDialog}
                disabled={deleteLoading}
                className="cursor-pointer"
              >
                取消
              </Button>
              <Button
                variant="primary"
                size="sm"
                onClick={handleRemoveUser}
                disabled={deleteLoading}
                className="cursor-pointer bg-[hsl(var(--danger))] hover:bg-[hsl(var(--danger))]/90"
              >
                {deleteLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    移除中...
                  </>
                ) : (
                  <>
                    <Trash2 className="h-4 w-4" />
                    确认移除
                  </>
                )}
              </Button>
            </div>
          }
        >
          {deletingUser && (
            <div className="space-y-4">
              <p className="text-[hsl(var(--ink))]">
                确定要将用户 <strong>{deletingUser.username}</strong> 从项目中移除吗？
              </p>
              <div className="rounded-xl bg-[hsl(var(--sand-2))] p-4">
                <p className="text-sm text-[hsl(var(--ink-muted))]">
                  移除后，该用户将无法访问此项目的任何数据。此操作可以撤销（重新添加用户）。
                </p>
              </div>
            </div>
          )}
        </Modal>
      </div>
    </RequirePermission>
  );
}
