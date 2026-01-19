import ProjectUsersClient from "./ProjectUsersClient";

// 静态导出需要 generateStaticParams
// 生成一些占位 ID，实际路由在客户端动态处理
export function generateStaticParams() {
  return Array.from({ length: 100 }, (_, i) => ({ id: String(i + 1) }));
}

export default function ProjectUsersPage() {
  return <ProjectUsersClient />;
}
