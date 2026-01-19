"use client";

import { useEffect, useState } from "react";
import { KeyRound, Mail } from "lucide-react";

import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { StaticLink } from "@/components/ui/StaticLink";
import { apiFetch } from "@/lib/api";

export default function ProfilePage() {
  const [profile, setProfile] = useState({
    user_name: "",
    email: "",
    status: "",
    roles: [] as string[],
    last_login: "",
  });
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await apiFetch<{
          success: boolean; data: {
            user_name: string;
            email: string;
            status: string;
            roles: string[];
            last_login: { time: string; ip: string } | null;
          }
        }>("/api/profile");

        if (response.success && response.data) {
          const { user_name, email, status, roles, last_login } = response.data;
          setProfile({
            user_name,
            email: email || "",
            status: status || "",
            roles: roles || [],
            last_login: last_login ? `上次登录: ${last_login.time} (IP: ${last_login.ip})` : "",
          });
        }
      } catch (err) {
        setNotice(err instanceof Error ? err.message : "加载个人信息失败。");
      }
    };

    load();
  }, []);

  return (
    <div className="space-y-6">

      {notice ? (
        <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
          {notice}
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <h3 className="font-display text-lg text-[hsl(var(--ink))]">账户信息</h3>
          <div className="mt-4 space-y-2 text-sm text-[hsl(var(--ink-muted))]">
            <div>用户名：<span className="font-semibold text-[hsl(var(--ink))]">{profile.user_name}</span></div>
            <div>邮箱：<span className="font-semibold text-[hsl(var(--ink))]">{profile.email || "-"}</span></div>
            <div>状态：<Badge tone="info">{profile.status || "-"}</Badge></div>
            <div>角色：{profile.roles.length ? profile.roles.join(", ") : "-"}</div>
            <div className="text-xs text-[hsl(var(--ink-muted))]">{profile.last_login}</div>
          </div>
        </Card>
        <Card>
          <h3 className="font-display text-lg text-[hsl(var(--ink))]">安全设置</h3>
          <div className="mt-4 flex flex-wrap gap-2">
            <StaticLink href="/profile/change-password" className="inline-flex">
              <Button variant="outline">
                <KeyRound className="h-4 w-4" />
                修改密码
              </Button>
            </StaticLink>
            <StaticLink href="/profile/change-email" className="inline-flex">
              <Button variant="outline">
                <Mail className="h-4 w-4" />
                修改邮箱
              </Button>
            </StaticLink>
          </div>
        </Card>
      </div>
    </div>
  );
}
