const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "";
const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "::1"]);

type PasswordTransportResult = {
  ok: boolean;
  message?: string;
  warning?: string;
};

const isLocalHost = (hostname: string) => LOCAL_HOSTS.has(hostname);

// 检查是否允许不安全的密码传输（内网部署时使用）
function isInsecureAllowed(): boolean {
  // 运行时检查，避免被构建时优化掉
  if (typeof window !== "undefined") {
    // 检查 URL 参数（用于临时测试）
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get("allow_insecure") === "true") {
      return true;
    }
  }
  // 检查环境变量（构建时设置）
  return process.env.NEXT_PUBLIC_ALLOW_INSECURE_PASSWORD === "true";
}

export function ensureSecurePasswordTransport(): PasswordTransportResult {
  if (typeof window === "undefined") {
    return { ok: true };
  }

  // 内网部署时允许非 HTTPS
  if (isInsecureAllowed()) {
    return { ok: true, warning: "已开启不安全密码传输，仅用于内网环境。" };
  }

  const origin = window.location.origin;
  const baseUrl = API_BASE ? new URL(API_BASE, origin) : new URL(origin);
  const isLocal = isLocalHost(baseUrl.hostname);
  const isHttps = baseUrl.protocol === "https:";

  // 内网 IP 地址也允许（192.168.x.x, 10.x.x.x, 172.16-31.x.x）
  const isPrivateIP = /^(192\.168\.|10\.|172\.(1[6-9]|2[0-9]|3[01])\.)/.test(baseUrl.hostname);
  
  if (isPrivateIP) {
    return { ok: true, warning: "当前为内网环境，密码将以明文提交。" };
  }

  if (!window.isSecureContext && !isLocal) {
    return {
      ok: false,
      message: "当前页面不是安全上下文，已阻止提交。请使用 HTTPS 访问前端。",
    };
  }

  if (!isHttps && !isLocal) {
    return {
      ok: false,
      message: "检测到后端为非 HTTPS，已阻止提交。请启用 HTTPS。",
    };
  }

  if (!isHttps && isLocal) {
    return { ok: true, warning: "当前为本地开发环境，密码将以明文提交，请勿用于生产环境。" };
  }

  return { ok: true };
}
