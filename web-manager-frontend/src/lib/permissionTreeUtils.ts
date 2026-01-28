/**
 * Permission Tree Utility Functions
 * 
 * These functions are extracted from the PermissionTree component
 * to enable property-based testing.
 */

// 权限项类型
export type Permission = {
  id: number;
  code: string;
  name: string;
  description?: string;
  category_code?: string;
  sort_order: number;
};

// 权限分类类型
export type PermissionCategory = {
  code: string;
  name: string;
  description?: string;
  sort_order: number;
  icon?: string;
  permissions: Permission[];
};

// 复选框状态类型
export type CheckboxState = "checked" | "unchecked" | "indeterminate";

/**
 * 获取分类的复选框状态
 * 
 * Property 4: Category Checkbox State Derivation
 * - If all permissions in the category are selected, returns "checked"
 * - If some (but not all) permissions are selected, returns "indeterminate"
 * - If no permissions are selected, returns "unchecked"
 * 
 * @param category - The permission category
 * @param selectedPermissions - Set of selected permission codes
 * @returns The checkbox state
 */
export function getCategoryCheckboxState(
  category: PermissionCategory,
  selectedPermissions: Set<string>
): CheckboxState {
  const permissionCodes = category.permissions.map((p) => p.code);
  
  // Handle empty category case
  if (permissionCodes.length === 0) {
    return "unchecked";
  }
  
  const selectedCount = permissionCodes.filter((code) =>
    selectedPermissions.has(code)
  ).length;

  if (selectedCount === 0) return "unchecked";
  if (selectedCount === permissionCodes.length) return "checked";
  return "indeterminate";
}

/**
 * 切换分类下所有权限的选中状态
 * 
 * Property 5: Category Toggle Propagation
 * - When toggled to checked, all child permissions become selected
 * - When toggled to unchecked, all child permissions become deselected
 * 
 * @param category - The permission category to toggle
 * @param currentSelection - Current set of selected permission codes
 * @returns New array of selected permission codes
 */
export function toggleCategoryPermissions(
  category: PermissionCategory,
  currentSelection: string[]
): string[] {
  const selectedSet = new Set(currentSelection);
  const permissionCodes = category.permissions.map((p) => p.code);
  const state = getCategoryCheckboxState(category, selectedSet);

  if (state === "checked") {
    // All selected -> deselect all in this category
    return currentSelection.filter((p) => !permissionCodes.includes(p));
  } else {
    // None or some selected -> select all in this category
    const toAdd = permissionCodes.filter((p) => !selectedSet.has(p));
    return [...currentSelection, ...toAdd];
  }
}

/**
 * 过滤权限树（搜索功能）
 * 
 * Property 6: Search Filter Correctness
 * - Filtered results include only permissions where code or name contains the query (case-insensitive)
 * 
 * @param tree - The permission tree to filter
 * @param query - The search query
 * @returns Filtered permission tree
 */
export function filterPermissionTree(
  tree: PermissionCategory[],
  query: string
): PermissionCategory[] {
  if (!query.trim()) return tree;

  const normalizedQuery = query.toLowerCase();
  return tree
    .map((category) => ({
      ...category,
      permissions: category.permissions.filter(
        (perm) =>
          perm.name.toLowerCase().includes(normalizedQuery) ||
          perm.code.toLowerCase().includes(normalizedQuery) ||
          perm.description?.toLowerCase().includes(normalizedQuery)
      ),
    }))
    .filter((category) => category.permissions.length > 0);
}

/**
 * 全选所有权限
 * 
 * Property 11: Bulk Selection Operations (Select All)
 * 
 * @param tree - The permission tree
 * @returns Array of all permission codes
 */
export function selectAllPermissions(tree: PermissionCategory[]): string[] {
  return tree.flatMap((cat) => cat.permissions.map((p) => p.code));
}

/**
 * 计算选中数量
 * 
 * Property 12: Selection Count Accuracy
 * 
 * @param tree - The permission tree
 * @param selectedPermissions - Array of selected permission codes
 * @returns Object with selected and total counts
 */
export function getSelectionCount(
  tree: PermissionCategory[],
  selectedPermissions: string[]
): { selected: number; total: number } {
  const total = tree.reduce((sum, cat) => sum + cat.permissions.length, 0);
  return {
    selected: selectedPermissions.length,
    total,
  };
}
