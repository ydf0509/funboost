import { getApiBaseUrl } from './api-config';

export type FunboostResponse<T> = {
  succ: boolean;
  msg?: string;
  data: T;
};

// 使用 api-config 获取 API 基础 URL
const getApiBase = () => getApiBaseUrl();

type ApiOptions = RequestInit & {
  json?: unknown;
};

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const url = `${getApiBase()}${path}`;
  const headers = new Headers(options.headers);
  let body = options.body;

  if (options.json !== undefined) {
    headers.set("Content-Type", "application/json");
    body = JSON.stringify(options.json);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    body,
    credentials: "include",
  });

  // 处理 401 未认证错误 - 清理缓存并重定向到登录页面
  if (response.status === 401) {
    if (typeof window !== "undefined") {
      // 清理所有认证相关的 localStorage 缓存，防止 stale session 导致重定向循环
      try {
        localStorage.removeItem("user_permissions_cache");
        localStorage.removeItem("current_project");
        // 保留主题设置: localStorage.removeItem("funboost-theme");
        
        // 重定向循环检测：如果 2 秒内已经重定向过，不再重定向
        const lastRedirect = sessionStorage.getItem("last_401_redirect");
        const now = Date.now();
        if (lastRedirect && now - parseInt(lastRedirect, 10) < 2000) {
          console.warn("检测到重定向循环，已阻止自动跳转");
          throw new Error("会话已过期，请刷新页面后重新登录");
        }
        sessionStorage.setItem("last_401_redirect", now.toString());
      } catch (e) {
        // localStorage/sessionStorage 不可用，忽略
        if (e instanceof Error && e.message.includes("会话已过期")) {
          throw e;
        }
      }
      window.location.href = "/login";
    }
    throw new Error("未登录，请先登录");
  }

  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    // 尝试从不同的字段获取错误消息
    let message = `请求失败：${response.status}`;
    if (typeof data === "object" && data) {
      const errorData = data as { msg?: string; error?: string; message?: string };
      message = errorData.msg || errorData.error || errorData.message || message;
    }
    throw new Error(message);
  }

  return data as T;
}

export async function funboostFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const data = await apiFetch<FunboostResponse<T>>(path, options);
  if (!data.succ) {
    throw new Error(data.msg || "请求失败");
  }
  return data.data;
}

export function buildQuery(params: Record<string, string | number | undefined | null>) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }
    search.append(key, String(value));
  });
  return search.toString();
}
