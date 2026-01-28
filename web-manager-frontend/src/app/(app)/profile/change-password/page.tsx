"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ensureSecurePasswordTransport } from "@/lib/password";
import { navigateTo } from "@/lib/navigation";

export default function ProfileChangePasswordPage() {
  const [current, setCurrent] = useState("");
  const [nextPass, setNextPass] = useState("");
  const [confirm, setConfirm] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [warning, setWarning] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setNotice(null);
    setWarning(null);
    if (nextPass !== confirm) {
      setNotice("两次输入的密码不一致。");
      return;
    }
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
      formData.append("current_password", current);
      formData.append("new_password", nextPass);
      formData.append("confirm_password", confirm);
      await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/profile/change-password`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });
      navigateTo("/profile");
    } catch (err) {
      setNotice(err instanceof Error ? err.message : "更新失败。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">

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
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              当前密码
            </label>
            <Input type="password" value={current} onChange={(event) => setCurrent(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              新密码
            </label>
            <Input type="password" value={nextPass} onChange={(event) => setNextPass(event.target.value)} required />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              确认新密码
            </label>
            <Input type="password" value={confirm} onChange={(event) => setConfirm(event.target.value)} required />
          </div>
          <Button type="submit" disabled={loading}>
            {loading ? "正在保存..." : "保存"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
