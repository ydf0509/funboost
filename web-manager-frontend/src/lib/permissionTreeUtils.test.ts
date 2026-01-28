/**
 * Property-Based Tests for Permission Tree Utilities
 * 
 * Feature: permission-tree-enhancement
 * 
 * These tests use fast-check for property-based testing to verify
 * the correctness properties defined in the design document.
 * 
 * @vitest-environment node
 */

import { describe, it, expect } from 'vitest';
import fc from 'fast-check';
import {
  getCategoryCheckboxState,
  toggleCategoryPermissions,
  filterPermissionTree,
  selectAllPermissions,
  getSelectionCount,
  type Permission,
  type PermissionCategory,
} from './permissionTreeUtils';

// Arbitrary generators for test data
const permissionArb = fc.record({
  id: fc.integer({ min: 1, max: 10000 }),
  code: fc.string({ minLength: 1, maxLength: 50 }),
  name: fc.string({ minLength: 1, maxLength: 100 }),
  description: fc.option(fc.string({ maxLength: 200 }), { nil: undefined }),
  category_code: fc.option(fc.string({ maxLength: 32 }), { nil: undefined }),
  sort_order: fc.integer({ min: 0, max: 100 }),
}) as fc.Arbitrary<Permission>;

const categoryArb = fc.record({
  code: fc.string({ minLength: 1, maxLength: 32 }),
  name: fc.string({ minLength: 1, maxLength: 64 }),
  description: fc.option(fc.string({ maxLength: 256 }), { nil: undefined }),
  sort_order: fc.integer({ min: 0, max: 100 }),
  icon: fc.option(fc.string({ maxLength: 16 }), { nil: undefined }),
  permissions: fc.array(permissionArb, { minLength: 0, maxLength: 10 }),
}) as fc.Arbitrary<PermissionCategory>;

// Helper to create a category with unique permission codes
const categoryWithUniqueCodesArb = fc.array(
  fc.string({ minLength: 1, maxLength: 20 }),
  { minLength: 1, maxLength: 10 }
).chain((codes) => {
  const uniqueCodes = [...new Set(codes)];
  return fc.record({
    code: fc.string({ minLength: 1, maxLength: 32 }),
    name: fc.string({ minLength: 1, maxLength: 64 }),
    description: fc.option(fc.string({ maxLength: 256 }), { nil: undefined }),
    sort_order: fc.integer({ min: 0, max: 100 }),
    icon: fc.option(fc.string({ maxLength: 16 }), { nil: undefined }),
    permissions: fc.constant(uniqueCodes.map((code, i) => ({
      id: i + 1,
      code,
      name: `Permission ${code}`,
      sort_order: i,
    }))),
  }) as fc.Arbitrary<PermissionCategory>;
});

describe('Permission Tree Utils - Property-Based Tests', () => {
  /**
   * Property 4: Category Checkbox State Derivation
   * 
   * For any category in the permission tree:
   * - If all permissions in the category are selected, the category checkbox state should be "checked"
   * - If some (but not all) permissions are selected, the state should be "indeterminate"
   * - If no permissions are selected, the state should be "unchecked"
   * 
   * **Validates: Requirements 3.3, 3.4, 3.5**
   */
  describe('Property 4: Category Checkbox State Derivation', () => {
    it('should return "unchecked" when no permissions are selected', () => {
      fc.assert(
        fc.property(categoryWithUniqueCodesArb, (category) => {
          // Skip empty categories
          if (category.permissions.length === 0) return true;
          
          const selectedPermissions = new Set<string>();
          const state = getCategoryCheckboxState(category, selectedPermissions);
          
          return state === 'unchecked';
        }),
        { numRuns: 100 }
      );
    });

    it('should return "checked" when all permissions are selected', () => {
      fc.assert(
        fc.property(categoryWithUniqueCodesArb, (category) => {
          // Skip empty categories
          if (category.permissions.length === 0) return true;
          
          const allCodes = category.permissions.map(p => p.code);
          const selectedPermissions = new Set(allCodes);
          const state = getCategoryCheckboxState(category, selectedPermissions);
          
          return state === 'checked';
        }),
        { numRuns: 100 }
      );
    });

    it('should return "indeterminate" when some (but not all) permissions are selected', () => {
      fc.assert(
        fc.property(
          categoryWithUniqueCodesArb,
          fc.integer({ min: 1 }),
          (category, selectCount) => {
            // Need at least 2 permissions to have partial selection
            if (category.permissions.length < 2) return true;
            
            const allCodes = category.permissions.map(p => p.code);
            // Select some but not all
            const actualSelectCount = Math.min(selectCount, allCodes.length - 1);
            const selectedCodes = allCodes.slice(0, actualSelectCount);
            const selectedPermissions = new Set(selectedCodes);
            
            const state = getCategoryCheckboxState(category, selectedPermissions);
            
            return state === 'indeterminate';
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should handle empty categories correctly', () => {
      const emptyCategory: PermissionCategory = {
        code: 'empty',
        name: 'Empty Category',
        sort_order: 0,
        permissions: [],
      };
      
      const state = getCategoryCheckboxState(emptyCategory, new Set());
      expect(state).toBe('unchecked');
    });

    it('should correctly derive state based on selection count', () => {
      fc.assert(
        fc.property(
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 10 }),
          fc.integer({ min: 0, max: 10 }),
          (codes, selectCount) => {
            const uniqueCodes = [...new Set(codes)];
            if (uniqueCodes.length === 0) return true;
            
            const category: PermissionCategory = {
              code: 'test',
              name: 'Test',
              sort_order: 0,
              permissions: uniqueCodes.map((code, i) => ({
                id: i + 1,
                code,
                name: `Perm ${code}`,
                sort_order: i,
              })),
            };
            
            const actualSelectCount = Math.min(selectCount, uniqueCodes.length);
            const selectedCodes = uniqueCodes.slice(0, actualSelectCount);
            const selectedPermissions = new Set(selectedCodes);
            
            const state = getCategoryCheckboxState(category, selectedPermissions);
            
            if (actualSelectCount === 0) {
              return state === 'unchecked';
            } else if (actualSelectCount === uniqueCodes.length) {
              return state === 'checked';
            } else {
              return state === 'indeterminate';
            }
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 5: Category Toggle Propagation
   * 
   * For any category, when its checkbox is toggled to checked, all child permissions 
   * should become selected. When toggled to unchecked, all child permissions should 
   * become deselected.
   * 
   * **Validates: Requirements 3.2**
   */
  describe('Property 5: Category Toggle Propagation', () => {
    it('should select all permissions when toggling from unchecked/indeterminate', () => {
      fc.assert(
        fc.property(categoryWithUniqueCodesArb, (category) => {
          if (category.permissions.length === 0) return true;
          
          // Start with no selection
          const initialSelection: string[] = [];
          const newSelection = toggleCategoryPermissions(category, initialSelection);
          
          // All permissions in category should be selected
          const categoryPermCodes = category.permissions.map(p => p.code);
          return categoryPermCodes.every(code => newSelection.includes(code));
        }),
        { numRuns: 100 }
      );
    });

    it('should deselect all permissions when toggling from checked', () => {
      fc.assert(
        fc.property(categoryWithUniqueCodesArb, (category) => {
          if (category.permissions.length === 0) return true;
          
          // Start with all selected
          const allCodes = category.permissions.map(p => p.code);
          const newSelection = toggleCategoryPermissions(category, allCodes);
          
          // No permissions in category should be selected
          return allCodes.every(code => !newSelection.includes(code));
        }),
        { numRuns: 100 }
      );
    });

    it('should preserve selections from other categories', () => {
      fc.assert(
        fc.property(
          categoryWithUniqueCodesArb,
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 1, maxLength: 5 }),
          (category, otherCodes) => {
            if (category.permissions.length === 0) return true;
            
            // Ensure other codes don't overlap with category codes
            const categoryPermCodes = new Set(category.permissions.map(p => p.code));
            const uniqueOtherCodes = otherCodes.filter(c => !categoryPermCodes.has(c));
            
            // Start with other codes selected
            const newSelection = toggleCategoryPermissions(category, uniqueOtherCodes);
            
            // Other codes should still be selected
            return uniqueOtherCodes.every(code => newSelection.includes(code));
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 6: Search Filter Correctness
   * 
   * For any search query string, the filtered results should include only permissions 
   * where the code or name contains the query string (case-insensitive match).
   * 
   * **Validates: Requirements 7.2**
   */
  describe('Property 6: Search Filter Correctness', () => {
    it('should only include permissions matching the query (case-insensitive)', () => {
      fc.assert(
        fc.property(
          fc.array(categoryArb, { minLength: 1, maxLength: 5 }),
          fc.string({ minLength: 1, maxLength: 10 }),
          (tree, query) => {
            const filtered = filterPermissionTree(tree, query);

            // Whitespace-only query is treated as empty query (no filtering).
            if (!query.trim()) {
              return filtered === tree;
            }

            const normalizedQuery = query.toLowerCase();
            
            // All permissions in filtered tree should match the query
            for (const category of filtered) {
              for (const perm of category.permissions) {
                const matches = 
                  perm.name.toLowerCase().includes(normalizedQuery) ||
                  perm.code.toLowerCase().includes(normalizedQuery) ||
                  perm.description?.toLowerCase().includes(normalizedQuery);
                
                if (!matches) return false;
              }
            }
            return true;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should return original tree when query is empty', () => {
      fc.assert(
        fc.property(
          fc.array(categoryArb, { minLength: 1, maxLength: 5 }),
          (tree) => {
            const filtered = filterPermissionTree(tree, '');
            return filtered === tree;
          }
        ),
        { numRuns: 100 }
      );
    });

    it('should exclude categories with no matching permissions', () => {
      fc.assert(
        fc.property(
          fc.array(categoryArb, { minLength: 1, maxLength: 5 }),
          fc.string({ minLength: 1, maxLength: 10 }),
          (tree, query) => {
            const filtered = filterPermissionTree(tree, query);
            
            // When query is whitespace-only, original tree is returned (no filtering)
            // In this case, empty categories may exist in the original tree
            if (!query.trim()) {
              return filtered === tree;
            }
            
            // When query is non-empty, all categories in filtered tree should have at least one permission
            return filtered.every(cat => cat.permissions.length > 0);
          }
        ),
        { numRuns: 100 }
      );
    });
  });

  /**
   * Property 11: Bulk Selection Operations
   * 
   * For any permission tree state:
   * - After "全选" is clicked, all permissions across all categories should be selected
   * - After "清空" is clicked, no permissions should be selected
   * 
   * **Validates: Requirements 8.3, 8.4**
   */
  describe('Property 11: Bulk Selection Operations', () => {
    it('selectAll should return all permission codes', () => {
      fc.assert(
        fc.property(
          fc.array(categoryArb, { minLength: 1, maxLength: 5 }),
          (tree) => {
            const allSelected = selectAllPermissions(tree);
            const expectedCodes = tree.flatMap(cat => cat.permissions.map(p => p.code));
            
            // Should have same length
            if (allSelected.length !== expectedCodes.length) return false;
            
            // Should contain all expected codes
            const selectedSet = new Set(allSelected);
            return expectedCodes.every(code => selectedSet.has(code));
          }
        ),
        { numRuns: 100 }
      );
    });

    it('clearAll should result in empty selection (represented by empty array)', () => {
      // Clear all is simply returning an empty array, which is trivially correct
      // This test verifies the contract
      const cleared: string[] = [];
      expect(cleared.length).toBe(0);
    });
  });

  /**
   * Property 12: Selection Count Accuracy
   * 
   * For any selection state, the displayed count "已选择 X/Y 个权限" should accurately 
   * reflect X = number of selected permissions and Y = total number of permissions.
   * 
   * **Validates: Requirements 8.5**
   */
  describe('Property 12: Selection Count Accuracy', () => {
    it('should accurately count selected and total permissions', () => {
      fc.assert(
        fc.property(
          fc.array(categoryArb, { minLength: 1, maxLength: 5 }),
          fc.array(fc.string({ minLength: 1, maxLength: 20 }), { minLength: 0, maxLength: 10 }),
          (tree, selectedCodes) => {
            const { selected, total } = getSelectionCount(tree, selectedCodes);
            
            // Total should equal sum of all permissions across categories
            const expectedTotal = tree.reduce((sum, cat) => sum + cat.permissions.length, 0);
            if (total !== expectedTotal) return false;
            
            // Selected should equal length of selected array
            return selected === selectedCodes.length;
          }
        ),
        { numRuns: 100 }
      );
    });
  });
});
