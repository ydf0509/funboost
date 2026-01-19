"use client";

import { useState, useEffect, useMemo, useCallback } from "react";
import clsx from "clsx";
import { Input } from "./Input";

// 标准操作类型
export const ACTION_TYPES = [
  { code: "create", name: "创建", category: "write" },
  { code: "read", name: "查看", category: "read" },
  { code: "update", name: "编辑", category: "write" },
  { code: "delete", name: "删除", category: "write" },
  { code: "execute", name: "执行", category: "write" },
  { code: "export", name: "导出", category: "read" },
] as const;

export type ActionType = (typeof ACTION_TYPES)[number]["code"];

// 权限项类型（增强版）
export type Permission = {
  id: number;
  code: string;
  name: string;
  description?: string;
  category_code?: string;
  sort_order: number;
  action_type?: string;
  action_type_display?: string;
  project_scope?: string | null;
};

// 权限分类类型（增强版，支持子分类）
export type PermissionCategory = {
  code: string;
  name: string;
  description?: string;
  sort_order: number;
  icon?: string;
  permissions: Permission[];
  subcategories?: PermissionCategory[];
};

// 组件属性类型
type PermissionTreeProps = {
  /** 权限树数据 */
  tree: PermissionCategory[];
  /** 已选中的权限代码列表 */
  selectedPermissions: string[];
  /** 权限选择变化回调 */
  onSelectionChange: (permissions: string[]) => void;
  /** 是否禁用 */
  disabled?: boolean;
  /** 是否显示搜索框 */
  showSearch?: boolean;
  /** 是否显示批量操作按钮 */
  showBulkActions?: boolean;
  /** 是否显示操作类型过滤器 */
  showActionTypeFilter?: boolean;
  /** localStorage 存储键名（用于保存展开状态） */
  storageKey?: string;
  /** 项目过滤 */
  projectFilter?: string;
};

// 复选框状态类型
type CheckboxState = "checked" | "unchecked" | "indeterminate";

// 递归获取分类下所有权限代码
function getAllPermissionCodes(category: PermissionCategory): string[] {
  const codes = category.permissions.map((p) => p.code);
  if (category.subcategories) {
    for (const sub of category.subcategories) {
      codes.push(...getAllPermissionCodes(sub));
    }
  }
  return codes;
}

// 递归获取分类下所有权限
function getAllPermissions(category: PermissionCategory): Permission[] {
  const perms = [...category.permissions];
  if (category.subcategories) {
    for (const sub of category.subcategories) {
      perms.push(...getAllPermissions(sub));
    }
  }
  return perms;
}

// 获取分类的复选框状态（支持子分类）
function getCategoryCheckboxState(
  category: PermissionCategory,
  selectedPermissions: Set<string>
): CheckboxState {
  const permissionCodes = getAllPermissionCodes(category);
  if (permissionCodes.length === 0) return "unchecked";
  
  const selectedCount = permissionCodes.filter((code) =>
    selectedPermissions.has(code)
  ).length;

  if (selectedCount === 0) return "unchecked";
  if (selectedCount === permissionCodes.length) return "checked";
  return "indeterminate";
}

// 扁平化权限树，获取所有权限
function flattenPermissions(tree: PermissionCategory[]): Permission[] {
  const result: Permission[] = [];
  for (const cat of tree) {
    result.push(...getAllPermissions(cat));
  }
  return result;
}

// 递归获取所有分类代码（包括子分类）
function getAllCategoryCodes(tree: PermissionCategory[]): string[] {
  const codes: string[] = [];
  for (const cat of tree) {
    codes.push(cat.code);
    if (cat.subcategories) {
      codes.push(...getAllCategoryCodes(cat.subcategories));
    }
  }
  return codes;
}

// 复选框组件
function Checkbox({
  state,
  onChange,
  disabled,
  label,
  description,
  badge,
  projectBadge,
}: {
  state: CheckboxState;
  onChange: () => void;
  disabled?: boolean;
  label: string;
  description?: string;
  badge?: string;
  projectBadge?: string | null;
}) {
  return (
    <label
      className={clsx(
        "flex items-start gap-3 cursor-pointer select-none",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      <span
        className={clsx(
          "mt-0.5 flex h-5 w-5 items-center justify-center rounded border-2 transition-colors flex-shrink-0",
          state === "checked"
            ? "bg-[hsl(var(--accent))] border-[hsl(var(--accent))]"
            : state === "indeterminate"
            ? "bg-[hsl(var(--accent))]/50 border-[hsl(var(--accent))]"
            : "bg-[hsl(var(--card))] border-[hsl(var(--line))]",
          !disabled && "hover:border-[hsl(var(--accent))]"
        )}
        onClick={(e) => {
          e.preventDefault();
          if (!disabled) onChange();
        }}
      >
        {state === "checked" && (
          <svg className="h-3 w-3 text-white" viewBox="0 0 12 12" fill="none">
            <path
              d="M2 6L5 9L10 3"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
        {state === "indeterminate" && (
          <svg className="h-3 w-3 text-white" viewBox="0 0 12 12" fill="none">
            <path
              d="M2 6H10"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        )}
      </span>
      <span className="flex flex-col min-w-0">
        <span className="flex items-center gap-2 flex-wrap">
          <span className="text-sm font-medium text-[hsl(var(--ink))]">
            {label}
          </span>
          {badge && (
            <span className="px-1.5 py-0.5 text-xs rounded bg-[hsl(var(--accent))]/10 text-[hsl(var(--accent))]">
              {badge}
            </span>
          )}
          {projectBadge && (
            <span className="px-1.5 py-0.5 text-xs rounded bg-[hsl(var(--sand-3))] text-[hsl(var(--ink-muted))]">
              {projectBadge}
            </span>
          )}
        </span>
        {description && (
          <span className="text-xs text-[hsl(var(--ink-muted))] truncate">
            {description}
          </span>
        )}
      </span>
    </label>
  );
}

// 展开/折叠图标
function ChevronIcon({ expanded }: { expanded: boolean }) {
  return (
    <svg
      className={clsx(
        "h-4 w-4 text-[hsl(var(--ink-muted))] transition-transform flex-shrink-0",
        expanded && "rotate-90"
      )}
      viewBox="0 0 16 16"
      fill="none"
    >
      <path
        d="M6 4L10 8L6 12"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

// 操作类型过滤按钮
function ActionTypeFilterButton({
  label,
  active,
  onClick,
  disabled,
  count,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
  count?: number;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={clsx(
        "px-3 py-1.5 text-sm rounded-lg transition-colors",
        active
          ? "bg-[hsl(var(--accent))] text-white"
          : "bg-[hsl(var(--sand-2))] text-[hsl(var(--ink-muted))] hover:bg-[hsl(var(--sand-3))]",
        disabled && "opacity-50 cursor-not-allowed"
      )}
    >
      {label}
      {count !== undefined && (
        <span className="ml-1 text-xs opacity-75">({count})</span>
      )}
    </button>
  );
}

export function PermissionTree({
  tree,
  selectedPermissions,
  onSelectionChange,
  disabled = false,
  showSearch = true,
  showBulkActions = true,
  showActionTypeFilter = true,
  storageKey = "permission-tree-expanded",
}: PermissionTreeProps) {
  // 搜索关键词
  const [searchQuery, setSearchQuery] = useState("");
  
  // 操作类型过滤
  const [actionTypeFilter, setActionTypeFilter] = useState<string | null>(null);
  
  // 展开状态（分类代码 -> 是否展开）
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    () => {
      // 从 localStorage 恢复状态，默认全部展开
      if (typeof window !== "undefined") {
        const saved = localStorage.getItem(storageKey);
        if (saved) {
          try {
            return new Set(JSON.parse(saved));
          } catch {
            // 解析失败，使用默认值
          }
        }
      }
      // 默认全部展开
      return new Set(getAllCategoryCodes(tree));
    }
  );

  // 搜索前的展开状态（用于恢复）
  const [preSearchExpanded, setPreSearchExpanded] = useState<Set<string> | null>(
    null
  );

  // 已选权限集合（用于快速查找）
  const selectedSet = useMemo(
    () => new Set(selectedPermissions),
    [selectedPermissions]
  );

  // 所有权限
  const allPermissions = useMemo(() => flattenPermissions(tree), [tree]);

  // 所有权限代码列表
  const allPermissionCodes = useMemo(
    () => allPermissions.map((p) => p.code),
    [allPermissions]
  );

  // 按操作类型统计
  const actionTypeCounts = useMemo(() => {
    const counts: Record<string, { total: number; selected: number }> = {};
    for (const perm of allPermissions) {
      const type = perm.action_type || "other";
      if (!counts[type]) {
        counts[type] = { total: 0, selected: 0 };
      }
      counts[type].total++;
      if (selectedSet.has(perm.code)) {
        counts[type].selected++;
      }
    }
    return counts;
  }, [allPermissions, selectedSet]);

  // 递归过滤分类
  const filterCategory = useCallback(
    (category: PermissionCategory): PermissionCategory | null => {
      const query = searchQuery.toLowerCase();
      const actionFilter = actionTypeFilter;

      // 过滤权限
      let filteredPermissions = category.permissions;
      
      if (query) {
        filteredPermissions = filteredPermissions.filter(
          (perm) =>
            perm.name.toLowerCase().includes(query) ||
            perm.code.toLowerCase().includes(query) ||
            perm.description?.toLowerCase().includes(query) ||
            perm.action_type?.toLowerCase().includes(query)
        );
      }
      
      if (actionFilter) {
        filteredPermissions = filteredPermissions.filter(
          (perm) => perm.action_type === actionFilter
        );
      }

      // 递归过滤子分类
      const filteredSubcategories: PermissionCategory[] = [];
      if (category.subcategories) {
        for (const sub of category.subcategories) {
          const filtered = filterCategory(sub);
          if (filtered) {
            filteredSubcategories.push(filtered);
          }
        }
      }

      // 如果没有权限也没有子分类，返回 null
      if (filteredPermissions.length === 0 && filteredSubcategories.length === 0) {
        return null;
      }

      return {
        ...category,
        permissions: filteredPermissions,
        subcategories: filteredSubcategories.length > 0 ? filteredSubcategories : undefined,
      };
    },
    [searchQuery, actionTypeFilter]
  );

  // 过滤后的权限树
  const filteredTree = useMemo(() => {
    if (!searchQuery.trim() && !actionTypeFilter) return tree;

    const result: PermissionCategory[] = [];
    for (const cat of tree) {
      const filtered = filterCategory(cat);
      if (filtered) {
        result.push(filtered);
      }
    }
    return result;
  }, [tree, searchQuery, actionTypeFilter, filterCategory]);

  // 搜索时自动展开匹配的分类
  useEffect(() => {
    if (searchQuery.trim() || actionTypeFilter) {
      // 保存搜索前的状态
      if (!preSearchExpanded) {
        setPreSearchExpanded(new Set(expandedCategories));
      }
      // 展开所有匹配的分类
      setExpandedCategories(new Set(getAllCategoryCodes(filteredTree)));
    } else if (preSearchExpanded) {
      // 恢复搜索前的状态
      setExpandedCategories(preSearchExpanded);
      setPreSearchExpanded(null);
    }
  }, [searchQuery, actionTypeFilter, filteredTree]);

  // 保存展开状态到 localStorage
  useEffect(() => {
    if (typeof window !== "undefined" && !searchQuery.trim() && !actionTypeFilter) {
      localStorage.setItem(
        storageKey,
        JSON.stringify(Array.from(expandedCategories))
      );
    }
  }, [expandedCategories, storageKey, searchQuery, actionTypeFilter]);

  // 切换分类展开状态
  const toggleCategory = useCallback((categoryCode: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      if (next.has(categoryCode)) {
        next.delete(categoryCode);
      } else {
        next.add(categoryCode);
      }
      return next;
    });
  }, []);

  // 切换单个权限
  const togglePermission = useCallback(
    (permissionCode: string) => {
      if (disabled) return;
      const newSelection = selectedSet.has(permissionCode)
        ? selectedPermissions.filter((p) => p !== permissionCode)
        : [...selectedPermissions, permissionCode];
      onSelectionChange(newSelection);
    },
    [disabled, selectedSet, selectedPermissions, onSelectionChange]
  );

  // 切换整个分类（包括子分类）
  const toggleCategoryPermissions = useCallback(
    (category: PermissionCategory) => {
      if (disabled) return;
      const permissionCodes = getAllPermissionCodes(category);
      const state = getCategoryCheckboxState(category, selectedSet);

      let newSelection: string[];
      if (state === "checked") {
        // 全选 -> 取消全选
        newSelection = selectedPermissions.filter(
          (p) => !permissionCodes.includes(p)
        );
      } else {
        // 未选/部分选 -> 全选
        const toAdd = permissionCodes.filter((p) => !selectedSet.has(p));
        newSelection = [...selectedPermissions, ...toAdd];
      }
      onSelectionChange(newSelection);
    },
    [disabled, selectedSet, selectedPermissions, onSelectionChange]
  );

  // 全选
  const selectAll = useCallback(() => {
    if (disabled) return;
    onSelectionChange(allPermissionCodes);
  }, [disabled, allPermissionCodes, onSelectionChange]);

  // 清空
  const clearAll = useCallback(() => {
    if (disabled) return;
    onSelectionChange([]);
  }, [disabled, onSelectionChange]);

  // 展开全部
  const expandAll = useCallback(() => {
    setExpandedCategories(new Set(getAllCategoryCodes(tree)));
  }, [tree]);

  // 折叠全部
  const collapseAll = useCallback(() => {
    setExpandedCategories(new Set());
  }, []);

  // 按操作类型选择
  const selectByActionType = useCallback(
    (type: "read" | "write" | ActionType) => {
      if (disabled) return;
      
      let toSelect: string[];
      if (type === "read") {
        // 选择所有读权限（read + export）
        toSelect = allPermissions
          .filter((p) => p.action_type === "read" || p.action_type === "export")
          .map((p) => p.code);
      } else if (type === "write") {
        // 选择所有写权限（create, update, delete, execute）
        toSelect = allPermissions
          .filter((p) =>
            ["create", "update", "delete", "execute"].includes(p.action_type || "")
          )
          .map((p) => p.code);
      } else {
        // 选择特定操作类型
        toSelect = allPermissions
          .filter((p) => p.action_type === type)
          .map((p) => p.code);
      }

      // 合并现有选择
      const newSelection = new Set([...selectedPermissions, ...toSelect]);
      onSelectionChange(Array.from(newSelection));
    },
    [disabled, allPermissions, selectedPermissions, onSelectionChange]
  );

  // 渲染分类（递归）
  const renderCategory = (category: PermissionCategory, level: number = 0) => {
    const isExpanded = expandedCategories.has(category.code);
    const categoryState = getCategoryCheckboxState(category, selectedSet);
    const hasChildren =
      category.permissions.length > 0 ||
      (category.subcategories && category.subcategories.length > 0);
    const totalPerms = getAllPermissionCodes(category).length;
    const selectedPerms = getAllPermissionCodes(category).filter((c) =>
      selectedSet.has(c)
    ).length;

    return (
      <div
        key={category.code}
        className={clsx(
          level === 0 &&
            "rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--card))]/50 overflow-hidden",
          level > 0 && "border-l-2 border-[hsl(var(--line))] ml-4"
        )}
      >
        {/* 分类头部 */}
        <div
          className={clsx(
            "flex items-center gap-3 px-4 py-3 cursor-pointer select-none",
            "hover:bg-[hsl(var(--sand-1))]",
            level > 0 && "py-2"
          )}
          onClick={() => toggleCategory(category.code)}
        >
          {hasChildren && <ChevronIcon expanded={isExpanded} />}
          {!hasChildren && <span className="w-4" />}
          <span className="text-lg">{category.icon || (level === 0 ? "📁" : "📂")}</span>
          <div className="flex-1 min-w-0" onClick={(e) => e.stopPropagation()}>
            <Checkbox
              state={categoryState}
              onChange={() => toggleCategoryPermissions(category)}
              disabled={disabled}
              label={category.name}
              description={`${selectedPerms}/${totalPerms} 个权限`}
            />
          </div>
        </div>

        {/* 子分类和权限列表 */}
        {isExpanded && hasChildren && (
          <div
            className={clsx(
              "border-t border-[hsl(var(--line))] bg-[hsl(var(--sand-1))]/50",
              level === 0 ? "px-4 py-3 pl-12" : "px-2 py-2 pl-8"
            )}
          >
            {/* 子分类 */}
            {category.subcategories?.map((sub) => renderCategory(sub, level + 1))}

            {/* 权限项 */}
            <div className="space-y-3 mt-2">
              {category.permissions.map((permission) => (
                <Checkbox
                  key={permission.code}
                  state={selectedSet.has(permission.code) ? "checked" : "unchecked"}
                  onChange={() => togglePermission(permission.code)}
                  disabled={disabled}
                  label={permission.name}
                  description={permission.description || permission.code}
                  badge={permission.action_type_display || permission.action_type}
                  projectBadge={permission.project_scope}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* 搜索框 */}
      {showSearch && (
        <div className="flex-1">
          <Input
            type="text"
            placeholder="搜索权限（按名称、代码、描述或操作类型）..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={disabled}
          />
        </div>
      )}

      {/* 操作类型过滤器 */}
      {showActionTypeFilter && (
        <div className="flex flex-wrap items-center gap-2">
          <ActionTypeFilterButton
            label="全部"
            active={actionTypeFilter === null}
            onClick={() => setActionTypeFilter(null)}
            disabled={disabled}
          />
          <span className="text-[hsl(var(--line))]">|</span>
          <ActionTypeFilterButton
            label="选择所有读权限"
            active={false}
            onClick={() => selectByActionType("read")}
            disabled={disabled}
          />
          <ActionTypeFilterButton
            label="选择所有写权限"
            active={false}
            onClick={() => selectByActionType("write")}
            disabled={disabled}
          />
          <span className="text-[hsl(var(--line))]">|</span>
          {ACTION_TYPES.map((at) => (
            <ActionTypeFilterButton
              key={at.code}
              label={at.name}
              active={actionTypeFilter === at.code}
              onClick={() =>
                setActionTypeFilter(actionTypeFilter === at.code ? null : at.code)
              }
              disabled={disabled}
              count={actionTypeCounts[at.code]?.selected || 0}
            />
          ))}
        </div>
      )}

      {/* 批量操作和统计 */}
      {showBulkActions && (
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={selectAll}
              disabled={disabled}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-lg transition-colors",
                "bg-[hsl(var(--accent))]/10 text-[hsl(var(--accent))]",
                "hover:bg-[hsl(var(--accent))]/20",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              全选
            </button>
            <button
              type="button"
              onClick={clearAll}
              disabled={disabled}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-lg transition-colors",
                "bg-[hsl(var(--sand-2))] text-[hsl(var(--ink-muted))]",
                "hover:bg-[hsl(var(--sand-3))]",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              清空
            </button>
            <button
              type="button"
              onClick={expandAll}
              disabled={disabled}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-lg transition-colors",
                "bg-[hsl(var(--sand-2))] text-[hsl(var(--ink-muted))]",
                "hover:bg-[hsl(var(--sand-3))]",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              展开全部
            </button>
            <button
              type="button"
              onClick={collapseAll}
              disabled={disabled}
              className={clsx(
                "px-3 py-1.5 text-sm rounded-lg transition-colors",
                "bg-[hsl(var(--sand-2))] text-[hsl(var(--ink-muted))]",
                "hover:bg-[hsl(var(--sand-3))]",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              折叠全部
            </button>
          </div>
          <div className="text-sm text-[hsl(var(--ink-muted))]">
            已选择 {selectedPermissions.length}/{allPermissionCodes.length} 个权限
          </div>
        </div>
      )}

      {/* 权限树 */}
      <div className="space-y-2">
        {filteredTree.length === 0 ? (
          <div className="py-8 text-center text-[hsl(var(--ink-muted))]">
            {searchQuery || actionTypeFilter ? "没有找到匹配的权限" : "暂无权限数据"}
          </div>
        ) : (
          filteredTree.map((category) => renderCategory(category))
        )}
      </div>
    </div>
  );
}

// 导出辅助函数供测试使用
export { flattenPermissions, getAllCategoryCodes, getCategoryCheckboxState, getAllPermissionCodes };
