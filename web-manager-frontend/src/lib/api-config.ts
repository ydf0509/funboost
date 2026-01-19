/**
 * API 配置
 * 
 * 生产环境：使用相对路径，前端和后端同源部署
 * 开发环境：使用 NEXT_PUBLIC_API_BASE 环境变量或默认值
 * 
 * 环境变量：
 * - NEXT_PUBLIC_API_BASE: 后端 API 基础 URL（开发环境使用）
 */

/**
 * 获取 API 基础 URL
 * 
 * @returns API 基础 URL
 * - 生产环境：空字符串（同源部署，使用相对路径）
 * - 开发环境：环境变量或默认值 http://127.0.0.1:27018
 */
export function getApiBaseUrl(): string {
  // 服务端渲染时使用环境变量
  if (typeof window === 'undefined') {
    return process.env.NEXT_PUBLIC_API_BASE || '';
  }

  // 客户端：生产环境使用相对路径（同源部署）
  if (process.env.NODE_ENV === 'production') {
    return '';
  }

  // 客户端：开发环境直接访问后端（绕过 Next.js rewrites 问题）
  return process.env.NEXT_PUBLIC_API_BASE || 'http://127.0.0.1:27018';
}

/**
 * API 配置对象
 */
export const apiConfig = {
  /** API 基础 URL */
  get baseUrl(): string {
    return getApiBaseUrl();
  },

  /** 请求凭证模式 */
  credentials: 'include' as RequestCredentials,

  /** 默认请求头 */
  defaultHeaders: {
    'Content-Type': 'application/json',
  },
};

/**
 * 构建完整的 API URL
 * 
 * @param path API 路径（以 / 开头）
 * @returns 完整的 API URL
 */
export function buildApiUrl(path: string): string {
  const base = getApiBaseUrl();
  // 确保路径以 / 开头
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${base}${normalizedPath}`;
}
