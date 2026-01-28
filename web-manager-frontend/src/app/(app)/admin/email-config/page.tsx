"use client";

import { useEffect, useState } from "react";
import { Mail, RefreshCw, Save } from "lucide-react";

import { RequirePermission } from "@/components/auth/RequirePermission";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { apiFetch } from "@/lib/api";
import { useActionPermissions } from "@/hooks/useActionPermissions";

type EmailConfig = {
  smtp_host: string;
  smtp_port: string;
  smtp_username: string;
  smtp_password: string;
  encryption: string;
  sender_name: string;
  sender_email: string;
};

const emptyConfig: EmailConfig = {
  smtp_host: "",
  smtp_port: "587",
  smtp_username: "",
  smtp_password: "",
  encryption: "tls",
  sender_name: "",
  sender_email: "",
};

export default function EmailConfigPage() {
  const [config, setConfig] = useState<EmailConfig>(emptyConfig);
  const [testEmail, setTestEmail] = useState("");
  const [notice, setNotice] = useState<string | null>(null);
  const [noticeType, setNoticeType] = useState<"success" | "error">("success");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const { canUpdate } = useActionPermissions("config");

  const loadConfig = async () => {
    setLoading(true);
    try {
      const response = await apiFetch<{
        success: boolean;
        data: {
          smtp_host?: string;
          smtp_port?: number;
          smtp_username?: string;
          use_tls?: boolean;
          use_ssl?: boolean;
          sender_name?: string;
          sender_email?: string;
        } | null;
      }>("/admin/api/email-config");

      if (response.success && response.data) {
        const data = response.data;
        setConfig({
          smtp_host: data.smtp_host || "",
          smtp_port: String(data.smtp_port || 587),
          smtp_username: data.smtp_username || "",
          smtp_password: "",  // Never returned from API
          encryption: data.use_ssl ? "ssl" : data.use_tls ? "tls" : "none",
          sender_name: data.sender_name || "",
          sender_email: data.sender_email || "",
        });
      }
    } catch (err) {
      showNotice(err instanceof Error ? err.message : "加载配置失败。", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const showNotice = (message: string, type: "success" | "error" = "success") => {
    setNotice(message);
    setNoticeType(type);
  };

  const updateConfig = async () => {
    if (!canUpdate) {
      showNotice("您没有权限修改邮件配置。", "error");
      return;
    }
    setSaving(true);
    setNotice(null);
    try {
      const response = await apiFetch<{ success: boolean; message?: string; error?: string }>(
        "/admin/api/email-config",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            smtp_host: config.smtp_host,
            smtp_port: config.smtp_port,
            smtp_username: config.smtp_username,
            smtp_password: config.smtp_password,
            encryption: config.encryption,
            sender_name: config.sender_name,
            sender_email: config.sender_email,
          }),
        }
      );

      if (response.success) {
        showNotice(response.message || "邮件配置保存成功！", "success");
      } else {
        showNotice(response.error || "保存失败。", "error");
      }
    } catch (err) {
      showNotice(err instanceof Error ? err.message : "保存失败。", "error");
    } finally {
      setSaving(false);
    }
  };

  const sendTest = async () => {
    if (!canUpdate) {
      showNotice("您没有权限发送测试邮件。", "error");
      return;
    }
    if (!testEmail) {
      showNotice("请输入测试邮箱地址", "error");
      return;
    }

    setTesting(true);
    setNotice(null);
    try {
      const response = await apiFetch<{ success: boolean; message: string }>(
        "/admin/test-email-ajax",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: testEmail }),
        }
      );
      showNotice(response.message, response.success ? "success" : "error");
    } catch (err) {
      showNotice(err instanceof Error ? err.message : "测试失败。", "error");
    } finally {
      setTesting(false);
    }
  };

  return (
    <RequirePermission permissions={["config:read"]}>
    <div className="space-y-6">

      {notice && (
        <Card className={`border text-sm ${noticeType === "success"
            ? "border-[hsl(var(--success))]/30 bg-[hsl(var(--success))]/10 text-[hsl(var(--success))]"
            : "border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 text-[hsl(var(--danger))]"
          }`}>
          {notice}
        </Card>
      )}

      <Card>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-display text-lg text-[hsl(var(--ink))]">SMTP 服务器设置</h3>
            <p className="text-sm text-[hsl(var(--ink-muted))]">配置邮件发送服务器信息。</p>
          </div>
          <Button variant="outline" size="sm" onClick={loadConfig} disabled={loading} className="cursor-pointer">
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            刷新
          </Button>
        </div>
        <div className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                SMTP 服务器 *
              </label>
              <Input
                placeholder="例如: smtp.gmail.com"
                value={config.smtp_host}
                onChange={(e) => setConfig((prev) => ({ ...prev, smtp_host: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                端口 *
              </label>
              <Input
                type="number"
                placeholder="587"
                value={config.smtp_port}
                onChange={(e) => setConfig((prev) => ({ ...prev, smtp_port: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                用户名
              </label>
              <Input
                placeholder="SMTP认证用户名（可选）"
                value={config.smtp_username}
                onChange={(e) => setConfig((prev) => ({ ...prev, smtp_username: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                密码
              </label>
              <Input
                type="password"
                placeholder="SMTP认证密码（可选，留空保持不变）"
                value={config.smtp_password}
                onChange={(e) => setConfig((prev) => ({ ...prev, smtp_password: e.target.value }))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
                加密方式
              </label>
              <Select
                value={config.encryption}
                onChange={(e) => setConfig((prev) => ({ ...prev, encryption: e.target.value }))}
              >
                <option value="tls">TLS (推荐)</option>
                <option value="ssl">SSL</option>
                <option value="none">无加密</option>
              </Select>
            </div>
          </div>
        </div>
      </Card>

      <Card>
        <div className="mb-4">
          <h3 className="font-display text-lg text-[hsl(var(--ink))]">发件人信息</h3>
          <p className="text-sm text-[hsl(var(--ink-muted))]">配置邮件发件人显示信息。</p>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
              发件人名称
            </label>
            <Input
              placeholder="例如: 系统管理员"
              value={config.sender_name}
              onChange={(e) => setConfig((prev) => ({ ...prev, sender_name: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
              发件人邮箱 *
            </label>
            <Input
              placeholder="例如: admin@example.com"
              value={config.sender_email}
              onChange={(e) => setConfig((prev) => ({ ...prev, sender_email: e.target.value }))}
            />
          </div>
        </div>
        <div className="mt-6">
          <Button onClick={updateConfig} disabled={saving || !canUpdate}>
            {saving ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                保存配置
              </>
            )}
          </Button>
        </div>
      </Card>

      <Card>
        <div className="mb-4">
          <h3 className="font-display text-lg text-[hsl(var(--ink))]">发送测试邮件</h3>
          <p className="text-sm text-[hsl(var(--ink-muted))]">验证邮件配置是否正确。</p>
        </div>
        <div className="flex flex-wrap items-end gap-3">
          <div className="flex-1 min-w-[200px] space-y-2">
            <label className="text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
              收件人邮箱
            </label>
            <Input
              placeholder="输入接收测试邮件的邮箱地址"
              value={testEmail}
              onChange={(e) => setTestEmail(e.target.value)}
            />
          </div>
          <Button variant="outline" onClick={sendTest} disabled={testing || !canUpdate}>
            {testing ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                发送中...
              </>
            ) : (
              <>
                <Mail className="h-4 w-4" />
                发送测试邮件
              </>
            )}
          </Button>
        </div>
      </Card>
    </div>
    </RequirePermission>
  );
}
