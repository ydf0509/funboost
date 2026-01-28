"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { navigateTo } from "@/lib/navigation";

export default function ProfileChangeEmailPage() {
  const [email, setEmail] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setNotice(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("new_email", email);
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/profile/change-email`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      setNotice("验证邮件已发送。");
      setTimeout(() => navigateTo("/profile"), 1200);
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "更新失败。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">

      {notice ? (
        <Card className="border border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-sm text-[hsl(var(--accent-2))]">
          {notice}
        </Card>
      ) : null}

      <Card>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              新邮箱
            </label>
            <Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </div>
          <p className="text-xs text-[hsl(var(--ink-muted))]">验证链接 30 分钟后失效。</p>
          <Button type="submit" disabled={loading}>
            {loading ? "正在发送..." : "发送验证邮件"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
