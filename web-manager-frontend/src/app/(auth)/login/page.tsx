"use client";

import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ensureSecurePasswordTransport } from "@/lib/password";
import { preparePassword, isEncryptionSupported } from "@/lib/crypto";
import { navigateTo } from "@/lib/navigation";

export default function LoginPage() {
  const [userName, setUserName] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);
    setNotice(null);
    setLoading(true);

    try {
      const transport = ensureSecurePasswordTransport();
      if (!transport.ok) {
        setError(transport.message ?? "密码传输不安全。");
        setLoading(false);
        return;
      }
      if (transport.warning) {
        setNotice(transport.warning);
      }

      // 准备加密密码
      let passwordData: unknown;
      try {
        passwordData = await preparePassword(password);
      } catch (encryptError) {
        setError(encryptError instanceof Error ? encryptError.message : "密码加密失败");
        setLoading(false);
        return;
      }

      // 使用 JSON 格式发送（支持加密密码对象）
      const response = await fetch("/api/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_name: userName,
          password: passwordData,
          remember_me: rememberMe,
        }),
        credentials: "include",
      });

      const data = await response.json();

      if (data.success) {
        // 登录成功，跳转到目标页面
        navigateTo(data.redirect || "/queue-op");
        return;
      } else {
        // 显示服务器返回的错误信息
        setError(data.error || "登录失败，请检查用户名或密码。");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h2 className="font-display text-xl text-[hsl(var(--ink))]">欢迎回来</h2>
        <p className="text-sm text-[hsl(var(--ink-muted))]">登录后管理你的队列。</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            用户名
          </label>
          <Input value={userName} onChange={(event) => setUserName(event.target.value)} required />
        </div>
        <div className="space-y-2">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            密码
          </label>
          <Input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        <label className="flex items-center gap-2 text-xs text-[hsl(var(--ink-muted))]">
          <input
            type="checkbox"
            checked={rememberMe}
            onChange={(event) => setRememberMe(event.target.checked)}
            className="h-4 w-4 rounded border-[hsl(var(--line))]"
          />
          记住我
        </label>
        {notice ? <div className="rounded-2xl border border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10 px-4 py-2 text-xs text-[hsl(var(--warning))]">{notice}</div> : null}
        {error ? <div className="rounded-2xl border border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 px-4 py-2 text-xs text-[hsl(var(--danger))]">{error}</div> : null}
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "正在登录..." : "登录"}
        </Button>
      </form>

      <div className="text-center text-xs text-[hsl(var(--ink-muted))]">
        <a className="font-semibold text-[hsl(var(--accent-2))]" href="/forgot-password">
          忘记密码？
        </a>
      </div>
    </div>
  );
}
