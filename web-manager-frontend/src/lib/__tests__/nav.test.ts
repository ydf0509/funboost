/**
 * 导航权限过滤属性测试
 * 
 * 测试以下属性：
 * - Property 12: Menu Permission Filtering
 * - Property 13: Multiple Permission Expression Evaluation
 * 
 * **Validates: Requirements 9.1, 9.2, 9.3**
 * 
 * @vitest-environment node
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import {
  NavItem,
  NavGroup,
  filterNavItemsByPermissions,
  filterNavGroupsByPermissions,
  parsePermissionExpression,
  evaluatePermissionExpression,
} from '../nav';

// ============================================================================
// Test Data Generators
// ============================================================================

// 生成有效的权限代码
const permissionCodeArb = fc.stringMatching(/^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$/);

// 生成导航项
const navItemArb = fc.record({
  label: fc.string({ minLength: 1, maxLength: 20 }),
  href: fc.stringMatching(/^\/[a-z][a-z0-9-]*$/),
  icon: fc.constant(() => null) as fc.Arbitrary<React.ComponentType<{ className?: string }>>,
  permissions: fc.option(fc.array(permissionCodeArb, { minLength: 1, maxLength: 3 })),
  permissionMode: fc.option(fc.constantFrom('any', 'all') as fc.Arbitrary<'any' | 'all'>),
}) as fc.Arbitrary<NavItem>;

// 生成导航分组
const navGroupArb = fc.record({
  title: fc.string({ minLength: 1, maxLength: 20 }),
  items: fc.array(navItemArb, { minLength: 1, maxLength: 5 }),
  permissions: fc.option(fc.array(permissionCodeArb, { minLength: 1, maxLength: 3 })),
  permissionMode: fc.option(fc.constantFrom('any', 'all') as fc.Arbitrary<'any' | 'all'>),
}) as fc.Arbitrary<NavGroup>;

// ============================================================================
// Property-Based Tests
// ============================================================================

describe('Navigation Permission Filtering - Property-Based Tests', () => {
  /**
   * Property 12: Menu Permission Filtering
   * 
   * *For any* navigation menu and user permission set, if all items in a submenu 
   * are hidden due to permission filtering, the parent menu item should also be hidden.
   * 
   * **Validates: Requirements 9.3**
   */
  describe('Property 12: Menu Permission Filtering', () => {
    it('should hide parent group when all items are filtered out', () => {
      fc.assert(
        fc.property(
          fc.array(navGroupArb, { minLength: 1, maxLength: 5 }),
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 5 }),
          (groups, userPerms) => {
            const userPermSet = new Set(userPerms);
            const filtered = filterNavGroupsByPermissions(groups, userPermSet);
            
            // 验证：如果一个分组被保留，它必须有至少一个可见的菜单项
            for (const group of filtered) {
              if (group.items.length === 0) {
                return false;
              }
            }
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should preserve items without permission requirements', () => {
      fc.assert(
        fc.property(
          fc.array(navGroupArb, { minLength: 1, maxLength: 5 }),
          (groups) => {
            // 空权限集合
            const userPermSet = new Set<string>();
            const filtered = filterNavGroupsByPermissions(groups, userPermSet);
            
            // 统计原始分组中没有权限要求的菜单项数量
            let itemsWithoutPerms = 0;
            for (const group of groups) {
              // 如果分组本身有权限要求，跳过
              if (group.permissions && group.permissions.length > 0) continue;
              
              for (const item of group.items) {
                if (!item.permissions || item.permissions.length === 0) {
                  itemsWithoutPerms++;
                }
              }
            }
            
            // 统计过滤后的菜单项数量
            let filteredItemsCount = 0;
            for (const group of filtered) {
              filteredItemsCount += group.items.length;
            }
            
            // 过滤后的菜单项数量应该等于没有权限要求的菜单项数量
            return filteredItemsCount === itemsWithoutPerms;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should show items when user has required permission', () => {
      fc.assert(
        fc.property(
          navItemArb.filter(item => item.permissions && item.permissions.length > 0),
          (item) => {
            // 用户拥有菜单项要求的所有权限
            const userPermSet = new Set(item.permissions || []);
            const filtered = filterNavItemsByPermissions([item], userPermSet);
            
            // 菜单项应该被保留
            return filtered.length === 1;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should hide items when user lacks all required permissions', () => {
      fc.assert(
        fc.property(
          navItemArb.filter(item => item.permissions && item.permissions.length > 0),
          (item) => {
            // 用户没有任何权限
            const userPermSet = new Set<string>();
            const filtered = filterNavItemsByPermissions([item], userPermSet);
            
            // 菜单项应该被隐藏
            return filtered.length === 0;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 13: Multiple Permission Expression Evaluation
   * 
   * *For any* permission expression with AND logic (e.g., "user:read AND role:read"), 
   * the expression should evaluate to true only if all individual permissions are 
   * present in the user's permission set.
   * 
   * **Validates: Requirements 9.1, 9.2**
   */
  describe('Property 13: Multiple Permission Expression Evaluation', () => {
    it('should parse permission expression correctly', () => {
      fc.assert(
        fc.property(
          fc.array(permissionCodeArb, { minLength: 1, maxLength: 5 }),
          (permissions) => {
            const expression = permissions.join(' AND ');
            const parsed = parsePermissionExpression(expression);
            
            // 解析后的权限数量应该等于原始数量
            return parsed.length === permissions.length;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should evaluate AND expression correctly - all permissions present', () => {
      fc.assert(
        fc.property(
          fc.array(permissionCodeArb, { minLength: 1, maxLength: 5 }),
          (permissions) => {
            const expression = permissions.join(' AND ');
            const userPermSet = new Set(permissions);
            
            // 用户拥有所有权限，表达式应该为 true
            return evaluatePermissionExpression(expression, userPermSet) === true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should evaluate AND expression correctly - missing some permissions', () => {
      fc.assert(
        fc.property(
          fc.array(permissionCodeArb, { minLength: 2, maxLength: 5 }),
          (permissions) => {
            const expression = permissions.join(' AND ');
            // 用户只有第一个权限
            const userPermSet = new Set([permissions[0]]);
            
            // 用户缺少部分权限，表达式应该为 false
            return evaluatePermissionExpression(expression, userPermSet) === false;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should evaluate AND expression correctly - no permissions', () => {
      fc.assert(
        fc.property(
          fc.array(permissionCodeArb, { minLength: 1, maxLength: 5 }),
          (permissions) => {
            const expression = permissions.join(' AND ');
            const userPermSet = new Set<string>();
            
            // 用户没有任何权限，表达式应该为 false
            return evaluatePermissionExpression(expression, userPermSet) === false;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle case-insensitive AND keyword', () => {
      const testCases = [
        'user:read AND role:read',
        'user:read and role:read',
        'user:read And role:read',
      ];
      
      for (const expression of testCases) {
        const parsed = parsePermissionExpression(expression);
        expect(parsed).toHaveLength(2);
        expect(parsed[0]).toBe('user:read');
        expect(parsed[1]).toBe('role:read');
      }
    });
  });

  /**
   * 辅助测试：通配符权限匹配
   */
  describe('Wildcard Permission Matching', () => {
    it('should match wildcard permissions', () => {
      // user:* 应该匹配 user:read
      const userPermSet = new Set(['user:*']);
      const filtered = filterNavItemsByPermissions(
        [{ label: 'Test', href: '/test', icon: () => null, permissions: ['user:read'] }],
        userPermSet
      );
      expect(filtered).toHaveLength(1);
    });

    it('should match exact permissions', () => {
      const userPermSet = new Set(['user:read']);
      const filtered = filterNavItemsByPermissions(
        [{ label: 'Test', href: '/test', icon: () => null, permissions: ['user:read'] }],
        userPermSet
      );
      expect(filtered).toHaveLength(1);
    });

    it('should not match unrelated permissions', () => {
      const userPermSet = new Set(['role:read']);
      const filtered = filterNavItemsByPermissions(
        [{ label: 'Test', href: '/test', icon: () => null, permissions: ['user:read'] }],
        userPermSet
      );
      expect(filtered).toHaveLength(0);
    });
  });

  /**
   * 辅助测试：permissionMode 'all' 模式
   */
  describe('Permission Mode: all', () => {
    it('should require all permissions in "all" mode', () => {
      const userPermSet = new Set(['user:read']);
      const filtered = filterNavItemsByPermissions(
        [{
          label: 'Test',
          href: '/test',
          icon: () => null,
          permissions: ['user:read', 'role:read'],
          permissionMode: 'all',
        }],
        userPermSet
      );
      // 用户只有 user:read，缺少 role:read，应该被隐藏
      expect(filtered).toHaveLength(0);
    });

    it('should show item when user has all permissions in "all" mode', () => {
      const userPermSet = new Set(['user:read', 'role:read']);
      const filtered = filterNavItemsByPermissions(
        [{
          label: 'Test',
          href: '/test',
          icon: () => null,
          permissions: ['user:read', 'role:read'],
          permissionMode: 'all',
        }],
        userPermSet
      );
      expect(filtered).toHaveLength(1);
    });
  });
});
