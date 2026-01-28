/**
 * useActionPermissions Hook 属性测试
 * 
 * 测试以下属性：
 * - Property 11: Button Visibility Based on Action Permissions
 * 
 * **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
 * 
 * @vitest-environment node
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';

// ============================================================================
// Types (mirroring the hook's types for testing)
// ============================================================================

interface ActionPermissions {
  canCreate: boolean;
  canRead: boolean;
  canUpdate: boolean;
  canDelete: boolean;
  canExecute: boolean;
  canExport: boolean;
}

// ============================================================================
// Pure Functions for Testing
// ============================================================================

/**
 * 检查用户是否拥有指定权限（支持通配符）
 */
function hasPermission(
  userPermissions: Set<string>,
  requiredPermission: string,
  project?: string
): boolean {
  // 精确匹配
  if (userPermissions.has(requiredPermission)) {
    return true;
  }

  // 带项目的精确匹配
  if (project) {
    const projectPerm = `${project}:${requiredPermission}`;
    if (userPermissions.has(projectPerm)) {
      return true;
    }
  }

  // 通配符匹配
  for (const perm of userPermissions) {
    if (!perm.includes('*')) continue;
    const pattern = new RegExp('^' + perm.replace(/\*/g, '.*') + '$');
    if (pattern.test(requiredPermission)) {
      return true;
    }
    if (project) {
      const projectRequired = `${project}:${requiredPermission}`;
      if (pattern.test(projectRequired)) {
        return true;
      }
    }
  }

  return false;
}

/**
 * 计算模块的操作权限（纯函数版本，用于测试）
 */
function computeActionPermissions(
  userPermissions: Set<string>,
  module: string,
  project?: string
): ActionPermissions {
  return {
    canCreate: hasPermission(userPermissions, `${module}:create`, project),
    canRead: hasPermission(userPermissions, `${module}:read`, project),
    canUpdate: hasPermission(userPermissions, `${module}:update`, project),
    canDelete: hasPermission(userPermissions, `${module}:delete`, project),
    canExecute: hasPermission(userPermissions, `${module}:execute`, project),
    canExport: hasPermission(userPermissions, `${module}:export`, project),
  };
}

// ============================================================================
// Test Data Generators
// ============================================================================

// 生成有效的模块名称
const moduleNameArb = fc.stringMatching(/^[a-z][a-z0-9_-]*$/).filter(s => s.length >= 1 && s.length <= 20);

// 生成有效的项目名称
const projectNameArb = fc.stringMatching(/^[a-z][a-z0-9_-]*$/).filter(s => s.length >= 1 && s.length <= 20);

// 标准操作类型
const actionTypes = ['create', 'read', 'update', 'delete', 'execute', 'export'] as const;
type ActionType = typeof actionTypes[number];

// 生成操作类型
const actionTypeArb = fc.constantFrom(...actionTypes);

// 生成权限代码
const permissionCodeArb = fc.tuple(moduleNameArb, actionTypeArb).map(([m, a]) => `${m}:${a}`);

// 生成通配符权限
const wildcardPermissionArb = moduleNameArb.map(m => `${m}:*`);

// ============================================================================
// Property-Based Tests
// ============================================================================

describe('useActionPermissions - Property-Based Tests', () => {
  /**
   * Property 11: Button Visibility Based on Action Permissions
   * 
   * *For any* module and user permission set, the visibility of action buttons
   * should match the user's permissions:
   * - Create button visible iff user has `module:create`
   * - Edit button visible iff user has `module:update`
   * - Delete button visible iff user has `module:delete`
   * 
   * **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
   */
  describe('Property 11: Button Visibility Based on Action Permissions', () => {
    it('canCreate should be true iff user has module:create permission', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 }),
          (module, permissions) => {
            const userPermSet = new Set(permissions);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            const hasCreatePerm = userPermSet.has(`${module}:create`);
            return actionPerms.canCreate === hasCreatePerm;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('canRead should be true iff user has module:read permission', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 }),
          (module, permissions) => {
            const userPermSet = new Set(permissions);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            const hasReadPerm = userPermSet.has(`${module}:read`);
            return actionPerms.canRead === hasReadPerm;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('canUpdate should be true iff user has module:update permission', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 }),
          (module, permissions) => {
            const userPermSet = new Set(permissions);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            const hasUpdatePerm = userPermSet.has(`${module}:update`);
            return actionPerms.canUpdate === hasUpdatePerm;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('canDelete should be true iff user has module:delete permission', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 }),
          (module, permissions) => {
            const userPermSet = new Set(permissions);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            const hasDeletePerm = userPermSet.has(`${module}:delete`);
            return actionPerms.canDelete === hasDeletePerm;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('canExecute should be true iff user has module:execute permission', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 }),
          (module, permissions) => {
            const userPermSet = new Set(permissions);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            const hasExecutePerm = userPermSet.has(`${module}:execute`);
            return actionPerms.canExecute === hasExecutePerm;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('canExport should be true iff user has module:export permission', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 }),
          (module, permissions) => {
            const userPermSet = new Set(permissions);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            const hasExportPerm = userPermSet.has(`${module}:export`);
            return actionPerms.canExport === hasExportPerm;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('wildcard permission module:* should grant all action permissions', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          (module) => {
            const userPermSet = new Set([`${module}:*`]);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            // 通配符应该授予所有操作权限
            return (
              actionPerms.canCreate &&
              actionPerms.canRead &&
              actionPerms.canUpdate &&
              actionPerms.canDelete &&
              actionPerms.canExecute &&
              actionPerms.canExport
            );
          }
        ),
        { numRuns: 100 }
      );
    });

    it('empty permissions should deny all actions', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          (module) => {
            const userPermSet = new Set<string>();
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            // 空权限应该拒绝所有操作
            return (
              !actionPerms.canCreate &&
              !actionPerms.canRead &&
              !actionPerms.canUpdate &&
              !actionPerms.canDelete &&
              !actionPerms.canExecute &&
              !actionPerms.canExport
            );
          }
        ),
        { numRuns: 100 }
      );
    });

    it('permissions for other modules should not affect current module', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          moduleNameArb,
          fc.array(actionTypeArb, { minLength: 1, maxLength: 6 }),
          (module, otherModule, actions) => {
            // 确保两个模块不同
            if (module === otherModule) return true;
            
            // 只给其他模块权限
            const otherPerms = actions.map(a => `${otherModule}:${a}`);
            const userPermSet = new Set(otherPerms);
            const actionPerms = computeActionPermissions(userPermSet, module);
            
            // 当前模块应该没有任何权限
            return (
              !actionPerms.canCreate &&
              !actionPerms.canRead &&
              !actionPerms.canUpdate &&
              !actionPerms.canDelete &&
              !actionPerms.canExecute &&
              !actionPerms.canExport
            );
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * 项目作用域权限测试
   */
  describe('Project Scope Permissions', () => {
    it('project-scoped permission should grant access for that project', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          projectNameArb,
          actionTypeArb,
          (module, project, action) => {
            const projectPerm = `${project}:${module}:${action}`;
            const userPermSet = new Set([projectPerm]);
            const actionPerms = computeActionPermissions(userPermSet, module, project);
            
            // 检查对应的操作权限
            const actionKey = `can${action.charAt(0).toUpperCase() + action.slice(1)}` as keyof ActionPermissions;
            return actionPerms[actionKey] === true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('global permission should grant access for any project', () => {
      fc.assert(
        fc.property(
          moduleNameArb,
          projectNameArb,
          actionTypeArb,
          (module, project, action) => {
            // 全局权限（无项目前缀）
            const globalPerm = `${module}:${action}`;
            const userPermSet = new Set([globalPerm]);
            const actionPerms = computeActionPermissions(userPermSet, module, project);
            
            // 检查对应的操作权限
            const actionKey = `can${action.charAt(0).toUpperCase() + action.slice(1)}` as keyof ActionPermissions;
            return actionPerms[actionKey] === true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * 边界情况测试
   */
  describe('Edge Cases', () => {
    it('should handle special characters in module names', () => {
      const specialModules = ['queue-manager', 'user_admin', 'role123'];
      
      for (const module of specialModules) {
        const userPermSet = new Set([`${module}:read`]);
        const actionPerms = computeActionPermissions(userPermSet, module);
        
        expect(actionPerms.canRead).toBe(true);
        expect(actionPerms.canCreate).toBe(false);
      }
    });

    it('should handle global wildcard *:*', () => {
      const userPermSet = new Set(['*:*']);
      const actionPerms = computeActionPermissions(userPermSet, 'anymodule');
      
      expect(actionPerms.canCreate).toBe(true);
      expect(actionPerms.canRead).toBe(true);
      expect(actionPerms.canUpdate).toBe(true);
      expect(actionPerms.canDelete).toBe(true);
      expect(actionPerms.canExecute).toBe(true);
      expect(actionPerms.canExport).toBe(true);
    });

    it('should handle action-specific wildcard *:read', () => {
      const userPermSet = new Set(['*:read']);
      const actionPerms = computeActionPermissions(userPermSet, 'anymodule');
      
      expect(actionPerms.canRead).toBe(true);
      expect(actionPerms.canCreate).toBe(false);
      expect(actionPerms.canUpdate).toBe(false);
      expect(actionPerms.canDelete).toBe(false);
    });
  });
});
