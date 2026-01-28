"use client";

import { useMemo } from "react";
import { usePermissions } from "@/contexts/PermissionContext";

// ============================================================================
// Types
// ============================================================================

/**
 * 操作权限标志接口
 * 
 * 提供常见 CRUD 操作的权限检查结果
 */
export interface ActionPermissions {
  /** 是否有创建权限 */
  canCreate: boolean;
  /** 是否有查看权限 */
  canRead: boolean;
  /** 是否有编辑权限 */
  canUpdate: boolean;
  /** 是否有删除权限 */
  canDelete: boolean;
  /** 是否有执行权限 */
  canExecute: boolean;
  /** 是否有导出权限 */
  canExport: boolean;
}

// ============================================================================
// Hook
// ============================================================================

/**
 * 操作权限 Hook
 * 
 * 用于按钮级别权限控制，返回指定模块的各种操作权限标志。
 * 
 * @param module - 模块名称，如 'user', 'role', 'queue' 等
 * @param project - 可选的项目作用域
 * @returns ActionPermissions 对象，包含各操作的权限标志
 * 
 * @example
 * ```tsx
 * function UserManagementPage() {
 *   const { canCreate, canUpdate, canDelete } = useActionPermissions('user');
 *   
 *   return (
 *     <div>
 *       {canCreate && <Button onClick={handleCreate}>创建用户</Button>}
 *       
 *       <Table>
 *         {users.map(user => (
 *           <TableRow key={user.id}>
 *             <TableCell>{user.name}</TableCell>
 *             <TableCell>
 *               {canUpdate && <Button onClick={() => handleEdit(user)}>编辑</Button>}
 *               {canDelete && <Button onClick={() => handleDelete(user)}>删除</Button>}
 *             </TableCell>
 *           </TableRow>
 *         ))}
 *       </Table>
 *     </div>
 *   );
 * }
 * ```
 * 
 * @example
 * ```tsx
 * // 带项目作用域的使用
 * function QueueManagementPage({ projectId }: { projectId: string }) {
 *   const { canCreate, canRead, canExecute } = useActionPermissions('queue', projectId);
 *   
 *   return (
 *     <div>
 *       {canRead && <QueueList />}
 *       {canCreate && <CreateQueueButton />}
 *       {canExecute && <ExecuteQueueButton />}
 *     </div>
 *   );
 * }
 * ```
 * 
 * **Validates: Requirements 8.6**
 */
export function useActionPermissions(module: string, project?: string): ActionPermissions {
  const { hasPermission } = usePermissions();

  return useMemo(
    () => ({
      canCreate: hasPermission(`${module}:create`, project),
      canRead: hasPermission(`${module}:read`, project),
      canUpdate: hasPermission(`${module}:update`, project),
      canDelete: hasPermission(`${module}:delete`, project),
      canExecute: hasPermission(`${module}:execute`, project),
      canExport: hasPermission(`${module}:export`, project),
    }),
    [module, project, hasPermission]
  );
}

// ============================================================================
// Exports
// ============================================================================

export default useActionPermissions;
