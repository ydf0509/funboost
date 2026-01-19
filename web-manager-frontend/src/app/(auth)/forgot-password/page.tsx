"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("email", email);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/forgot_password`, {
        method: "POST",
        body: formData,
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setMessage(data.message || "如果邮箱存在，重置链接已发送。");
      } else {
        setError(data.error || "请求失败，请稍后重试。");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="font-display text-xl text-[hsl(var(--ink))]">重置密码</h2>
        <p className="text-sm text-[hsl(var(--ink-muted))]">我们会向邮箱发送重置链接。</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            邮箱
          </label>
          <Input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </div>
        {message ? <div className="rounded-2xl border border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10 px-4 py-2 text-xs text-[hsl(var(--success))]">{message}</div> : null}
        {error ? <div className="rounded-2xl border border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 px-4 py-2 text-xs text-[hsl(var(--danger))]">{error}</div> : null}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "正在发送..." : "发送重置链接"}
        </Button>
      </form>

      <div className="text-center text-xs text-[hsl(var(--ink-muted))]">
        <a className="font-semibold text-[hsl(var(--accent-2))]" href="/login">
          返回登录
        </a>
      </div>
    </div>
  );
}
