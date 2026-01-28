"use client";

import { useCallback, useEffect, useState } from "react";
import { Edit2, FolderKanban, Plus, RefreshCw, Shield, ShieldPlus, Trash2, X } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { useActionPermissions } from "@/hooks/useActionPermissions";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { PermissionSelector, type PermissionCategory } from "@/components/ui/PermissionSelector";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { StatCard } from "@/components/ui/StatCard";
import { TextArea } from "@/components/ui/TextArea";
import { apiFetch } from "@/lib/api";

type PermissionItem = {
  code: string;
  name: string;
  description?: string;
};

type ProjectItem = {
  id: number;
  code: string;
  name: string;
  description?: string;
};

type RoleRow = {
  id: number;
  name: string;
  description: string;
  permissions: string[];
  projects?: { id: number; code: string; name: string }[];
  user_count: number;
  created_at: string;
  is_builtin: boolean;
};

type RoleForm = {
  name: string;
  description: string;
  permissions: string[];
  projects: number[];
};

const emptyForm: RoleForm = {
  name: "",
  description: "",
  permissions: [],
  projects: [],
};

export default function RolesPage() {
  const [roles, setRoles] = useState<RoleRow[]>([]);
  const [allPermissions, setAllPermissions] = useState<PermissionItem[]>([]);
  const [permissionTree, setPermissionTree] = useState<PermissionCategory[]>([]);
  const [allProjects, setAllProjects] = useState<ProjectItem[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 使用 useActionPermissions hook 获取操作权限
  const { canCreate, canUpdate, canDelete } = useActionPermissions("role");

  // Modal state
  const [formOpen, setFormOpen] = useState(false);
  const [editingRole, setEditingRole] = useState<RoleRow | null>(null);
  const [roleForm, setRoleForm] = useState<RoleForm>(emptyForm);
  const [saving, setSaving] = useState(false);

  const loadRoles = useCallback(async () => {
    setLoading(true);
    setNotice(null);
    try {
      const response = await apiFetch<{
        success: boolean;
        data: { roles: RoleRow[]; total: number };
      }>("/admin/api/roles");

      if (response.success && response.data) {
        setRoles(response.data.roles);
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "加载角色失败。");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadPermissions = useCallback(async () => {
    try {
      // 加载权限树
      const treeResponse = await apiFetch<{
        success: boolean;
        data: { tree: { categories: PermissionCategory[] } | PermissionCategory[] };
      }>("/admin/api/permissions/tree");

      if (treeResponse.success && treeResponse.data) {
        // 兼容两种格式：{ categories: [...] } 或直接数组
        const tree = treeResponse.data.tree;
        const categories = Array.isArray(tree) ? tree : (tree.categories || []);
        setPermissionTree(categories);
        
        // 递归提取所有权限
        const extractPermissions = (cats: PermissionCategory[]): PermissionItem[] => {
          return cats.flatMap(cat => [
            ...(cat.permissions || []),
            ...extractPermissions(cat.subcategories || [])
          ]);
        };
        setAllPermissions(extractPermissions(categories));
      }
    } catch (err) {
      console.error("Failed to load permissions tree:", err);
      // 降级到旧 API
      try {
        const response = await apiFetch<{
          success: boolean;
          data: { permissions: PermissionItem[] };
        }>("/admin/api/permissions");
        if (response.success && response.data) {
          setAllPermissions(response.data.permissions);
        }
      } catch {
        console.error("Failed to load permissions from fallback API");
      }
    }
  }, []);

  const loadProjects = useCallback(async () => {
    try {
      const response = await apiFetch<{
        success: boolean;
        data: { projects: ProjectItem[] };
      }>("/admin/api/projects?page_size=100");

      if (response.success && response.data) {
        setAllProjects(response.data.projects);
      }
    } catch (err) {
      console.error("Failed to load projects:", err);
    }
  }, []);

  useEffect(() => {
    loadRoles();
    loadPermissions();
    loadProjects();
  }, [loadRoles, loadPermissions, loadProjects]);

  const openCreateForm = () => {
    setEditingRole(null);
    setRoleForm(emptyForm);
    setFormOpen(true);
  };

  const openEditForm = async (role: RoleRow) => {
    setEditingRole(role);
    try {
      const response = await apiFetch<{ success: boolean; data: RoleRow }>(
        `/admin/api/roles/${role.id}`
      );
      if (response.success && response.data) {
        setRoleForm({
          name: response.data.name,
          description: response.data.description || "",
          permissions: response.data.permissions || [],
          projects: response.data.projects?.map(p => p.id) || [],
        });
      } else {
        setRoleForm({
          name: role.name,
          description: role.description || "",
          permissions: role.permissions || [],
          projects: role.projects?.map(p => p.id) || [],
        });
      }
    } catch {
      setRoleForm({
        name: role.name,
        description: role.description || "",
        permissions: role.permissions || [],
        projects: role.projects?.map(p => p.id) || [],
      });
    }
    setFormOpen(true);
  };

  const handlePermissionChange = (permissions: string[]) => {
    setRoleForm(prev => ({ ...prev, permissions }));
  };

  const handleProjectToggle = (projectId: number) => {
    setRoleForm(prev => ({
      ...prev,
      projects: prev.projects.includes(projectId)
        ? prev.projects.filter(id => id !== projectId)
        : [...prev.projects, projectId]
    }));
  };

  const handleSubmit = async () => {
    setNotice(null);
    setSaving(true);
    try {
      const payload = {
        name: roleForm.name,
        description: roleForm.description,
        permissions: roleForm.permissions,
        projects: roleForm.projects,
      };

      if (editingRole) {
        const response = await apiFetch<{ success: boolean; error?: string }>(
          `/admin/api/roles/${editingRole.id}`,
          { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
        );
        if (!response.success) throw new Error(response.error || "更新失败");
        setNotice("角色更新成功！");
      } else {
        const response = await apiFetch<{ success: boolean; error?: string }>(
          `/admin/api/roles`,
          { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }
        );
        if (!response.success) throw new Error(response.error || "创建失败");
        setNotice("角色创建成功！");
      }
      setFormOpen(false);
      setEditingRole(null);
      loadRoles();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "操作失败。");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (role: RoleRow) => {
    if (!confirm(`确定要删除角色 "${role.name}" 吗？\n此操作不可撤销！`)) return;
    setNotice(null);
    try {
      const response = await apiFetch<{ success: boolean; error?: string }>(
        `/admin/api/roles/${role.id}`,
        { method: "DELETE" }
      );
      if (!response.success) throw new Error(response.error || "删除失败");
      setNotice("角色删除成功！");
      loadRoles();
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "删除失败。");
    }
  };

  const stats = {
    total: roles.length,
    builtin: roles.filter(r => r.is_builtin).length,
    custom: roles.filter(r => !r.is_builtin).length,
    totalUsers: roles.reduce((sum, r) => sum + r.user_count, 0),
  };

  return (
    <RequirePermission permissions={["role:read"]}>
    <div className="space-y-6">
      {/* 通知消息 - 改为浮动Toast */}
      {notice && (
        <div className="fixed top-4 right-4 z-50 animate-in slide-in-from-top-2 fade-in duration-300">
          <Card className="shadow-lg max-w-md border-l-4 border-l-blue-500 bg-blue-50 dark:bg-blue-950/20">
            <div className="flex items-start gap-3 p-4">
              <div className="flex-shrink-0 text-blue-500">
                <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-blue-800 dark:text-blue-200">{notice}</p>
              </div>
              <button 
                onClick={() => setNotice(null)}
                className="flex-shrink-0 text-blue-500 hover:text-blue-700 transition-colors"
              >
                <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </Card>
        </div>
      )}

      {/* 统计卡片 */}
      <div className="grid gap-4 grid-cols-2 lg:grid-cols-4">
        <StatCard label="总角色数" value={stats.total} helper="个" tone="info" />
        <StatCard label="内置角色" value={stats.builtin} helper="个" tone="success" />
        <StatCard label="自定义" value={stats.custom} helper="个" tone="warning" />
        <StatCard label="关联用户" value={stats.totalUsers} helper="人" tone="neutral" />
      </div>

      {/* 角色列表 - 整合操作区域 */}
      <Card>
        <div className="flex flex-col gap-4">
          {/* 操作按钮区域 */}
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-[hsl(var(--ink))]">角色管理</h3>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={loadRoles} className="cursor-pointer">
                <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                刷新
              </Button>
              {canCreate && (
                <Button variant="primary" size="sm" onClick={openCreateForm} className="cursor-pointer">
                  <ShieldPlus className="h-4 w-4" />
                  新建角色
                </Button>
              )}
            </div>
          </div>

          {/* 表格 */}
          <div className="overflow-x-auto -mx-6 px-6">
            {loading ? (
              <div className="py-12 text-center">
                <RefreshCw className="h-8 w-8 mx-auto mb-3 animate-spin text-[hsl(var(--accent))]" />
                <p className="text-sm text-[hsl(var(--ink-muted))]">正在加载角色...</p>
              </div>
            ) : roles.length === 0 ? (
              <EmptyState title="暂无角色" subtitle="请先创建角色并分配权限。" />
            ) : (
              <table className="w-full text-sm">
                <thead className="text-left text-xs uppercase tracking-wider text-[hsl(var(--ink-muted))] border-b border-[hsl(var(--line))]">
                  <tr>
                    <th className="px-3 py-3 font-semibold">角色</th>
                    <th className="px-3 py-3 font-semibold">描述</th>
                    <th className="px-3 py-3 font-semibold">权限</th>
                    <th className="px-3 py-3 font-semibold">关联项目</th>
                    <th className="px-3 py-3 font-semibold">用户数</th>
                    <th className="px-3 py-3 font-semibold">创建时间</th>
                    <th className="px-3 py-3 font-semibold">操作</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--line))]">
                  {roles.map((role) => (
                    <tr key={role.id} className="hover:bg-[hsl(var(--sand-2))]/50 transition-colors">
                      <td className="px-3 py-4">
                        <div className="flex items-center gap-2">
                          <Shield className="h-4 w-4 text-[hsl(var(--accent))]" />
                          <span className="font-medium text-[hsl(var(--ink))]">{role.name}</span>
                          {role.is_builtin && <Badge tone="info">内置</Badge>}
                        </div>
                      </td>
                      <td className="px-3 py-4 text-[hsl(var(--ink-muted))] text-xs max-w-xs truncate">
                        {role.description || "-"}
                      </td>
                      <td className="px-3 py-4">
                        <div className="flex flex-wrap gap-1 max-w-md">
                          {role.permissions.length > 0 ? (
                            role.permissions.slice(0, 3).map((perm) => (
                              <Badge key={perm} tone="neutral" className="text-xs">{perm}</Badge>
                            ))
                          ) : (
                            <span className="text-[hsl(var(--ink-muted))] text-xs">-</span>
                          )}
                          {role.permissions.length > 3 && (
                            <Badge tone="neutral" className="text-xs">+{role.permissions.length - 3}</Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-4">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {role.projects && role.projects.length > 0 ? (
                            role.projects.slice(0, 2).map((proj) => (
                              <Badge key={proj.id} tone="info" className="text-xs">
                                <FolderKanban className="h-3 w-3 mr-1" />
                                {proj.name}
                              </Badge>
                            ))
                          ) : (
                            <span className="text-[hsl(var(--ink-muted))] text-xs">全部项目</span>
                          )}
                          {role.projects && role.projects.length > 2 && (
                            <Badge tone="info" className="text-xs">+{role.projects.length - 2}</Badge>
                          )}
                        </div>
                      </td>
                      <td className="px-3 py-4 text-center">
                        <Badge tone={role.user_count > 0 ? "success" : "neutral"}>{role.user_count}</Badge>
                      </td>
                      <td className="px-3 py-4 text-xs text-[hsl(var(--ink-muted))]">{role.created_at || "-"}</td>
                      <td className="px-3 py-4">
                        <div className="flex items-center gap-1.5">
                          {canUpdate && (
                            <Button 
                              variant="primary" 
                              size="sm" 
                              className="h-8 px-3 cursor-pointer" 
                              onClick={() => openEditForm(role)}
                            >
                              <Edit2 className="h-3 w-3" />
                              编辑
                            </Button>
                          )}
                          {canDelete && (
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="h-8 px-2 cursor-pointer text-[hsl(var(--danger))] hover:bg-[hsl(var(--danger))]/10" 
                              onClick={() => handleDelete(role)} 
                              disabled={role.is_builtin || role.user_count > 0}
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
        </div>
      </Card>

      <Modal
        open={formOpen}
        title={editingRole ? `编辑角色: ${editingRole.name}` : "新建角色"}
        subtitle={editingRole ? "修改角色信息和权限配置" : "创建新角色并分配权限"}
        onClose={() => setFormOpen(false)}
        size="xl"
        footer={
          <div className="flex items-center justify-between">
            <p className="text-xs text-[hsl(var(--ink-muted))]">
              {roleForm.permissions.length > 0 && (
                <span>已选择 <span className="font-semibold text-[hsl(var(--accent))]">{roleForm.permissions.length}</span> 项权限</span>
              )}
            </p>
            <div className="flex gap-3">
              <Button 
                variant="outline" 
                onClick={() => setFormOpen(false)}
                className="cursor-pointer"
              >
                <X className="h-4 w-4" />
                取消
              </Button>
              <Button 
                onClick={handleSubmit} 
                disabled={saving || !roleForm.name.trim()}
                className="cursor-pointer min-w-[120px]"
              >
                {saving ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    保存中...
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4" />
                    {editingRole ? "保存修改" : "创建角色"}
                  </>
                )}
              </Button>
            </div>
          </div>
        }
      >
        <div className="space-y-6">
          {/* 基本信息区块 */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 pb-2 border-b border-[hsl(var(--line))]/40">
              <Shield className="h-4 w-4 text-[hsl(var(--accent))]" />
              <h3 className="text-sm font-semibold text-[hsl(var(--ink))]">基本信息</h3>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label 
                  htmlFor="role-name"
                  className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]"
                >
                  角色名称 <span className="text-[hsl(var(--danger))]">*</span>
                </label>
                <Input 
                  id="role-name"
                  value={roleForm.name} 
                  onChange={(e) => setRoleForm(prev => ({ ...prev, name: e.target.value }))} 
                  placeholder="例如：项目管理员" 
                  disabled={editingRole?.is_builtin}
                  className="transition-all duration-200"
                />
                {editingRole?.is_builtin && (
                  <p className="flex items-center gap-1 text-xs text-[hsl(var(--warning))]">
                    <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    内置角色不能修改名称
                  </p>
                )}
              </div>
              
              <div className="space-y-2 md:col-span-2">
                <label 
                  htmlFor="role-description"
                  className="block text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]"
                >
                  描述
                </label>
                <TextArea 
                  id="role-description"
                  value={roleForm.description} 
                  onChange={(e) => setRoleForm(prev => ({ ...prev, description: e.target.value }))} 
                  placeholder="简要描述此角色的职责和用途..." 
                  className="min-h-[72px] resize-none transition-all duration-200"
                />
              </div>
            </div>
          </div>

          {/* 关联项目区块 */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[hsl(var(--line))]/40">
              <div className="flex items-center gap-2">
                <FolderKanban className="h-4 w-4 text-[hsl(var(--accent))]" />
                <h3 className="text-sm font-semibold text-[hsl(var(--ink))]">关联项目</h3>
              </div>
              {roleForm.projects.length > 0 && (
                <Badge tone="info" className="text-xs">
                  已选 {roleForm.projects.length} 个
                </Badge>
              )}
            </div>
            <p className="text-xs text-[hsl(var(--ink-muted))]">
              选择此角色可以访问的项目。不选择则可访问全部项目。
            </p>
            <div className="rounded-2xl bg-[hsl(var(--sand))]/50 border border-[hsl(var(--line))]/30 p-4 max-h-[180px] overflow-y-auto">
              {allProjects.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-6 text-center">
                  <FolderKanban className="h-8 w-8 text-[hsl(var(--ink-muted))]/40 mb-2" />
                  <p className="text-sm text-[hsl(var(--ink-muted))]">暂无可用项目</p>
                </div>
              ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {allProjects.map((proj) => (
                    <label 
                      key={proj.id} 
                      className={`
                        group flex items-center gap-2.5 rounded-xl border px-3 py-2.5 
                        cursor-pointer transition-all duration-200
                        ${roleForm.projects.includes(proj.id) 
                          ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))]/10 shadow-sm" 
                          : "border-[hsl(var(--line))]/60 hover:border-[hsl(var(--accent))]/50 hover:bg-[hsl(var(--card))]/50"
                        }
                      `}
                    >
                      <input 
                        type="checkbox" 
                        checked={roleForm.projects.includes(proj.id)} 
                        onChange={() => handleProjectToggle(proj.id)} 
                        className="h-4 w-4 rounded border-[hsl(var(--line))] text-[hsl(var(--accent))] focus:ring-[hsl(var(--accent))]/20 transition-colors" 
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-1.5">
                          <FolderKanban className={`h-3.5 w-3.5 transition-colors ${
                            roleForm.projects.includes(proj.id) 
                              ? "text-[hsl(var(--accent))]" 
                              : "text-[hsl(var(--ink-muted))] group-hover:text-[hsl(var(--accent))]"
                          }`} />
                          <span className="text-sm font-medium text-[hsl(var(--ink))] truncate">{proj.name}</span>
                        </div>
                        {proj.code !== proj.name && (
                          <p className="text-xs text-[hsl(var(--ink-muted))] truncate mt-0.5">{proj.code}</p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 权限分配区块 */}
          <div className="space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-[hsl(var(--line))]/40">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-[hsl(var(--accent))]" />
                <h3 className="text-sm font-semibold text-[hsl(var(--ink))]">权限分配</h3>
              </div>
              {roleForm.permissions.length > 0 && (
                <Badge tone="success" className="text-xs">
                  已选 {roleForm.permissions.length} 项
                </Badge>
              )}
            </div>
            {permissionTree.length > 0 ? (
              <PermissionSelector
                tree={permissionTree}
                selectedPermissions={roleForm.permissions}
                onSelectionChange={handlePermissionChange}
                disabled={false}
              />
            ) : allPermissions.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 text-center rounded-2xl bg-[hsl(var(--sand))]/50 border border-[hsl(var(--line))]/30">
                <Shield className="h-10 w-10 text-[hsl(var(--ink-muted))]/40 mb-3" />
                <p className="text-sm text-[hsl(var(--ink-muted))]">暂无可用权限</p>
                <p className="text-xs text-[hsl(var(--ink-muted))]/70 mt-1">请先在权限管理中创建权限</p>
              </div>
            ) : (
              <div className="rounded-2xl bg-[hsl(var(--sand))]/50 border border-[hsl(var(--line))]/30 p-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {allPermissions.map((perm) => (
                    <label 
                      key={perm.code} 
                      className={`
                        group flex items-center gap-2.5 rounded-xl border px-3 py-2.5 
                        cursor-pointer transition-all duration-200
                        ${roleForm.permissions.includes(perm.code) 
                          ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))]/10 shadow-sm" 
                          : "border-[hsl(var(--line))]/60 hover:border-[hsl(var(--accent))]/50 hover:bg-[hsl(var(--card))]/50"
                        }
                      `}
                    >
                      <input 
                        type="checkbox" 
                        checked={roleForm.permissions.includes(perm.code)} 
                        onChange={() => { 
                          const newPerms = roleForm.permissions.includes(perm.code) 
                            ? roleForm.permissions.filter(p => p !== perm.code) 
                            : [...roleForm.permissions, perm.code]; 
                          handlePermissionChange(newPerms); 
                        }} 
                        className="h-4 w-4 rounded border-[hsl(var(--line))] text-[hsl(var(--accent))] focus:ring-[hsl(var(--accent))]/20 transition-colors" 
                      />
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-[hsl(var(--ink))]">{perm.name || perm.code}</span>
                        {perm.description && (
                          <p className="text-xs text-[hsl(var(--ink-muted))] truncate mt-0.5">{perm.description}</p>
                        )}
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </Modal>
    </div>
    </RequirePermission>
  );
}
