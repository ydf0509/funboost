/**
 * 导航工具函数
 * 
 * 在静态导出模式下，Next.js 的客户端路由（router.push）依赖 RSC payload 文件，
 * 这些文件在 Flask 服务时可能无法正确处理。
 * 
 * 此模块提供统一的导航函数，在生产环境下使用完整页面刷新，
 * 在开发环境下使用 Next.js 客户端路由。
 */

/**
 * 检测是否为生产环境（静态导出模式）
 * 
 * 在静态导出模式下，我们通过 Flask 服务静态文件，
 * 此时应该使用完整页面刷新而不是客户端路由。
 */
export function isStaticExportMode(): boolean {
  // 在服务端渲染时，默认为非静态模式
  if (typeof window === 'undefined') {
    return false;
  }
  
  // 检查是否为开发服务器（端口 3000）
  const isDev = window.location.port === '3000';
  
  return !isDev;
}

/**
 * 导航到指定路径
 * 
 * 在静态导出模式下使用完整页面刷新，
 * 在开发模式下可以使用 Next.js router。
 * 
 * @param path 目标路径
 * @param options 导航选项
 */
export function navigateTo(path: string, options?: { replace?: boolean }): void {
  if (typeof window === 'undefined') {
    return;
  }
  
  // 确保路径以 / 开头
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  
  if (isStaticExportMode()) {
    // 静态导出模式：使用完整页面刷新
    if (options?.replace) {
      window.location.replace(normalizedPath);
    } else {
      window.location.href = normalizedPath;
    }
  } else {
    // 开发模式：也使用完整页面刷新以保持一致性
    // 这样可以避免开发和生产环境行为不一致
    if (options?.replace) {
      window.location.replace(normalizedPath);
    } else {
      window.location.href = normalizedPath;
    }
  }
}

/**
 * 替换当前页面（不添加历史记录）
 * 
 * @param path 目标路径
 */
export function replaceTo(path: string): void {
  navigateTo(path, { replace: true });
}
