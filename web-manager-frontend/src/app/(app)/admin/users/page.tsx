"use client";

import { useCallback, useEffect, useState } from "react";
import { Lock, RefreshCw, UserPlus, Save, Edit2, Trash2, Download } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { PermissionGuard } from "@/components/auth/PermissionGuard";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Select } from "@/components/ui/Select";
import { StaticLink } from "@/components/ui/StaticLink";
import { apiFetch } from "@/lib/api";

const statusToneMap: Record<string, "success" | "warning" | "danger" | "neutral"> = {
  active: "success",
  disabled: "danger",
  locked: "warning",
};
const statusLabelMap: Record<string, string> = {
  active: "启用",
  disabled: "禁用",
  locked: "锁定",
};

type ProjectInfo = {
  project_id: number;
  project_name: string;
  project_code: string;
  permission_level: string;
};

type UserRow = {
  user_name: string;
  email: string;
  status: string;
  roles: string[];
  locked_until: string;
  projects: ProjectInfo[];
};

type RoleOption = {
  name: string;
  checked: boolean;
};

export default function AdminUsersPage() {
  const [users, setUsers] = useState<UserRow[]>([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [notice, setNotice] = useState<{ type: "success" | "error"; message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  // 使用 useActionPermissions hook 获取操作权限
  const { canCreate, canUpdate, canDelete, canExport } = useActionPermissions("user");

  // 编辑用户 Modal 状态
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<UserRow | null>(null);
  const [editEmail, setEditEmail] = useState("");
  const [editStatus, setEditStatus] = useState("active");
  const [editRoles, setEditRoles] = useState<RoleOption[]>([]);
  const [editLoading, setEditLoading] = useState(false);

  // 可用角色列表
  const [availableRoles, setAvailableRoles] = useState<string[]>([]);

  // 重置密码 Modal
  const [resetPasswordModal, setResetPasswordModal] = useState<{ userName: string; newPassword: string } | null>(null);

  const loadUsers = useCallback(async () => {
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
          users: UserRow[];
          page: number;
          page_size: number;
          total: number;
          total_pages: number;
        };
      }>(`/admin/api/users?${query.toString()}`);

      if (response.success && response.data) {
        setUsers(response.data.users);
        setTotal(response.data.total);
        setTotalPages(response.data.total_pages);
      }
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "加载用户失败。" });
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, search, status]);

  const loadRoles = useCallback(async () => {
    try {
      const response = await apiFetch<{ success: boolean; data: { roles: { name: string }[] } }>("/admin/api/roles");
      if (response.success && response.data) {
        setAvailableRoles(response.data.roles.map((r) => r.name));
      }
    } catch {
      setAvailableRoles(["admin", "user", "viewer"]);
    }
  }, []);

  useEffect(() => {
    loadUsers();
    loadRoles();
  }, [loadUsers, loadRoles]);

  // 切换用户状态（点击状态 Badge）
  const handleToggleStatus = async (userName: string) => {
    setNotice(null);
    try {
      const response = await apiFetch<{ success: boolean; error?: string; new_status?: string }>(
        `/admin/users/${userName}/toggle_status`,
        { method: "POST", headers: { "Content-Type": "application/json" } }
      );
      if (!response.success) {
        throw new Error(response.error || "操作失败");
      }
      setNotice({ type: "success", message: `状态已切换为 ${statusLabelMap[response.new_status || ""] || response.new_status}` });
      loadUsers();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "操作失败。" });
    }
  };

  // 重置密码
  const handleResetPassword = async (userName: string) => {
    if (!confirm(`确定要重置用户 ${userName} 的密码吗？`)) return;
    setNotice(null);
    try {
      const response = await apiFetch<{ success: boolean; error?: string; new_password?: string }>(
        `/admin/users/${userName}/reset_password`,
        { method: "POST", headers: { "Content-Type": "application/json" } }
      );
      if (!response.success) {
        throw new Error(response.error || "重置密码失败");
      }
      if (response.new_password) {
        setResetPasswordModal({ userName, newPassword: response.new_password });
      } else {
        setNotice({ type: "success", message: "密码已重置。" });
      }
      loadUsers();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "重置密码失败。" });
    }
  };

  // 删除用户
  const handleDeleteUser = async (userName: string) => {
    if (!confirm(`确定要删除用户 ${userName} 吗？此操作不可撤销！`)) return;
    setNotice(null);
    try {
      const response = await apiFetch<{ success: boolean; error?: string }>(
        `/admin/users/${userName}/delete`,
        { method: "DELETE", headers: { "Content-Type": "application/json" } }
      );
      if (!response.success) {
        throw new Error(response.error || "删除失败");
      }
      setNotice({ type: "success", message: `用户 ${userName} 已删除。` });
      loadUsers();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "删除失败。" });
    }
  };

  // 打开编辑 Modal
  const openEditModal = (user: UserRow) => {
    setEditingUser(user);
    setEditEmail(user.email || "");
    setEditStatus(user.status);
    setEditRoles(
      availableRoles.map((role) => ({
        name: role,
        checked: user.roles.includes(role),
      }))
    );
    setEditModalOpen(true);
  };

  // 关闭编辑 Modal
  const closeEditModal = () => {
    setEditModalOpen(false);
    setEditingUser(null);
  };

  // 保存编辑 - 使用 JSON API
  const handleEditSubmit = async () => {
    if (!editingUser) return;
    setEditLoading(true);
    try {
      const response = await apiFetch<{ success: boolean; error?: string; message?: string }>(
        `/admin/api/users/${editingUser.user_name}/edit`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: editEmail,
            status: editStatus,
            roles: editRoles.filter((r) => r.checked).map((r) => r.name),
          }),
        }
      );

      if (!response.success) {
        throw new Error(response.error || "更新失败");
      }

      setNotice({ type: "success", message: response.message || "用户信息已更新。" });
      closeEditModal();
      loadUsers();
    } catch (err) {
      setNotice({ type: "error", message: err instanceof Error ? err.message : "更新失败。" });
    } finally {
      setEditLoading(false);
    }
  };

  return (
    <RequirePermission permissions={["user:read"]}>
    <div className="space-y-6">
      {/* 通知消息 - 改为浮动Toast */}
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
              placeholder="搜索用户名或邮箱..." 
              value={search} 
              onChange={(e) => setSearch(e.target.value)} 
              className="flex-1 min-w-[200px]"
            />
            <Select value={status} onChange={(e) => setStatus(e.target.value)} className="w-28">
              <option value="">全部</option>
              <option value="active">启用</option>
              <option value="disabled">禁用</option>
              <option value="locked">锁定</option>
            </Select>
            <Button variant="primary" size="sm" onClick={loadUsers} className="cursor-pointer whitespace-nowrap">
              查询
            </Button>
          </div>
          
          {/* 右侧：操作按钮组 */}
          <div className="flex items-center gap-2 sm:border-l sm:border-[hsl(var(--line))] sm:pl-3">
            <span className="text-xs text-[hsl(var(--ink-muted))] whitespace-nowrap">
              共 <span className="font-semibold text-[hsl(var(--ink))]">{total}</span> 人
            </span>
            <Button variant="outline" size="sm" onClick={loadUsers} className="cursor-pointer">
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            </Button>
            {canExport && (
              <Button 
                variant="outline" 
                size="sm" 
                onClick={() => {
                  const params = new URLSearchParams();
                  if (status) params.append("status", status);
                  window.open(`/admin/api/users/export?${params.toString()}`, "_blank");
                }}
                className="cursor-pointer whitespace-nowrap"
              >
                <Download className="h-4 w-4" />
                导出
              </Button>
            )}
            <StaticLink href="/admin/users/create" className="inline-flex">
              {canCreate && (
                <Button size="sm" className="cursor-pointer whitespace-nowrap">
                  <UserPlus className="h-4 w-4" />
                  新建
                </Button>
              )}
            </StaticLink>
          </div>
        </div>
      </Card>

      {/* 用户表格 */}
      <Card>
        <div className="overflow-x-auto -mx-6 px-6">
          {loading ? (
            <div className="py-12 text-center">
              <RefreshCw className="h-8 w-8 mx-auto mb-3 animate-spin text-[hsl(var(--accent))]" />
              <p className="text-sm text-[hsl(var(--ink-muted))]">正在加载用户...</p>
            </div>
          ) : users.length === 0 ? (
            <EmptyState title="暂无用户" subtitle="没有符合条件的账号。" />
          ) : (
            <table className="w-full text-sm">
              <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] border-b border-[hsl(var(--line))]">
                <tr>
                  <th className="px-3 py-3 font-semibold">用户名</th>
                  <th className="px-3 py-3 font-semibold">邮箱</th>
                  <th className="px-3 py-3 font-semibold">状态</th>
                  <th className="px-3 py-3 font-semibold">角色</th>
                  <th className="px-3 py-3 font-semibold">所属项目</th>
                  <th className="px-3 py-3 font-semibold">锁定</th>
                  <th className="px-3 py-3 font-semibold text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[hsl(var(--line))]">
                {users.map((user) => (
                  <tr key={user.user_name} className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors">
                    <td className="px-3 py-4 font-medium text-[hsl(var(--ink))]">{user.user_name}</td>
                    <td className="px-3 py-4 text-[hsl(var(--ink-muted))] text-xs">{user.email || "-"}</td>
                    <td className="px-3 py-4">
                      <button
                        onClick={() => handleToggleStatus(user.user_name)}
                        className="cursor-pointer hover:opacity-80 transition-opacity"
                        title="点击切换状态"
                      >
                        <Badge tone={statusToneMap[user.status] || "neutral"}>
                          {statusLabelMap[user.status] ?? user.status}
                        </Badge>
                      </button>
                    </td>
                    <td className="px-3 py-4">
                      <div className="flex flex-wrap gap-1">
                        {user.roles.length ? user.roles.map((role) => (
                          <Badge key={role} tone="info">{role}</Badge>
                        )) : <span className="text-[hsl(var(--ink-muted))] text-xs">-</span>}
                      </div>
                    </td>
                    <td className="px-3 py-4">
                      <div className="flex flex-wrap gap-1">
                        {user.projects && user.projects.length > 0 ? user.projects.map((proj) => (
                          <Badge 
                            key={proj.project_id} 
                            tone={proj.permission_level === 'admin' ? 'success' : proj.permission_level === 'write' ? 'warning' : 'neutral'}
                            className="text-xs"
                          >
                            {proj.project_name}
                            <span className="ml-1 opacity-60">({proj.permission_level === 'admin' ? '管理' : proj.permission_level === 'write' ? '读写' : '只读'})</span>
                          </Badge>
                        )) : <span className="text-[hsl(var(--ink-muted))] text-xs">-</span>}
                      </div>
                    </td>
                    <td className="px-3 py-4 text-xs text-[hsl(var(--ink-muted))]">
                      {user.locked_until ? (
                        <span className="inline-flex items-center gap-1 text-[hsl(var(--warning))]">
                          <Lock className="h-3 w-3" />
                          {user.locked_until}
                        </span>
                      ) : (
                        "-"
                      )}
                    </td>
                    <td className="px-3 py-4">
                      <div className="flex justify-end gap-1.5">
                        {canUpdate && (
                          <Button 
                            variant="primary" 
                            size="sm" 
                            onClick={() => openEditModal(user)} 
                            className="cursor-pointer h-8 px-3"
                          >
                            <Edit2 className="h-3 w-3" />
                            编辑
                          </Button>
                        )}
                        {canUpdate && (
                          <Button 
                            variant="outline" 
                            size="sm" 
                            onClick={() => handleResetPassword(user.user_name)}
                            className="cursor-pointer h-8 px-3"
                          >
                            重置密码
                          </Button>
                        )}
                        {canDelete && (
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={() => handleDeleteUser(user.user_name)}
                            className="cursor-pointer h-8 px-2 text-[hsl(var(--danger))] hover:bg-[hsl(var(--danger))]/10"
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

      {/* 编辑用户 Modal */}
      <Modal
        open={editModalOpen}
        title={`编辑用户 ${editingUser?.user_name ?? ""}`}
        onClose={closeEditModal}
        size="md"
        footer={
          <div className="flex justify-end gap-2">
            <Button variant="outline" size="sm" onClick={closeEditModal} className="cursor-pointer">
              取消
            </Button>
            <Button variant="primary" size="sm" onClick={handleEditSubmit} disabled={editLoading} className="cursor-pointer">
              <Save className="h-4 w-4" />
              {editLoading ? "保存中..." : "保存修改"}
            </Button>
          </div>
        }
      >
        <div className="space-y-5">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              邮箱
            </label>
            <Input type="email" value={editEmail} onChange={(e) => setEditEmail(e.target.value)} placeholder="user@example.com" />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              状态
            </label>
            <Select value={editStatus} onChange={(e) => setEditStatus(e.target.value)}>
              <option value="active">启用</option>
              <option value="disabled">禁用</option>
            </Select>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              角色
            </label>
            <div className="flex flex-wrap gap-2">
              {editRoles.map((role) => (
                <label
                  key={role.name}
                  className={`flex items-center gap-2 rounded-full border px-4 py-2 text-sm cursor-pointer transition-all ${
                    role.checked 
                      ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))]/10 text-[hsl(var(--accent))]" 
                      : "border-[hsl(var(--line))] hover:bg-[hsl(var(--sand-2))]"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={role.checked}
                    onChange={(e) =>
                      setEditRoles((prev) =>
                        prev.map((item) =>
                          item.name === role.name ? { ...item, checked: e.target.checked } : item
                        )
                      )
                    }
                    className="accent-[hsl(var(--accent))] h-4 w-4"
                  />
                  {role.name}
                </label>
              ))}
              {editRoles.length === 0 && (
                <span className="text-sm text-[hsl(var(--ink-muted))]">加载角色中...</span>
              )}
            </div>
          </div>
        </div>
      </Modal>

      {/* 重置密码结果 Modal */}
      <Modal
        open={!!resetPasswordModal}
        title="密码已重置"
        onClose={() => setResetPasswordModal(null)}
        size="sm"
        footer={
          <div className="flex justify-end">
            <Button variant="primary" size="sm" onClick={() => setResetPasswordModal(null)} className="cursor-pointer">
              确定
            </Button>
          </div>
        }
      >
        {resetPasswordModal && (
          <div className="space-y-4">
            <p className="text-[hsl(var(--ink))]">
              用户 <strong>{resetPasswordModal.userName}</strong> 的密码已重置为：
            </p>
            <div className="rounded-xl bg-[hsl(var(--sand-2))] p-4 font-mono text-lg text-[hsl(var(--accent))] text-center select-all">
              {resetPasswordModal.newPassword}
            </div>
            <p className="text-xs text-[hsl(var(--ink-muted))]">
              请将此密码告知用户，用户登录后需要修改密码。
            </p>
          </div>
        )}
      </Modal>
    </div>
    </RequirePermission>
  );
}
