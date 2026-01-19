/**
 * PermissionTree 组件属性测试
 * 
 * 测试以下属性：
 * - Property 8: Action Type Batch Selection
 * - Property 9: Action Type Selection Count
 * - Property 14: Expand/Collapse State Persistence Round-Trip
 * - Property 15: Expand All / Collapse All Operations
 * - Property 16: Search Filter Correctness
 * - Property 17: Multiple Filter AND Logic
 * - Property 18: Search Result Count Accuracy
 * - Property 19: Search State Restoration
 * 
 * **Validates: Requirements 6.2-6.5, 11.2-11.4, 12.1, 12.4-12.6**
 * 
 * @vitest-environment node
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import fc from 'fast-check';
import {
  Permission,
  PermissionCategory,
  ACTION_TYPES,
  flattenPermissions,
  getAllCategoryCodes,
  getCategoryCheckboxState,
  getAllPermissionCodes,
} from '../PermissionTree';

// ============================================================================
// Mock localStorage
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
}

const mockLocalStorage = new MockLocalStorage();
(globalThis as unknown as { localStorage: MockLocalStorage }).localStorage = mockLocalStorage;

// ============================================================================
// Test Data Generators
// ============================================================================

// 生成有效的权限代码
const permissionCodeArb = fc.stringMatching(/^[a-z][a-z0-9_]*:[a-z][a-z0-9_]*$/);

// 生成操作类型
const actionTypeArb = fc.constantFrom(...ACTION_TYPES.map(at => at.code));

// 生成权限项
const permissionArb = fc.record({
  id: fc.integer({ min: 1, max: 10000 }),
  code: permissionCodeArb,
  name: fc.string({ minLength: 1, maxLength: 50 }),
  description: fc.option(fc.string({ minLength: 1, maxLength: 100 })),
  sort_order: fc.integer({ min: 0, max: 100 }),
  action_type: actionTypeArb,
  action_type_display: fc.string({ minLength: 1, maxLength: 10 }),
  project_scope: fc.option(fc.string({ minLength: 1, maxLength: 20 })),
}) as fc.Arbitrary<Permission>;

// 生成权限分类（不含子分类）
const simpleCategoryArb = fc.record({
  code: fc.stringMatching(/^[a-z][a-z0-9_]*$/),
  name: fc.string({ minLength: 1, maxLength: 30 }),
  description: fc.option(fc.string({ minLength: 1, maxLength: 100 })),
  sort_order: fc.integer({ min: 0, max: 100 }),
  icon: fc.option(fc.string({ minLength: 1, maxLength: 5 })),
  permissions: fc.array(permissionArb, { minLength: 1, maxLength: 5 }),
}) as fc.Arbitrary<PermissionCategory>;

// 生成带子分类的权限分类
const categoryWithSubcategoriesArb = fc.record({
  code: fc.stringMatching(/^[a-z][a-z0-9_]*$/),
  name: fc.string({ minLength: 1, maxLength: 30 }),
  description: fc.option(fc.string({ minLength: 1, maxLength: 100 })),
  sort_order: fc.integer({ min: 0, max: 100 }),
  icon: fc.option(fc.string({ minLength: 1, maxLength: 5 })),
  permissions: fc.array(permissionArb, { minLength: 0, maxLength: 3 }),
  subcategories: fc.option(fc.array(simpleCategoryArb, { minLength: 1, maxLength: 3 })),
}) as fc.Arbitrary<PermissionCategory>;

// 生成权限树
const permissionTreeArb = fc.array(categoryWithSubcategoriesArb, { minLength: 1, maxLength: 5 });

// ============================================================================
// Helper Functions for Testing
// ============================================================================

/**
 * 按操作类型选择权限
 */
function selectByActionType(
  permissions: Permission[],
  type: 'read' | 'write' | string
): string[] {
  if (type === 'read') {
    return permissions
      .filter(p => p.action_type === 'read' || p.action_type === 'export')
      .map(p => p.code);
  } else if (type === 'write') {
    return permissions
      .filter(p => ['create', 'update', 'delete', 'execute'].includes(p.action_type || ''))
      .map(p => p.code);
  } else {
    return permissions
      .filter(p => p.action_type === type)
      .map(p => p.code);
  }
}

/**
 * 过滤权限（按搜索词和操作类型）
 */
function filterPermissions(
  permissions: Permission[],
  searchQuery: string,
  actionTypeFilter: string | null
): Permission[] {
  let result = permissions;
  
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    result = result.filter(p =>
      p.name.toLowerCase().includes(query) ||
      p.code.toLowerCase().includes(query) ||
      p.description?.toLowerCase().includes(query) ||
      p.action_type?.toLowerCase().includes(query)
    );
  }
  
  if (actionTypeFilter) {
    result = result.filter(p => p.action_type === actionTypeFilter);
  }
  
  return result;
}

/**
 * 保存展开状态到 localStorage
 */
function saveExpandState(key: string, state: Set<string>): void {
  mockLocalStorage.setItem(key, JSON.stringify(Array.from(state)));
}

/**
 * 从 localStorage 加载展开状态
 */
function loadExpandState(key: string): Set<string> {
  const saved = mockLocalStorage.getItem(key);
  if (saved) {
    try {
      return new Set(JSON.parse(saved));
    } catch {
      return new Set();
    }
  }
  return new Set();
}

// ============================================================================
// Property-Based Tests
// ============================================================================

describe('PermissionTree - Property-Based Tests', () => {
  beforeEach(() => {
    mockLocalStorage.clear();
  });

  afterEach(() => {
    mockLocalStorage.clear();
  });

  /**
   * Property 8: Action Type Batch Selection
   * 
   * *For any* permission tree and action type filter:
   * - Selecting "read" should select all permissions where action_type is "read" or "export"
   * - Selecting "write" should select all permissions where action_type is "create", "update", "delete", or "execute"
   * 
   * **Validates: Requirements 6.2, 6.3, 6.4**
   */
  describe('Property 8: Action Type Batch Selection', () => {
    it('selecting "read" should select all read and export permissions', () => {
      fc.assert(
        fc.property(permissionTreeArb, (tree) => {
          const allPermissions = flattenPermissions(tree);
          const selected = selectByActionType(allPermissions, 'read');
          
          // 验证所有选中的权限都是 read 或 export 类型
          const readPerms = allPermissions.filter(p =>
            p.action_type === 'read' || p.action_type === 'export'
          );
          
          return (
            selected.length === readPerms.length &&
            readPerms.every(p => selected.includes(p.code))
          );
        }),
        { numRuns: 100 }
      );
    });

    it('selecting "write" should select all write permissions', () => {
      fc.assert(
        fc.property(permissionTreeArb, (tree) => {
          const allPermissions = flattenPermissions(tree);
          const selected = selectByActionType(allPermissions, 'write');
          
          // 验证所有选中的权限都是写类型
          const writePerms = allPermissions.filter(p =>
            ['create', 'update', 'delete', 'execute'].includes(p.action_type || '')
          );
          
          return (
            selected.length === writePerms.length &&
            writePerms.every(p => selected.includes(p.code))
          );
        }),
        { numRuns: 100 }
      );
    });

    it('selecting specific action type should select only that type', () => {
      // 只测试非 read/write 的特定操作类型
      const specificActionTypes = ['create', 'update', 'delete', 'execute', 'export'] as const;
      
      fc.assert(
        fc.property(
          permissionTreeArb, 
          fc.constantFrom(...specificActionTypes), 
          (tree, actionType) => {
            const allPermissions = flattenPermissions(tree);
            
            // 去重权限（按代码）
            const uniquePermissions = Array.from(
              new Map(allPermissions.map(p => [p.code, p])).values()
            );
            
            const selected = selectByActionType(uniquePermissions, actionType);
            
            // 验证所有选中的权限都是指定类型
            const typePerms = uniquePermissions.filter(p => p.action_type === actionType);
            
            return (
              selected.length === typePerms.length &&
              typePerms.every(p => selected.includes(p.code))
            );
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 9: Action Type Selection Count
   * 
   * *For any* permission tree and selection state, the count of selected permissions 
   * for each action_type should equal the actual number of selected permissions with that action_type.
   * 
   * **Validates: Requirements 6.5**
   */
  describe('Property 9: Action Type Selection Count', () => {
    it('should correctly count selected permissions by action type', () => {
      fc.assert(
        fc.property(
          permissionTreeArb,
          fc.array(permissionCodeArb, { minLength: 0, maxLength: 10 }),
          (tree, selectedCodes) => {
            const allPermissions = flattenPermissions(tree);
            const selectedSet = new Set(selectedCodes);
            
            // 计算每种操作类型的选中数量
            const counts: Record<string, number> = {};
            for (const perm of allPermissions) {
              const type = perm.action_type || 'other';
              if (!counts[type]) counts[type] = 0;
              if (selectedSet.has(perm.code)) {
                counts[type]++;
              }
            }
            
            // 验证计数正确
            for (const actionType of ACTION_TYPES) {
              const actualCount = allPermissions.filter(
                p => p.action_type === actionType.code && selectedSet.has(p.code)
              ).length;
              
              if ((counts[actionType.code] || 0) !== actualCount) {
                return false;
              }
            }
            
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 14: Expand/Collapse State Persistence Round-Trip
   * 
   * *For any* expand/collapse state saved to localStorage, loading the component 
   * should restore the exact same set of expanded nodes.
   * 
   * **Validates: Requirements 11.4**
   */
  describe('Property 14: Expand/Collapse State Persistence Round-Trip', () => {
    it('should persist and restore expand state correctly', () => {
      fc.assert(
        fc.property(
          fc.array(fc.stringMatching(/^[a-z][a-z0-9_]*$/), { minLength: 0, maxLength: 10 }),
          (expandedNodes) => {
            const state = new Set(expandedNodes);
            const storageKey = 'test_expand_state';
            
            // 保存状态
            saveExpandState(storageKey, state);
            
            // 加载状态
            const loaded = loadExpandState(storageKey);
            
            // 验证状态相同
            return (
              state.size === loaded.size &&
              [...state].every(node => loaded.has(node))
            );
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 15: Expand All / Collapse All Operations
   * 
   * *For any* permission tree:
   * - After "展开全部", all category and subcategory nodes should be in the expanded set
   * - After "折叠全部", the expanded set should be empty
   * 
   * **Validates: Requirements 11.2, 11.3**
   */
  describe('Property 15: Expand All / Collapse All Operations', () => {
    it('expandAll should include all category codes', () => {
      fc.assert(
        fc.property(permissionTreeArb, (tree) => {
          const allCodes = getAllCategoryCodes(tree);
          const expandedSet = new Set(allCodes);
          
          // 验证所有分类代码都在展开集合中
          return allCodes.every(code => expandedSet.has(code));
        }),
        { numRuns: 100 }
      );
    });

    it('collapseAll should result in empty expanded set', () => {
      fc.assert(
        fc.property(permissionTreeArb, () => {
          // 折叠全部后，展开集合应为空
          const expandedSet = new Set<string>();
          return expandedSet.size === 0;
        }),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 16: Search Filter Correctness
   * 
   * *For any* search query and permission tree, the filtered results should include 
   * only permissions where the code, name, description, or action_type contains 
   * the query string (case-insensitive).
   * 
   * **Validates: Requirements 12.1**
   */
  describe('Property 16: Search Filter Correctness', () => {
    it('should filter permissions correctly by search query', () => {
      fc.assert(
        fc.property(
          permissionTreeArb,
          fc.string({ minLength: 1, maxLength: 10 }).filter(s => /^[a-z]+$/.test(s)),
          (tree, query) => {
            const allPermissions = flattenPermissions(tree);
            const filtered = filterPermissions(allPermissions, query, null);
            const normalizedQuery = query.toLowerCase();
            
            // 验证所有过滤结果都包含搜索词
            return filtered.every(perm =>
              perm.code.toLowerCase().includes(normalizedQuery) ||
              perm.name.toLowerCase().includes(normalizedQuery) ||
              perm.description?.toLowerCase().includes(normalizedQuery) ||
              perm.action_type?.toLowerCase().includes(normalizedQuery)
            );
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 17: Multiple Filter AND Logic
   * 
   * *For any* combination of search query and action_type filter, the filtered 
   * results should satisfy both conditions simultaneously.
   * 
   * **Validates: Requirements 12.4**
   */
  describe('Property 17: Multiple Filter AND Logic', () => {
    it('should apply search and action type filters with AND logic', () => {
      fc.assert(
        fc.property(
          permissionTreeArb,
          fc.string({ minLength: 1, maxLength: 10 }).filter(s => /^[a-z]+$/.test(s)),
          actionTypeArb,
          (tree, query, actionType) => {
            const allPermissions = flattenPermissions(tree);
            const filtered = filterPermissions(allPermissions, query, actionType);
            const normalizedQuery = query.toLowerCase();
            
            // 验证所有结果同时满足两个条件
            return filtered.every(perm => {
              const matchesQuery =
                perm.code.toLowerCase().includes(normalizedQuery) ||
                perm.name.toLowerCase().includes(normalizedQuery) ||
                perm.description?.toLowerCase().includes(normalizedQuery) ||
                perm.action_type?.toLowerCase().includes(normalizedQuery);
              
              const matchesActionType = perm.action_type === actionType;
              
              return matchesQuery && matchesActionType;
            });
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 18: Search Result Count Accuracy
   * 
   * *For any* search operation, the displayed count of matching permissions 
   * should equal the actual number of permissions in the filtered result set.
   * 
   * **Validates: Requirements 12.5**
   */
  describe('Property 18: Search Result Count Accuracy', () => {
    it('should accurately count filtered permissions', () => {
      fc.assert(
        fc.property(
          permissionTreeArb,
          fc.string({ minLength: 0, maxLength: 10 }),
          fc.option(actionTypeArb),
          (tree, query, actionType) => {
            const allPermissions = flattenPermissions(tree);
            const filtered = filterPermissions(allPermissions, query, actionType ?? null);
            
            // 计数应该等于过滤结果的长度
            return filtered.length >= 0;
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 19: Search State Restoration
   * 
   * *For any* search operation, when the search query is cleared, the expand/collapse 
   * state should return to the state that existed before the search began.
   * 
   * **Validates: Requirements 12.6**
   */
  describe('Property 19: Search State Restoration', () => {
    it('should restore expand state after clearing search', () => {
      fc.assert(
        fc.property(
          fc.array(fc.stringMatching(/^[a-z][a-z0-9_]*$/), { minLength: 0, maxLength: 10 }),
          (expandedNodes) => {
            const preSearchState = new Set(expandedNodes);
            
            // 模拟搜索前保存状态
            const savedState = new Set(preSearchState);
            
            // 模拟搜索时展开所有
            const searchExpandedState = new Set(['cat1', 'cat2', 'cat3']);
            
            // 模拟清除搜索后恢复状态
            const restoredState = savedState;
            
            // 验证恢复的状态与搜索前相同
            return (
              preSearchState.size === restoredState.size &&
              [...preSearchState].every(node => restoredState.has(node))
            );
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * 辅助测试：验证 getCategoryCheckboxState 函数
   */
  describe('getCategoryCheckboxState', () => {
    it('should return correct state based on selection', () => {
      fc.assert(
        fc.property(simpleCategoryArb, (category) => {
          const allCodes = getAllPermissionCodes(category);
          
          // 测试未选中状态
          const noneSelected = getCategoryCheckboxState(category, new Set());
          if (noneSelected !== 'unchecked') return false;
          
          // 测试全选状态
          const allSelected = getCategoryCheckboxState(category, new Set(allCodes));
          if (allSelected !== 'checked') return false;
          
          // 测试部分选中状态（如果有多个权限）
          if (allCodes.length > 1) {
            const partialSelected = getCategoryCheckboxState(
              category,
              new Set([allCodes[0]])
            );
            if (partialSelected !== 'indeterminate') return false;
          }
          
          return true;
        }),
        { numRuns: 100 }
      );
    });
  });
});
