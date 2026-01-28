"use client";

import { useState } from "react";
import { KeyRound, Eye, EyeOff, ShieldCheck, AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { apiFetch } from "@/lib/api";
import { preparePasswords } from "@/lib/crypto";
import { navigateTo } from "@/lib/navigation";

export default function ForceChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setError(null);

    // 前端验证
    if (!currentPassword || !newPassword || !confirmPassword) {
      setError("所有字段都是必填的");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("两次输入的新密码不一致");
      return;
    }

    if (newPassword.length < 8) {
      setError("新密码长度至少8位");
      return;
    }

    setLoading(true);
    try {
      // 加密所有密码
      let encryptedPasswords;
      try {
        encryptedPasswords = await preparePasswords({
          current_password: currentPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        });
      } catch (encryptError) {
        setError(encryptError instanceof Error ? encryptError.message : "密码加密失败");
        setLoading(false);
        return;
      }

      const response = await apiFetch<{ success: boolean; error?: string; redirect?: string }>(
        "/api/force_change_password",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(encryptedPasswords),
        }
      );

      if (!response.success) {
        throw new Error(response.error || "修改失败");
      }

      setSuccess(true);
      setTimeout(() => {
        navigateTo(response.redirect || "/queue-op");
      }, 1500);
    } catch (err) {
      setError(err instanceof Error ? err.message : "修改失败，请稍后重试");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 标题 */}
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[hsl(var(--warning))]/15 text-[hsl(var(--warning))] mb-4">
          <KeyRound className="h-7 w-7" />
        </div>
        <h2 className="font-display text-xl text-[hsl(var(--ink))]">修改密码</h2>
        <p className="mt-1 text-sm text-[hsl(var(--ink-muted))]">安全策略要求您修改密码</p>
      </div>

      {/* 安全提示 */}
      <Card className="border-[hsl(var(--warning))]/30 bg-[hsl(var(--warning))]/5 p-4">
        <div className="flex gap-3">
          <AlertTriangle className="h-5 w-5 text-[hsl(var(--warning))] flex-shrink-0" />
          <div className="text-xs text-[hsl(var(--ink-muted))]">
            <p className="font-semibold text-[hsl(var(--warning))] mb-1">密码要求</p>
            <ul className="space-y-0.5 list-disc list-inside">
              <li>至少8个字符</li>
              <li>包含大小写字母和数字</li>
              <li>包含特殊字符（如 @#$%）</li>
            </ul>
          </div>
        </div>
      </Card>

      {/* 成功状态 */}
      {success ? (
        <div className="text-center py-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[hsl(var(--success))]/15 text-[hsl(var(--success))] mb-4">
            <ShieldCheck className="h-7 w-7" />
          </div>
          <h3 className="font-display text-lg text-[hsl(var(--ink))]">密码修改成功</h3>
          <p className="mt-1 text-sm text-[hsl(var(--ink-muted))]">正在跳转...</p>
        </div>
      ) : (
        <form className="space-y-4" onSubmit={handleSubmit}>
          {/* 错误提示 */}
          {error && (
            <div className="rounded-xl border border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 px-4 py-3 text-sm text-[hsl(var(--danger))]">
              {error}
            </div>
          )}

          {/* 当前密码 */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              当前密码
            </label>
            <div className="relative">
              <Input
                type={showCurrentPassword ? "text" : "password"}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="请输入当前密码"
                required
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))] transition-colors cursor-pointer"
              >
                {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* 新密码 */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              新密码
            </label>
            <div className="relative">
              <Input
                type={showNewPassword ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="请输入新密码"
                required
              />
              <button
                type="button"
                onClick={() => setShowNewPassword(!showNewPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))] transition-colors cursor-pointer"
              >
                {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* 确认新密码 */}
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--ink-muted))]">
              确认新密码
            </label>
            <div className="relative">
              <Input
                type={showConfirmPassword ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="请再次输入新密码"
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))] transition-colors cursor-pointer"
              >
                {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          {/* 提交按钮 */}
          <Button type="submit" className="w-full cursor-pointer" disabled={loading}>
            {loading ? "正在保存..." : "确认修改密码"}
          </Button>
        </form>
      )}

      {/* 返回登录 */}
      {!success && (
        <div className="text-center text-xs text-[hsl(var(--ink-muted))]">
          <a className="font-semibold text-[hsl(var(--accent-2))] hover:underline cursor-pointer" href="/login">
            返回登录
          </a>
        </div>
      )}
    </div>
  );
}
