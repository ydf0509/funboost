import type { NextConfig } from "next";
import type { Rewrite, RouteHas } from "next/dist/lib/load-custom-routes";

/**
 * Next.js 配置
 * 
 * 生产环境：静态导出到 Flask 静态目录
 * 开发环境：使用 rewrites 代理 API 请求到后端
 * 
 * 环境变量：
 * - BACKEND_PORT: 后端端口，默认 27018
 * - ALLOWED_HOSTS: 允许的主机名列表，逗号分隔，默认 "localhost,127.0.0.1"
 *                  前端会根据访问的 host 自动代理到对应的后端地址
 */
const isProd = process.env.NODE_ENV === "production";

// 开发模式后端端口
const BACKEND_PORT = process.env.BACKEND_PORT || "27018";

// 允许的主机名列表（用于动态生成 rewrites）
// 每个主机名都会生成对应的 rewrite 规则，确保 cookie domain 一致
const ALLOWED_HOSTS = (process.env.ALLOWED_HOSTS || "localhost,127.0.0.1")
  .split(",")
  .map(h => h.trim())
  .filter(Boolean);

/**
 * 为指定的源路径生成多主机 rewrite 规则
 * 第一个匹配的 host 会被使用，所以更具体的规则放在前面
 */
function generateHostRewrites(source: string, extraHas?: RouteHas[]): Rewrite[] {
  const rewrites: Rewrite[] = [];

  // 为每个 host 生成带条件的 rewrite 规则
  for (const host of ALLOWED_HOSTS) {
    const hasConditions = [
      { type: "header" as const, key: "host", value: `${host.replace(/\./g, "\\.")}(.*)` },
      ...(extraHas || []),
    ];

    rewrites.push({
      source,
      destination: `http://${host}:${BACKEND_PORT}${source}`,
      has: hasConditions,
    });
  }

  // 始终添加一个默认 fallback（使用第一个 host），确保请求不会漏掉
  const fallback: Rewrite = {
    source,
    destination: `http://${ALLOWED_HOSTS[0]}:${BACKEND_PORT}${source}`,
  };
  // 如果有额外条件，fallback 也需要这些条件
  if (extraHas && extraHas.length > 0) {
    fallback.has = extraHas;
  }
  rewrites.push(fallback);

  return rewrites;
}

const nextConfig: NextConfig = {
  // Next.js 16 Turbopack 会尝试推断 monorepo root；本仓库同时存在多个 lockfile，
  // 可能导致推断到仓库根目录，从而在构建时错误地从根目录解析依赖（例如 tailwindcss）。
  // 显式指定 root 为前端项目目录，避免出现 "Can't resolve 'tailwindcss'" 等错误。
  turbopack: {
    root: __dirname,
  },

  // 生产环境使用静态导出模式，输出到 Flask 静态目录
  output: isProd ? "export" : undefined,

  // 生产环境使用静态导出模式
  // 注意：Next.js 16 Turbopack 不允许 distDir 指向项目外部
  // 构建后需要将 out/ 目录内容复制到 Flask 静态目录
  distDir: isProd ? "out" : ".next",

  // 禁用图片优化（静态导出不支持）
  images: {
    unoptimized: true,
  },

  // 不使用尾部斜杠，避免重定向循环
  trailingSlash: false,

  // 开发环境使用 rewrites 代理 API 请求
  // 根据请求的 host 动态选择后端地址，确保 cookie domain 一致
  async rewrites() {
    // 生产环境不需要 rewrites（静态导出不支持）
    if (isProd) {
      return [];
    }

    // 生成 fallback 规则：根据访问的 host 代理到对应的后端
    const fallbackRewrites: Rewrite[] = ALLOWED_HOSTS.map(host => ({
      source: "/:path*",
      destination: `http://${host}:${BACKEND_PORT}/:path*`,
      has: [{ type: "header" as const, key: "host", value: `${host.replace(/\./g, "\\.")}(.*)` }],
    }));

    // 添加一个默认 fallback（使用第一个 host）
    fallbackRewrites.push({
      source: "/:path*",
      destination: `http://${ALLOWED_HOSTS[0]}:${BACKEND_PORT}/:path*`,
    });

    return {
      // beforeFiles: 在检查 Next.js 页面之前处理，用于必须代理到后端的请求
      beforeFiles: [
        // 用户项目 API（项目选择器需要）
        ...generateHostRewrites("/api/user/projects"),
        ...generateHostRewrites("/api/user/current-project"),
        // 用户管理 API（需要代理到后端）
        ...generateHostRewrites("/admin/api/users"),
        ...generateHostRewrites("/admin/api/users/:path*"),
        // 用户操作 API（FormData 请求，包含 multipart 或 form-urlencoded）
        ...generateHostRewrites("/admin/users/create", [
          { type: "header" as const, key: "content-type", value: "(.*)(multipart/form-data|application/x-www-form-urlencoded)(.*)" },
        ]),
        ...generateHostRewrites("/admin/users/:path*/edit", [
          { type: "header" as const, key: "content-type", value: "(.*)(multipart/form-data|application/x-www-form-urlencoded)(.*)" },
        ]),
        ...generateHostRewrites("/admin/users/:path*/toggle_status", [
          { type: "header" as const, key: "content-type", value: "(.*)" },
        ]),
        ...generateHostRewrites("/admin/users/:path*/delete"),
        ...generateHostRewrites("/admin/users/:path*/unlock"),
        ...generateHostRewrites("/admin/users/:path*/reset_password"),
        // 角色管理 API
        ...generateHostRewrites("/admin/api/roles"),
        ...generateHostRewrites("/admin/api/roles/:path*"),
        // 邮件配置相关 API（需要 multipart/form-data）
        ...generateHostRewrites("/admin/email-config", [
          { type: "header" as const, key: "content-type", value: "(.*)multipart/form-data(.*)" },
        ]),
        // 测试邮件 API
        ...generateHostRewrites("/admin/test-email"),
        ...generateHostRewrites("/admin/test-email-ajax"),
      ],
      // afterFiles: 在 Next.js 页面匹配后处理
      afterFiles: [],
      // fallback: 未匹配的请求代理到后端
      fallback: fallbackRewrites,
    };
  },
};

export default nextConfig;
