import {
  BarChart3,
  ClipboardList,
  Clock,
  Cog,
  Database,
  FileText,
  FolderKanban,
  Gauge,
  LayoutDashboard,
  LogOut,
  Mail,
  Network,
  Radio,
  Settings,
  Shield,
  User,
  Users,
  Workflow,
} from "lucide-react";

export type NavItem = {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  /** 访问此菜单项所需的权限（任意一个即可，除非使用 permissionMode: 'all'） */
  permissions?: string[];
  /** 权限匹配模式：'any' = 任意一个权限即可，'all' = 需要所有权限 */
  permissionMode?: 'any' | 'all';
  /** 权限表达式，支持 AND 逻辑，如 "user:read AND role:read" */
  permissionExpression?: string;
};

export type NavGroup = {
  title: string;
  items: NavItem[];
  /** 访问此分组所需的权限（任意一个即可） */
  permissions?: string[];
  /** 权限匹配模式：'any' = 任意一个权限即可，'all' = 需要所有权限 */
  permissionMode?: 'any' | 'all';
};

export const navGroups: NavGroup[] = [
  {
    title: "总览",
    items: [
      { label: "队列运维", href: "/queue-op", icon: Gauge, permissions: ["queue:read"] },
      { label: "RPC 调用", href: "/rpc-call", icon: Radio, permissions: ["queue:read"] },
      { label: "定时任务", href: "/timing-jobs", icon: Clock, permissions: ["queue:read"] },
    ],
  },
  {
    title: "监控",
    items: [
      { label: "任务结果", href: "/fun-results", icon: Database, permissions: ["queue:read"] },
      { label: "消费速率", href: "/consume-speed", icon: BarChart3, permissions: ["queue:read"] },
      { label: "按 IP 查看消费者", href: "/running-consumers/ip", icon: Network, permissions: ["queue:read"] },
      { label: "按队列查看消费者", href: "/running-consumers/queue", icon: Workflow, permissions: ["queue:read"] },
      { label: "关于", href: "/about", icon: FileText },
      { label: "个人中心", href: "/profile", icon: User },
    ],
  },
  {
    title: "系统管理",
    permissions: ["user:read", "role:read", "project:read", "audit:read", "config:read"],
    items: [
      { label: "用户管理", href: "/admin/users", icon: Users, permissions: ["user:read"] },
      { label: "角色管理", href: "/admin/roles", icon: Shield, permissions: ["role:read"] },
      { label: "项目管理", href: "/admin/projects", icon: FolderKanban, permissions: ["project:read"] },
      { label: "审计日志", href: "/admin/audit/logs", icon: ClipboardList, permissions: ["audit:read"] },
      { label: "邮件配置", href: "/admin/email-config", icon: Mail, permissions: ["config:read"] },
    ],
  },
];

export const quickActions: NavItem[] = [
  { label: "仪表盘", href: "/queue-op", icon: LayoutDashboard },
  { label: "配置", href: "/admin/email-config", icon: Cog, permissions: ["config:read"] },
  { label: "退出登录", href: "/login", icon: LogOut },
];

/**
 * 通配符权限匹配
 * 
 * 支持 * 通配符，例如：
 * - user:* 匹配 user:read, user:write 等
 * - projectA:queue:* 匹配 projectA:queue:read 等
 */
function matchWildcard(userPerms: string[], required: string): boolean {
  for (const perm of userPerms) {
    if (!perm.includes('*')) continue;
    // 将通配符转换为正则表达式
    const escaped = perm.replace(/[.+?^${}()|[\]\\]/g, '\\$&');
    const pattern = new RegExp('^' + escaped.replace(/\*/g, '.*') + '$');
    if (pattern.test(required)) return true;
  }
  return false;
}

/**
 * 检查用户是否拥有指定权限（支持通配符）
 */
function hasPermission(userPermissions: Set<string>, userPermsArray: string[], required: string): boolean {
  // 精确匹配
  if (userPermissions.has(required)) return true;
  // 通配符匹配
  return matchWildcard(userPermsArray, required);
}

/**
 * 解析权限表达式
 * 
 * 支持 AND 逻辑，如 "user:read AND role:read"
 * 
 * @param expression 权限表达式
 * @returns 权限列表
 */
export function parsePermissionExpression(expression: string): string[] {
  return expression
    .split(/\s+AND\s+/i)
    .map(p => p.trim())
    .filter(p => p.length > 0);
}

/**
 * 评估权限表达式
 * 
 * @param expression 权限表达式（如 "user:read AND role:read"）
 * @param userPermissions 用户权限集合
 * @returns 是否满足表达式
 */
export function evaluatePermissionExpression(
  expression: string,
  userPermissions: Set<string>
): boolean {
  const required = parsePermissionExpression(expression);
  const userPermsArray = Array.from(userPermissions);
  // AND 逻辑：所有权限都必须满足
  return required.every(perm => hasPermission(userPermissions, userPermsArray, perm));
}

/**
 * 根据用户权限过滤导航项
 * 
 * @param items 导航项列表
 * @param userPermissions 用户权限集合
 * @returns 过滤后的导航项列表
 */
export function filterNavItemsByPermissions(
  items: NavItem[],
  userPermissions: Set<string>
): NavItem[] {
  const userPermsArray = Array.from(userPermissions);

  return items.filter((item) => {
    // 检查权限表达式
    if (item.permissionExpression) {
      return evaluatePermissionExpression(item.permissionExpression, userPermissions);
    }

    // 没有权限要求的菜单项始终显示
    if (!item.permissions || item.permissions.length === 0) {
      return true;
    }

    const mode = item.permissionMode || 'any';

    if (mode === 'all') {
      // 需要所有权限
      return item.permissions.every(perm => hasPermission(userPermissions, userPermsArray, perm));
    } else {
      // 有任意一个权限即可显示
      return item.permissions.some(perm => hasPermission(userPermissions, userPermsArray, perm));
    }
  });
}

/**
 * 根据用户权限过滤导航分组
 * 
 * @param groups 导航分组列表
 * @param userPermissions 用户权限集合
 * @returns 过滤后的导航分组列表（空分组会被隐藏）
 */
export function filterNavGroupsByPermissions(
  groups: NavGroup[],
  userPermissions: Set<string>
): NavGroup[] {
  const userPermsArray = Array.from(userPermissions);

  return groups
    .map((group) => {
      // 检查分组级别的权限
      if (group.permissions && group.permissions.length > 0) {
        const mode = group.permissionMode || 'any';
        let hasGroupPermission: boolean;

        if (mode === 'all') {
          hasGroupPermission = group.permissions.every(perm =>
            hasPermission(userPermissions, userPermsArray, perm)
          );
        } else {
          hasGroupPermission = group.permissions.some(perm =>
            hasPermission(userPermissions, userPermsArray, perm)
          );
        }

        if (!hasGroupPermission) {
          return null;
        }
      }

      // 过滤分组内的菜单项
      const filteredItems = filterNavItemsByPermissions(
        group.items,
        userPermissions
      );

      // 如果分组内没有可见的菜单项，隐藏整个分组
      if (filteredItems.length === 0) {
        return null;
      }

      return {
        ...group,
        items: filteredItems,
      };
    })
    .filter((group): group is NavGroup => group !== null);
}
