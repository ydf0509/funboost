"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { useState } from "react";
import { Eye, EyeOff, CheckCircle2, AlertCircle } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ensureSecurePasswordTransport } from "@/lib/password";
import { preparePasswords } from "@/lib/crypto";
import { navigateTo } from "@/lib/navigation";

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  // 密码强度检查
  const checkPasswordStrength = (pwd: string) => {
    if (!pwd) return { score: 0, text: "", color: "" };
    
    let score = 0;
    if (pwd.length >= 8) score++;
    if (pwd.length >= 12) score++;
    if (/[a-z]/.test(pwd)) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^a-zA-Z0-9]/.test(pwd)) score++;
    
    const levels = [
      { score: 0, text: "", color: "" },
      { score: 1, text: "弱", color: "text-[hsl(var(--danger))]" },
      { score: 2, text: "中等", color: "text-[hsl(var(--warning))]" },
      { score: 3, text: "强", color: "text-[hsl(var(--success))]" },
      { score: 4, text: "很强", color: "text-[hsl(var(--success))]" },
      { score: 5, text: "非常强", color: "text-[hsl(var(--success))]" },
    ];
    
    return levels[Math.min(score, 5)];
  };

  const strength = checkPasswordStrength(newPassword);

  if (!token) {
    return (
      <div className="space-y-4">
        <div className="space-y-1 text-center">
          <h2 className="font-display text-lg font-semibold text-[hsl(var(--ink))]">重置密码</h2>
          <p className="text-xs text-[hsl(var(--ink-muted))]">无效的重置链接</p>
        </div>
        <div className="rounded-lg border border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 px-3 py-2">
          <p className="text-xs text-[hsl(var(--danger))]">重置链接无效或已过期，请重新申请密码重置。</p>
        </div>
        <div className="text-center">
          <a className="text-xs font-semibold text-[hsl(var(--accent-2))] hover:text-[hsl(var(--accent))]" href="/forgot-password">
            重新申请
          </a>
        </div>
      </div>
    );
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setMessage(null);
    setError(null);
    setNotice(null);

    if (newPassword !== confirmPassword) {
      setError("两次输入的密码不一致。");
      return;
    }

    if (newPassword.length < 8) {
      setError("密码长度至少 8 个字符。");
      return;
    }

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

      // 加密密码
      let encryptedPasswords;
      try {
        encryptedPasswords = await preparePasswords({
          new_password: newPassword,
          confirm_password: confirmPassword,
        });
      } catch (encryptError) {
        setError(encryptError instanceof Error ? encryptError.message : "密码加密失败");
        setLoading(false);
        return;
      }

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE ?? ""}/reset_password/${token}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(encryptedPasswords),
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setMessage(data.message || "密码已更新，请重新登录。");
        setTimeout(() => navigateTo("/login"), 1500);
      } else {
        setError(data.error || "重置失败，请稍后重试。");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "重置失败。");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* 页面标题 */}
      <div className="space-y-1 text-center">
        <h2 className="font-display text-lg font-semibold text-[hsl(var(--ink))]">设置新密码</h2>
        <p className="text-xs text-[hsl(var(--ink-muted))]">请输入一个强密码来保护你的账户</p>
      </div>

      {/* 表单 */}
      <form className="space-y-3" onSubmit={handleSubmit}>
        {/* 新密码 */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            新密码
          </label>
          <div className="relative">
            <Input
              type={showNewPassword ? "text" : "password"}
              value={newPassword}
              onChange={(event) => setNewPassword(event.target.value)}
              placeholder="输入新密码"
              required
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowNewPassword(!showNewPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))] transition-colors cursor-pointer"
            >
              {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {newPassword && (
            <div className="flex items-center justify-between text-xs px-1">
              <span className="text-[hsl(var(--ink-muted))]">强度：</span>
              <span className={strength.color}>{strength.text}</span>
            </div>
          )}
        </div>

        {/* 确认密码 */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
            确认新密码
          </label>
          <div className="relative">
            <Input
              type={showConfirmPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(event) => setConfirmPassword(event.target.value)}
              placeholder="再次输入密码"
              required
              className="pr-10"
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))] transition-colors cursor-pointer"
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {newPassword && confirmPassword && newPassword === confirmPassword && (
            <div className="flex items-center gap-1 text-xs text-[hsl(var(--success))] px-1">
              <CheckCircle2 className="h-3 w-3" />
              密码匹配
            </div>
          )}
        </div>

        {/* 提示消息 */}
        {notice && (
          <div className="rounded-lg border border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/10 px-3 py-2 flex gap-2">
            <AlertCircle className="h-4 w-4 text-[hsl(var(--warning))] flex-shrink-0 mt-0.5" />
            <p className="text-xs text-[hsl(var(--warning))]">{notice}</p>
          </div>
        )}

        {message && (
          <div className="rounded-lg border border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10 px-3 py-2 flex gap-2">
            <CheckCircle2 className="h-4 w-4 text-[hsl(var(--success))] flex-shrink-0 mt-0.5" />
            <p className="text-xs text-[hsl(var(--success))]">{message}</p>
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 px-3 py-2 flex gap-2">
            <AlertCircle className="h-4 w-4 text-[hsl(var(--danger))] flex-shrink-0 mt-0.5" />
            <p className="text-xs text-[hsl(var(--danger))]">{error}</p>
          </div>
        )}

        {/* 提交按钮 */}
        <Button type="submit" className="w-full" disabled={loading || !newPassword || !confirmPassword}>
          {loading ? "正在更新..." : "更新密码"}
        </Button>
      </form>

      {/* 返回登录 */}
      <div className="text-center text-xs text-[hsl(var(--ink-muted))]">
        <a className="font-semibold text-[hsl(var(--accent-2))] hover:text-[hsl(var(--accent))] transition-colors" href="/login">
          返回登录
        </a>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="space-y-4">
        <div className="space-y-1 text-center">
          <h2 className="font-display text-lg font-semibold text-[hsl(var(--ink))]">设置新密码</h2>
          <p className="text-xs text-[hsl(var(--ink-muted))]">正在加载...</p>
        </div>
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  );
}
