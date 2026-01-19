"use client";

import { useEffect, useState } from "react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { SectionHeader } from "@/components/ui/SectionHeader";
import { TextArea } from "@/components/ui/TextArea";
import { apiFetch } from "@/lib/api";
import { navigateTo } from "@/lib/navigation";

const parsePermissions = (html: string) => {
  const doc = new DOMParser().parseFromString(html, "text/html");
  return Array.from(doc.querySelectorAll("input[name='permissions']")).map((input) => {
    const element = input as HTMLInputElement;
    const label = element.closest("label")?.textContent?.trim() || element.value;
    return { code: element.value, label };
  });
};

export default function RoleCreatePage() {
  const [permissions, setPermissions] = useState<{ code: string; label: string }[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selected, setSelected] = useState<string[]>([]);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadPermissions = async () => {
      try {
        const html = await apiFetch<string>("/admin/roles/create");
        setPermissions(parsePermissions(html));
      } catch (err) {
        setNotice(err instanceof Error ? err.message : "加载权限失败。");
      }
    };

    loadPermissions();
  }, []);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setNotice(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("name", name);
      formData.append("description", description);
      selected.forEach((perm) => formData.append("permissions", perm));

      await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/admin/roles/create`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      navigateTo("/admin/roles");
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "创建失败。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <RequirePermission permissions={["role:create"]}>
      <div className="space-y-8">
        <SectionHeader title="创建角色" subtitle="为新角色定义权限。" />

      {notice ? (
        <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
          {notice}
        </Card>
      ) : null}

      <Card>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              角色名称
            </label>
            <Input value={name} onChange={(event) => setName(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              描述
            </label>
            <TextArea value={description} onChange={(event) => setDescription(event.target.value)} />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              权限
            </label>
            <div className="flex flex-wrap gap-2">
              {permissions.map((perm) => (
                <label key={perm.code} className="flex items-center gap-2 rounded-full border border-[hsl(var(--line))] px-3 py-1 text-xs">
                  <input
                    type="checkbox"
                    checked={selected.includes(perm.code)}
                    onChange={(event) => {
                      setSelected((prev) =>
                        event.target.checked ? [...prev, perm.code] : prev.filter((item) => item !== perm.code)
                      );
                    }}
                  />
                  {perm.code}
                </label>
              ))}
            </div>
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? "正在创建..." : "创建角色"}
          </Button>
        </form>
      </Card>
      </div>
    </RequirePermission>
  );
}
