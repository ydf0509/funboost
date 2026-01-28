"use client";

import { useEffect, useState } from "react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { Select } from "@/components/ui/Select";
import { ensureSecurePasswordTransport } from "@/lib/password";
import { navigateTo } from "@/lib/navigation";
import { apiFetch } from "@/lib/api";

interface Role {
  id: number;
  name: string;
  description?: string;
}

interface Project {
  id: number;
  name: string;
  code: string;
  status: string;
}

interface SelectedProject {
  projectId: number;
  permissionLevel: string;
}

export default function UserCreatePage() {
  const [roles, setRoles] = useState<Role[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [userName, setUserName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);
  const [selectedProjects, setSelectedProjects] = useState<SelectedProject[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadData = async () => {
      try {
        // 加载角色
        const rolesResponse = await fetch("/admin/api/roles", {
          credentials: "include",
        });
        const rolesData = await rolesResponse.json();
        if (rolesData.success && rolesData.data?.roles) {
          setRoles(rolesData.data.roles);
        }

        // 加载项目列表
        const projectsResponse = await apiFetch<{
          success: boolean;
          data: { projects: Project[] };
        }>("/admin/api/projects?page_size=100&status=active");
        if (projectsResponse.success && projectsResponse.data?.projects) {
          setProjects(projectsResponse.data.projects);
        }
      } catch (err) {
        setNotice(err instanceof Error ? err.message : "加载数据失败。");
      }
    };

    loadData();
  }, []);

  // 切换项目选择
  const toggleProject = (projectId: number) => {
    setSelectedProjects((prev) => {
      const existing = prev.find((p) => p.projectId === projectId);
      if (existing) {
        return prev.filter((p) => p.projectId !== projectId);
      } else {
        return [...prev, { projectId, permissionLevel: "read" }];
      }
    });
  };

  // 更新项目权限级别
  const updateProjectPermission = (projectId: number, permissionLevel: string) => {
    setSelectedProjects((prev) =>
      prev.map((p) => (p.projectId === projectId ? { ...p, permissionLevel } : p))
    );
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setNotice(null);
    setWarning(null);
    setLoading(true);

    try {
      const transport = ensureSecurePasswordTransport();
      if (!transport.ok) {
        setNotice(transport.message ?? "密码传输不安全。");
        setLoading(false);
        return;
      }
      if (transport.warning) {
        setWarning(transport.warning);
      }

      const formData = new FormData();
      formData.append("user_name", userName);
      formData.append("password", password);
      formData.append("email", email);
      selectedRoles.forEach((role) => formData.append("roles", role));
      // 添加项目授权信息
      formData.append("projects", JSON.stringify(selectedProjects));

      // 使用 API 路径提交（直接调用后端，避免 Next.js rewrites 问题）
      const apiBase = (await import('@/lib/api-config')).getApiBaseUrl();
      const response = await fetch(`${apiBase}/admin/api/users/create`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      const data = await response.json();
      if (data.success) {
        navigateTo("/admin/users");
      } else {
        setNotice(data.error || "创建用户失败。");
      }
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "创建用户失败。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <RequirePermission permissions={["user:create"]}>
      <div className="space-y-8">
        <SectionHeader title="创建用户" subtitle="新增账号并分配角色和项目权限。" />

      {notice ? (
        <Card className="border border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 text-sm text-[hsl(var(--danger))]">
          {notice}
        </Card>
      ) : null}
      {warning ? (
        <Card className="border border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10 text-sm text-[hsl(var(--warning))]">
          {warning}
        </Card>
      ) : null}

      <Card>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                用户名
              </label>
              <Input value={userName} onChange={(event) => setUserName(event.target.value)} required />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
                邮箱
              </label>
              <Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </div>
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              密码
            </label>
            <Input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              角色
            </label>
            <div className="flex flex-wrap gap-2">
              {roles.map((role) => (
                <label key={role.name} className="flex items-center gap-2 rounded-full border border-[hsl(var(--line))] px-3 py-1 text-xs">
                  <input
                    type="checkbox"
                    checked={selectedRoles.includes(role.name)}
                    onChange={(event) => {
                      setSelectedRoles((prev) =>
                        event.target.checked ? [...prev, role.name] : prev.filter((item) => item !== role.name)
                      );
                    }}
                  />
                  {role.name}
                </label>
              ))}
            </div>
          </div>

          {/* 项目授权 */}
          <div className="space-y-3">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              项目授权
            </label>
            <p className="text-xs text-[hsl(var(--ink-muted))]">
              选择用户可以访问的项目，并设置权限级别（只读/读写/管理员）
            </p>
            {projects.length === 0 ? (
              <p className="text-sm text-[hsl(var(--ink-muted))]">暂无可用项目</p>
            ) : (
              <div className="space-y-2 rounded-xl border border-[hsl(var(--line))] p-4">
                {projects.map((project) => {
                  const selected = selectedProjects.find((p) => p.projectId === project.id);
                  return (
                    <div
                      key={project.id}
                      className={`flex items-center justify-between rounded-lg p-3 transition ${selected
                        ? "bg-[hsl(var(--accent))]/10 border border-[hsl(var(--accent))]/30"
                        : "bg-[hsl(var(--sand-2))] hover:bg-[hsl(var(--sand-2))]/80"
                        }`}
                    >
                      <label className="flex items-center gap-3 cursor-pointer flex-1">
                        <input
                          type="checkbox"
                          checked={!!selected}
                          onChange={() => toggleProject(project.id)}
                          className="h-4 w-4"
                        />
                        <div>
                          <span className="font-medium text-[hsl(var(--ink))]">{project.name}</span>
                          <span className="ml-2 text-xs text-[hsl(var(--ink-muted))]">({project.code})</span>
                        </div>
                      </label>
                      {selected && (
                        <Select
                          value={selected.permissionLevel}
                          onChange={(e) => updateProjectPermission(project.id, e.target.value)}
                          className="w-28 text-xs"
                        >
                          <option value="read">只读</option>
                          <option value="write">读写</option>
                          <option value="admin">管理员</option>
                        </Select>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
            {selectedProjects.length > 0 && (
              <p className="text-xs text-[hsl(var(--accent-2))]">
                已选择 {selectedProjects.length} 个项目
              </p>
            )}
          </div>

          <Button type="submit" disabled={loading}>
            {loading ? "正在创建..." : "创建用户"}
          </Button>
        </form>
      </Card>
      </div>
    </RequirePermission>
  );
}
