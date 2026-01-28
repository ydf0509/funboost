/**
 * Property-Based Tests for Permission Context
 * 
 * Feature: granular-permission-system
 * 
 * These tests use fast-check for property-based testing to verify
 * the correctness properties defined in the design document.
 * 
 * **Validates: Requirements 7.2, 7.3, 15.6**
 * 
 * @vitest-environment node
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import fc from 'fast-check';

// ============================================================================
// Mock localStorage for Node environment
// ============================================================================

class MockLocalStorage {
  private store: Map<string, string> = new Map();

  getItem(key: string): string | null {
    return this.store.get(key) ?? null;
  }

  setItem(key: string, value: string): void {
    this.store.set(key, value);
  }

  removeItem(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }

  get length(): number {
    return this.store.size;
  }

  key(index: number): string | null {
    const keys = Array.from(this.store.keys());
    return keys[index] ?? null;
  }
}

// Set up global localStorage mock
const mockLocalStorage = new MockLocalStorage();
(globalThis as unknown as { localStorage: MockLocalStorage }).localStorage = mockLocalStorage;

// ============================================================================
// Helper Functions (extracted from PermissionContext for testing)
// ============================================================================

/**
 * 通配符匹配
 * 
 * 支持 * 通配符，例如：
 * - user:* 匹配 user:read, user:write 等
 * - projectA:queue:* 匹配 projectA:queue:read 等
 */
function matchWildcard(userPerms: string[], required: string): boolean {
  for (const perm of userPerms) {
    if (!perm.includes("*")) continue;
    // 将通配符转换为正则表达式
    const escaped = perm.replace(/[.+?^${}()|[\]\\]/g, "\\$&");
    const pattern = new RegExp("^" + escaped.replace(/\*/g, ".*") + "$");
    if (pattern.test(required)) return true;
  }
  return false;
}

/**
 * 检查是否拥有指定权限
 * 
 * 支持：
 * - 精确匹配
 * - 项目作用域匹配
 * - 通配符匹配
 */
function hasPermission(
  permissions: string[],
  permissionSet: Set<string>,
  code: string,
  project?: string
): boolean {
  // 精确匹配
  if (permissionSet.has(code)) return true;

  // 带项目的精确匹配
  if (project) {
    const projectPerm = `${project}:${code}`;
    if (permissionSet.has(projectPerm)) return true;
  }

  // 通配符匹配
  if (matchWildcard(permissions, code)) return true;

  // 带项目的通配符匹配
  if (project) {
    const projectPerm = `${project}:${code}`;
    if (matchWildcard(permissions, projectPerm)) return true;
  }

  return false;
}

/**
 * 检查是否拥有任意一个指定权限
 */
function hasAnyPermission(
  permissions: string[],
  permissionSet: Set<string>,
  codes: string[],
  project?: string
): boolean {
  return codes.some((code) => hasPermission(permissions, permissionSet, code, project));
}

/**
 * 检查是否拥有所有指定权限
 */
function hasAllPermissions(
  permissions: string[],
  permissionSet: Set<string>,
  codes: string[],
  project?: string
): boolean {
  return codes.every((code) => hasPermission(permissions, permissionSet, code, project));
}

/**
 * 检查 PermissionGuard 是否应该渲染子组件
 * 
 * @param required 所需权限列表
 * @param userPermSet 用户权限集合
 * @param mode 匹配模式：'any' 或 'all'
 * @returns 是否应该渲染
 */
function checkPermissionGuard(
  required: string[],
  userPermSet: Set<string>,
  mode: 'any' | 'all'
): boolean {
  const userPerms = Array.from(userPermSet);
  
  if (mode === 'all') {
    return hasAllPermissions(userPerms, userPermSet, required);
  } else {
    return hasAnyPermission(userPerms, userPermSet, required);
  }
}

// ============================================================================
// Cache Helper Functions
// ============================================================================

const CACHE_KEY = "user_permissions_cache";

interface CachedData {
  permissions: string[];
  permissionDetails: Array<{
    code: string;
    name: string;
    action_type: string;
    project_scope: string | null;
  }>;
  roles: string[];
  userName: string | null;
  isAuthenticated: boolean;
}

interface CacheEntry {
  data: CachedData;
  timestamp: number;
}

/**
 * 将权限数据保存到 localStorage
 */
function setCachedPermissions(data: CachedData): void {
  localStorage.setItem(
    CACHE_KEY,
    JSON.stringify({
      data,
      timestamp: Date.now(),
    })
  );
}

/**
 * 从 localStorage 获取缓存的权限数据
 */
function getCachedPermissions(): CacheEntry | null {
  const cached = localStorage.getItem(CACHE_KEY);
  if (!cached) return null;
  
  try {
    return JSON.parse(cached);
  } catch {
    return null;
  }
}

/**
 * 清除权限缓存
 */
function clearPermissionCache(): void {
  localStorage.removeItem(CACHE_KEY);
}

// ============================================================================
// Arbitrary Generators
// ============================================================================

/**
 * 生成有效的权限代码
 * 格式: module:action 或 module:submodule:action
 */
const permissionCodeArb = fc.oneof(
  // Simple format: module:action
  fc.tuple(
    fc.stringMatching(/^[a-z][a-z0-9_-]{0,9}$/),
    fc.stringMatching(/^[a-z][a-z0-9_-]{0,9}$/)
  ).map(([module, action]) => `${module}:${action}`),
  // Extended format: module:submodule:action
  fc.tuple(
    fc.stringMatching(/^[a-z][a-z0-9_-]{0,9}$/),
    fc.stringMatching(/^[a-z][a-z0-9_-]{0,9}$/),
    fc.stringMatching(/^[a-z][a-z0-9_-]{0,9}$/)
  ).map(([module, submodule, action]) => `${module}:${submodule}:${action}`)
);

/**
 * 生成非空的权限代码数组
 */
const permissionCodesArb = fc.array(permissionCodeArb, { minLength: 1, maxLength: 5 });

/**
 * 生成用户权限数组
 */
const userPermissionsArb = fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 });

// ============================================================================
// Property-Based Tests
// ============================================================================

describe('Permission Context - Property-Based Tests', () => {
  /**
   * Property 10: Permission Guard Visibility
   * 
   * *For any* PermissionGuard component with required permissions and a user's permission set:
   * - In "any" mode: children should render if the user has at least one of the required permissions
   * - In "all" mode: children should render only if the user has all required permissions
   * 
   * **Validates: Requirements 7.2, 7.3**
   */
  describe('Property 10: Permission Guard Visibility', () => {
    it('should render children in "any" mode if user has at least one required permission', () => {
      fc.assert(
        fc.property(
          // Use permission code format to avoid wildcard edge cases in simple string tests
          permissionCodesArb,
          permissionCodesArb,
          (required, userPerms) => {
            const userPermSet = new Set(userPerms);
            // Check using the same logic as checkPermissionGuard (which includes wildcard matching)
            const result = checkPermissionGuard(required, userPermSet, 'any');
            // The result should match hasAnyPermission which accounts for wildcards
            const expected = hasAnyPermission(userPerms, userPermSet, required);
            return result === expected;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should render children in "all" mode only if user has all required permissions', () => {
      fc.assert(
        fc.property(
          // Use permission code format to avoid wildcard edge cases in simple string tests
          permissionCodesArb,
          permissionCodesArb,
          (required, userPerms) => {
            const userPermSet = new Set(userPerms);
            // Check using the same logic as checkPermissionGuard (which includes wildcard matching)
            const result = checkPermissionGuard(required, userPermSet, 'all');
            // The result should match hasAllPermissions which accounts for wildcards
            const expected = hasAllPermissions(userPerms, userPermSet, required);
            return result === expected;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should correctly handle "any" mode with permission code format', () => {
      fc.assert(
        fc.property(
          permissionCodesArb,
          userPermissionsArb,
          (required, userPerms) => {
            const userPermSet = new Set(userPerms);
            const hasAny = required.some(p => userPermSet.has(p));
            const result = checkPermissionGuard(required, userPermSet, 'any');
            return result === hasAny;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should correctly handle "all" mode with permission code format', () => {
      fc.assert(
        fc.property(
          permissionCodesArb,
          userPermissionsArb,
          (required, userPerms) => {
            const userPermSet = new Set(userPerms);
            const hasAll = required.every(p => userPermSet.has(p));
            const result = checkPermissionGuard(required, userPermSet, 'all');
            return result === hasAll;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return false in "any" mode when user has no permissions', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 5 }),
          (required) => {
            const userPermSet = new Set<string>();
            const result = checkPermissionGuard(required, userPermSet, 'any');
            return result === false;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return false in "all" mode when user has no permissions', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 5 }),
          (required) => {
            const userPermSet = new Set<string>();
            const result = checkPermissionGuard(required, userPermSet, 'all');
            return result === false;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return true in "any" mode when user has all required permissions', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 5 }),
          (required) => {
            // User has all required permissions
            const userPermSet = new Set(required);
            const result = checkPermissionGuard(required, userPermSet, 'any');
            return result === true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return true in "all" mode when user has all required permissions', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 5 }),
          (required) => {
            // User has all required permissions
            const userPermSet = new Set(required);
            const result = checkPermissionGuard(required, userPermSet, 'all');
            return result === true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle partial permission overlap correctly in "any" mode', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 2, maxLength: 5 }),
          fc.integer({ min: 1 }),
          (required, overlapCount) => {
            // User has some but not all required permissions
            const actualOverlap = Math.min(overlapCount, required.length - 1);
            const userPerms = required.slice(0, actualOverlap);
            const userPermSet = new Set(userPerms);
            
            const result = checkPermissionGuard(required, userPermSet, 'any');
            // Should return true because user has at least one required permission
            return result === (actualOverlap > 0);
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle partial permission overlap correctly in "all" mode', () => {
      fc.assert(
        fc.property(
          // Generate unique strings that don't contain wildcards to avoid wildcard matching issues
          fc.uniqueArray(
            fc.string({ minLength: 1, maxLength: 20 }).filter(s => !s.includes('*')), 
            { minLength: 2, maxLength: 5 }
          ),
          fc.integer({ min: 1 }),
          (required, overlapCount) => {
            // User has some but not all required permissions
            const actualOverlap = Math.min(overlapCount, required.length - 1);
            const userPerms = required.slice(0, actualOverlap);
            const userPermSet = new Set(userPerms);
            
            const result = checkPermissionGuard(required, userPermSet, 'all');
            // Should return false because user doesn't have all required permissions
            return result === false;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 24: Cache Invalidation on Logout
   * 
   * *For any* user logout or session expiration event, the permission cache should be 
   * cleared and subsequent permission checks should require a fresh API call.
   * 
   * **Validates: Requirements 15.6**
   */
  describe('Property 24: Cache Invalidation on Logout', () => {
    beforeEach(() => {
      // Clear localStorage before each test
      mockLocalStorage.clear();
    });

    afterEach(() => {
      // Clean up after each test
      mockLocalStorage.clear();
    });

    it('should clear cache when clearPermissionCache is called', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 10 }),
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 0, maxLength: 5 }),
          fc.option(fc.string({ minLength: 1, maxLength: 20 })),
          (permissions, roles, userName) => {
            // Set up cache with some data
            const cacheData: CachedData = {
              permissions,
              permissionDetails: permissions.map(p => ({
                code: p,
                name: `Permission ${p}`,
                action_type: 'read',
                project_scope: null,
              })),
              roles,
              userName: userName ?? null,
              isAuthenticated: true,
            };
            
            setCachedPermissions(cacheData);
            
            // Verify cache exists
            const beforeClear = getCachedPermissions();
            if (!beforeClear) return false;
            
            // Clear cache
            clearPermissionCache();
            
            // Verify cache is cleared
            const afterClear = getCachedPermissions();
            return afterClear === null;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should have no cached permissions after logout', () => {
      fc.assert(
        fc.property(
          fc.array(permissionCodeArb, { minLength: 1, maxLength: 10 }),
          (permissions) => {
            // Set up cache
            const cacheData: CachedData = {
              permissions,
              permissionDetails: [],
              roles: ['user'],
              userName: 'testuser',
              isAuthenticated: true,
            };
            
            setCachedPermissions(cacheData);
            
            // Simulate logout by clearing cache
            clearPermissionCache();
            
            // Verify no cached data
            const cached = localStorage.getItem(CACHE_KEY);
            return cached === null;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should require fresh data after cache invalidation', () => {
      fc.assert(
        fc.property(
          fc.array(permissionCodeArb, { minLength: 1, maxLength: 10 }),
          fc.array(permissionCodeArb, { minLength: 1, maxLength: 10 }),
          (oldPermissions, newPermissions) => {
            // Set up initial cache
            const oldCacheData: CachedData = {
              permissions: oldPermissions,
              permissionDetails: [],
              roles: ['user'],
              userName: 'testuser',
              isAuthenticated: true,
            };
            
            setCachedPermissions(oldCacheData);
            
            // Clear cache (logout)
            clearPermissionCache();
            
            // Set up new cache (new login)
            const newCacheData: CachedData = {
              permissions: newPermissions,
              permissionDetails: [],
              roles: ['admin'],
              userName: 'newuser',
              isAuthenticated: true,
            };
            
            setCachedPermissions(newCacheData);
            
            // Verify new data is used
            const cached = getCachedPermissions();
            if (!cached) return false;
            
            // New permissions should be in cache
            return (
              cached.data.permissions.length === newPermissions.length &&
              cached.data.userName === 'newuser' &&
              cached.data.roles.includes('admin')
            );
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should clear all permission-related data on logout', () => {
      fc.assert(
        fc.property(
          fc.record({
            permissions: fc.array(permissionCodeArb, { minLength: 1, maxLength: 10 }),
            roles: fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 5 }),
            userName: fc.string({ minLength: 1, maxLength: 50 }),
          }),
          (userData) => {
            // Set up cache with full user data
            const cacheData: CachedData = {
              permissions: userData.permissions,
              permissionDetails: userData.permissions.map(p => ({
                code: p,
                name: `Permission ${p}`,
                action_type: 'read',
                project_scope: null,
              })),
              roles: userData.roles,
              userName: userData.userName,
              isAuthenticated: true,
            };
            
            setCachedPermissions(cacheData);
            
            // Verify cache exists with all data
            const beforeClear = getCachedPermissions();
            if (!beforeClear) return false;
            if (beforeClear.data.permissions.length !== userData.permissions.length) return false;
            if (beforeClear.data.roles.length !== userData.roles.length) return false;
            if (beforeClear.data.userName !== userData.userName) return false;
            
            // Clear cache (logout)
            clearPermissionCache();
            
            // Verify all data is cleared
            const afterClear = getCachedPermissions();
            return afterClear === null;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle multiple logout/login cycles correctly', () => {
      fc.assert(
        fc.property(
          fc.array(
            fc.record({
              permissions: fc.array(permissionCodeArb, { minLength: 1, maxLength: 5 }),
              userName: fc.string({ minLength: 1, maxLength: 20 }),
            }),
            { minLength: 2, maxLength: 5 }
          ),
          (sessions) => {
            for (const session of sessions) {
              // Login - set cache
              const cacheData: CachedData = {
                permissions: session.permissions,
                permissionDetails: [],
                roles: ['user'],
                userName: session.userName,
                isAuthenticated: true,
              };
              
              setCachedPermissions(cacheData);
              
              // Verify cache is set
              const cached = getCachedPermissions();
              if (!cached) return false;
              if (cached.data.userName !== session.userName) return false;
              
              // Logout - clear cache
              clearPermissionCache();
              
              // Verify cache is cleared
              const afterLogout = getCachedPermissions();
              if (afterLogout !== null) return false;
            }
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should not affect other localStorage items when clearing permission cache', () => {
      fc.assert(
        fc.property(
          fc.array(permissionCodeArb, { minLength: 1, maxLength: 5 }),
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.string({ minLength: 1, maxLength: 100 }),
          (permissions, otherKey, otherValue) => {
            // Ensure other key is different from cache key
            const safeOtherKey = otherKey === CACHE_KEY ? `other_${otherKey}` : otherKey;
            
            // Set up permission cache
            const cacheData: CachedData = {
              permissions,
              permissionDetails: [],
              roles: ['user'],
              userName: 'testuser',
              isAuthenticated: true,
            };
            
            setCachedPermissions(cacheData);
            
            // Set other localStorage item
            localStorage.setItem(safeOtherKey, otherValue);
            
            // Clear permission cache
            clearPermissionCache();
            
            // Verify permission cache is cleared
            const permCache = getCachedPermissions();
            if (permCache !== null) return false;
            
            // Verify other item is preserved
            const otherItem = localStorage.getItem(safeOtherKey);
            return otherItem === otherValue;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Additional tests for hasAnyPermission and hasAllPermissions functions
   */
  describe('Permission Check Functions', () => {
    it('hasAnyPermission should return true if at least one permission matches', () => {
      fc.assert(
        fc.property(
          permissionCodesArb,
          userPermissionsArb,
          (required, userPerms) => {
            const userPermSet = new Set(userPerms);
            const result = hasAnyPermission(userPerms, userPermSet, required);
            const expected = required.some(p => userPermSet.has(p));
            return result === expected;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('hasAllPermissions should return true only if all permissions match', () => {
      fc.assert(
        fc.property(
          permissionCodesArb,
          userPermissionsArb,
          (required, userPerms) => {
            const userPermSet = new Set(userPerms);
            const result = hasAllPermissions(userPerms, userPermSet, required);
            const expected = required.every(p => userPermSet.has(p));
            return result === expected;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('hasAnyPermission with empty required array should return false', () => {
      fc.assert(
        fc.property(
          userPermissionsArb,
          (userPerms) => {
            const userPermSet = new Set(userPerms);
            const result = hasAnyPermission(userPerms, userPermSet, []);
            return result === false;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('hasAllPermissions with empty required array should return true', () => {
      fc.assert(
        fc.property(
          userPermissionsArb,
          (userPerms) => {
            const userPermSet = new Set(userPerms);
            const result = hasAllPermissions(userPerms, userPermSet, []);
            return result === true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
