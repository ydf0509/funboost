"use client";

import { useState, useMemo, useCallback } from "react";
import clsx from "clsx";
import { Check, ChevronRight, Minus, Search, Settings, Shield, Users, FileText, FolderKanban, Activity, Database } from "lucide-react";

// 标准操作类型
export const ACTION_TYPES = [
  { code: "create", name: "创建", color: "text-[hsl(var(--success))]", bg: "bg-[hsl(var(--success))]/10" },
  { code: "read", name: "查看", color: "text-[hsl(var(--info))]", bg: "bg-[hsl(var(--info))]/10" },
  { code: "update", name: "编辑", color: "text-[hsl(var(--warning))]", bg: "bg-[hsl(var(--warning))]/10" },
  { code: "delete", name: "删除", color: "text-[hsl(var(--danger))]", bg: "bg-[hsl(var(--danger))]/10" },
  { code: "execute", name: "执行", color: "text-[hsl(var(--accent))]", bg: "bg-[hsl(var(--accent))]/10" },
  { code: "export", name: "导出", color: "text-[hsl(var(--accent-2))]", bg: "bg-[hsl(var(--accent-2))]/10" },
] as const;

// 权限项类型
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

// 权限分类类型
export type PermissionCategory = {
  code: string;
  name: string;
  description?: string;
  sort_order: number;
  icon?: string;
  permissions: Permission[];
  subcategories?: PermissionCategory[];
};

type PermissionSelectorProps = {
  tree: PermissionCategory[];
  selectedPermissions: string[];
  onSelectionChange: (permissions: string[]) => void;
  disabled?: boolean;
};

// 分类图标映射（使用 Lucide 图标）
const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  system: <Settings className="h-4 w-4" />,
  user: <Users className="h-4 w-4" />,
  role: <Shield className="h-4 w-4" />,
  audit: <FileText className="h-4 w-4" />,
  config: <Settings className="h-4 w-4" />,
  project: <FolderKanban className="h-4 w-4" />,
  queue: <Activity className="h-4 w-4" />,
  task: <Database className="h-4 w-4" />,
  default: <Shield className="h-4 w-4" />,
};

// 获取分类图标
function getCategoryIcon(code: string): React.ReactNode {
  const lowerCode = code.toLowerCase();
  for (const [key, icon] of Object.entries(CATEGORY_ICONS)) {
    if (lowerCode.includes(key)) return icon;
  }
  return CATEGORY_ICONS.default;
}

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

// 扁平化权限树
function flattenTree(tree: PermissionCategory[]): PermissionCategory[] {
  const result: PermissionCategory[] = [];
  for (const cat of tree) {
    result.push(cat);
    if (cat.subcategories) {
      result.push(...flattenTree(cat.subcategories));
    }
  }
  return result;
}

// 获取操作类型配置
function getActionTypeConfig(actionType?: string) {
  const config = ACTION_TYPES.find(at => at.code === actionType);
  return config || { code: actionType || "other", name: actionType || "其他", color: "text-[hsl(var(--ink-muted))]", bg: "bg-[hsl(var(--sand-2))]" };
}

export function PermissionSelector({
  tree,
  selectedPermissions,
  onSelectionChange,
  disabled = false,
}: PermissionSelectorProps) {
  // 当前选中的分类
  const [activeCategory, setActiveCategory] = useState<string | null>(
    tree.length > 0 ? tree[0].code : null
  );
  
  // 搜索关键词
  const [searchQuery, setSearchQuery] = useState("");
  
  // 操作类型过滤
  const [actionFilter, setActionFilter] = useState<string | null>(null);

  // 已选权限集合
  const selectedSet = useMemo(
    () => new Set(selectedPermissions),
    [selectedPermissions]
  );

  // 扁平化的分类列表（用于左侧导航）
  const flatCategories = useMemo(() => flattenTree(tree), [tree]);

  // 所有权限
  const allPermissions = useMemo(() => {
    const result: Permission[] = [];
    for (const cat of tree) {
      result.push(...getAllPermissions(cat));
    }
    return result;
  }, [tree]);

  // 当前分类的权限
  const currentCategory = useMemo(() => {
    if (!activeCategory) return null;
    return flatCategories.find((c) => c.code === activeCategory) || null;
  }, [activeCategory, flatCategories]);

  // 当前显示的权限（应用搜索和过滤）
  const displayPermissions = useMemo(() => {
    let perms = currentCategory ? getAllPermissions(currentCategory) : [];
    
    // 搜索过滤
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      perms = perms.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.code.toLowerCase().includes(query) ||
          p.description?.toLowerCase().includes(query)
      );
    }
    
    // 操作类型过滤
    if (actionFilter) {
      perms = perms.filter((p) => p.action_type === actionFilter);
    }
    
    return perms;
  }, [currentCategory, searchQuery, actionFilter]);

  // 统计各分类的选中数量
  const categoryStats = useMemo(() => {
    const stats: Record<string, { total: number; selected: number }> = {};
    for (const cat of flatCategories) {
      const codes = getAllPermissionCodes(cat);
      stats[cat.code] = {
        total: codes.length,
        selected: codes.filter((c) => selectedSet.has(c)).length,
      };
    }
    return stats;
  }, [flatCategories, selectedSet]);

  // 统计各操作类型的数量
  const actionStats = useMemo(() => {
    const perms = currentCategory ? getAllPermissions(currentCategory) : [];
    const stats: Record<string, number> = {};
    for (const perm of perms) {
      const type = perm.action_type || "other";
      stats[type] = (stats[type] || 0) + 1;
    }
    return stats;
  }, [currentCategory]);

  // 切换单个权限
  const togglePermission = useCallback(
    (code: string) => {
      if (disabled) return;
      const newSelection = selectedSet.has(code)
        ? selectedPermissions.filter((p) => p !== code)
        : [...selectedPermissions, code];
      onSelectionChange(newSelection);
    },
    [disabled, selectedSet, selectedPermissions, onSelectionChange]
  );

  // 切换整个分类（大类勾选）
  const toggleCategory = useCallback(
    (category: PermissionCategory) => {
      if (disabled) return;
      const codes = getAllPermissionCodes(category);
      const allSelected = codes.every((c) => selectedSet.has(c));
      
      if (allSelected) {
        // 取消选择该分类下所有权限
        const codesSet = new Set(codes);
        const newSelection = selectedPermissions.filter((p) => !codesSet.has(p));
        onSelectionChange(newSelection);
      } else {
        // 选择该分类下所有权限
        const newSelection = new Set([...selectedPermissions, ...codes]);
        onSelectionChange(Array.from(newSelection));
      }
    },
    [disabled, selectedSet, selectedPermissions, onSelectionChange]
  );

  // 全选当前分类
  const selectAllInCategory = useCallback(() => {
    if (disabled || !currentCategory) return;
    const codes = displayPermissions.map((p) => p.code);
    const newSelection = new Set([...selectedPermissions, ...codes]);
    onSelectionChange(Array.from(newSelection));
  }, [disabled, currentCategory, displayPermissions, selectedPermissions, onSelectionChange]);

  // 清空当前分类
  const clearAllInCategory = useCallback(() => {
    if (disabled || !currentCategory) return;
    const codes = new Set(displayPermissions.map((p) => p.code));
    const newSelection = selectedPermissions.filter((p) => !codes.has(p));
    onSelectionChange(newSelection);
  }, [disabled, currentCategory, displayPermissions, selectedPermissions, onSelectionChange]);

  // 全选所有
  const selectAll = useCallback(() => {
    if (disabled) return;
    onSelectionChange(allPermissions.map((p) => p.code));
  }, [disabled, allPermissions, onSelectionChange]);

  // 清空所有
  const clearAll = useCallback(() => {
    if (disabled) return;
    onSelectionChange([]);
  }, [disabled, onSelectionChange]);

  // 按操作类型选择（只作用于当前分类）
  const selectByActionType = useCallback(
    (type: "read" | "write") => {
      if (disabled || !currentCategory) return;
      const readTypes = ["read", "export"];
      const writeTypes = ["create", "update", "delete", "execute"];
      const targetTypes = type === "read" ? readTypes : writeTypes;
      
      // 只选择当前分类下的权限
      const categoryPermissions = getAllPermissions(currentCategory);
      const toSelect = categoryPermissions
        .filter((p) => targetTypes.includes(p.action_type || ""))
        .map((p) => p.code);
      
      const newSelection = new Set([...selectedPermissions, ...toSelect]);
      onSelectionChange(Array.from(newSelection));
    },
    [disabled, currentCategory, selectedPermissions, onSelectionChange]
  );

  // 获取分类的选中状态：全选、部分选、未选
  const getCategoryCheckState = (category: PermissionCategory): "all" | "partial" | "none" => {
    const codes = getAllPermissionCodes(category);
    const selectedCount = codes.filter((c) => selectedSet.has(c)).length;
    if (selectedCount === 0) return "none";
    if (selectedCount === codes.length) return "all";
    return "partial";
  };

  return (
    <div className="flex flex-col h-[500px] rounded-xl border border-[hsl(var(--line))] bg-[hsl(var(--card))] overflow-hidden">
      {/* 顶部工具栏 */}
      <div className="flex items-center gap-3 px-4 py-3 border-b border-[hsl(var(--line))] bg-[hsl(var(--sand))]/30">
        {/* 搜索框 */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[hsl(var(--ink-muted))]" />
          <input
            type="text"
            placeholder="搜索权限（按名称、代码、描述或操作类型）..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            disabled={disabled}
            className="w-full h-9 pl-9 pr-3 rounded-lg border border-[hsl(var(--line))] bg-[hsl(var(--card))] text-sm text-[hsl(var(--ink))] placeholder:text-[hsl(var(--ink-muted))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--accent))]/20 focus:border-[hsl(var(--accent))]"
          />
        </div>
        
        {/* 快捷操作 */}
        <div className="flex items-center gap-1.5">
          <button
            type="button"
            onClick={() => selectByActionType("read")}
            disabled={disabled}
            className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-[hsl(var(--success))]/30 text-[hsl(var(--success))] hover:bg-[hsl(var(--success))]/10 transition-colors disabled:opacity-50 cursor-pointer"
          >
            选择所有读权限
          </button>
          <button
            type="button"
            onClick={() => selectByActionType("write")}
            disabled={disabled}
            className="px-2.5 py-1.5 text-xs font-medium rounded-lg border border-[hsl(var(--warning))]/30 text-[hsl(var(--warning))] hover:bg-[hsl(var(--warning))]/10 transition-colors disabled:opacity-50 cursor-pointer"
          >
            选择所有写权限
          </button>
          <button
            type="button"
            onClick={selectAll}
            disabled={disabled}
            className="px-2.5 py-1.5 text-xs font-medium rounded-lg text-[hsl(var(--accent))] hover:bg-[hsl(var(--accent))]/10 transition-colors disabled:opacity-50 cursor-pointer"
          >
            全选
          </button>
          <button
            type="button"
            onClick={clearAll}
            disabled={disabled}
            className="px-2.5 py-1.5 text-xs font-medium rounded-lg text-[hsl(var(--ink-muted))] hover:bg-[hsl(var(--sand-2))] transition-colors disabled:opacity-50 cursor-pointer"
          >
            清空
          </button>
        </div>
        
        {/* 统计 */}
        <div className="text-xs text-[hsl(var(--ink-muted))] ml-auto whitespace-nowrap">
          已选择 <span className="font-semibold text-[hsl(var(--accent))]">{selectedPermissions.length}</span>/{allPermissions.length} 个权限
        </div>
      </div>

      {/* 主体区域：左右分栏 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧：分类导航（带勾选框） */}
        <div className="w-52 flex-shrink-0 border-r border-[hsl(var(--line))] bg-[hsl(var(--sand))]/20 overflow-y-auto">
          {tree.map((category) => {
            const stats = categoryStats[category.code];
            const isActive = activeCategory === category.code;
            const hasSubcategories = category.subcategories && category.subcategories.length > 0;
            const checkState = getCategoryCheckState(category);
            
            return (
              <div key={category.code}>
                {/* 主分类 */}
                <div
                  className={clsx(
                    "flex items-center gap-2 px-3 py-2.5 transition-colors",
                    isActive
                      ? "bg-[hsl(var(--accent))]/10 border-r-2 border-[hsl(var(--accent))]"
                      : "hover:bg-[hsl(var(--sand-2))]"
                  )}
                >
                  {/* 分类勾选框 */}
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      toggleCategory(category);
                    }}
                    disabled={disabled}
                    className={clsx(
                      "flex h-4 w-4 items-center justify-center rounded border transition-colors flex-shrink-0 cursor-pointer",
                      checkState === "all"
                        ? "bg-[hsl(var(--accent))] border-[hsl(var(--accent))]"
                        : checkState === "partial"
                        ? "bg-[hsl(var(--accent))]/50 border-[hsl(var(--accent))]"
                        : "border-[hsl(var(--line))] hover:border-[hsl(var(--accent))]"
                    )}
                  >
                    {checkState === "all" && <Check className="h-3 w-3 text-white" />}
                    {checkState === "partial" && <Minus className="h-3 w-3 text-white" />}
                  </button>
                  
                  {/* 分类名称（可点击切换） */}
                  <button
                    type="button"
                    onClick={() => setActiveCategory(category.code)}
                    className={clsx(
                      "flex-1 flex items-center gap-2 text-left cursor-pointer",
                      isActive ? "text-[hsl(var(--accent))]" : "text-[hsl(var(--ink))]"
                    )}
                  >
                    <span className={clsx(
                      "flex-shrink-0",
                      isActive ? "text-[hsl(var(--accent))]" : "text-[hsl(var(--ink-muted))]"
                    )}>
                      {getCategoryIcon(category.code)}
                    </span>
                    <span className="flex-1 text-sm font-medium truncate">{category.name}</span>
                  </button>
                  
                  {/* 统计数字 */}
                  {stats && (
                    <span className={clsx(
                      "text-xs tabular-nums flex-shrink-0",
                      stats.selected > 0
                        ? "text-[hsl(var(--accent))]"
                        : "text-[hsl(var(--ink-muted))]"
                    )}>
                      {stats.selected}/{stats.total}
                    </span>
                  )}
                </div>
                
                {/* 子分类 */}
                {hasSubcategories && category.subcategories?.map((sub) => {
                  const subStats = categoryStats[sub.code];
                  const isSubActive = activeCategory === sub.code;
                  const subCheckState = getCategoryCheckState(sub);
                  
                  return (
                    <div
                      key={sub.code}
                      className={clsx(
                        "flex items-center gap-2 pl-6 pr-3 py-2 transition-colors",
                        isSubActive
                          ? "bg-[hsl(var(--accent))]/10 border-r-2 border-[hsl(var(--accent))]"
                          : "hover:bg-[hsl(var(--sand-2))]"
                      )}
                    >
                      {/* 子分类勾选框 */}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleCategory(sub);
                        }}
                        disabled={disabled}
                        className={clsx(
                          "flex h-3.5 w-3.5 items-center justify-center rounded border transition-colors flex-shrink-0 cursor-pointer",
                          subCheckState === "all"
                            ? "bg-[hsl(var(--accent))] border-[hsl(var(--accent))]"
                            : subCheckState === "partial"
                            ? "bg-[hsl(var(--accent))]/50 border-[hsl(var(--accent))]"
                            : "border-[hsl(var(--line))] hover:border-[hsl(var(--accent))]"
                        )}
                      >
                        {subCheckState === "all" && <Check className="h-2.5 w-2.5 text-white" />}
                        {subCheckState === "partial" && <Minus className="h-2.5 w-2.5 text-white" />}
                      </button>
                      
                      <button
                        type="button"
                        onClick={() => setActiveCategory(sub.code)}
                        className={clsx(
                          "flex-1 flex items-center gap-1.5 text-left cursor-pointer",
                          isSubActive ? "text-[hsl(var(--accent))]" : "text-[hsl(var(--ink-muted))] hover:text-[hsl(var(--ink))]"
                        )}
                      >
                        <ChevronRight className="h-3 w-3 flex-shrink-0" />
                        <span className="flex-1 text-xs truncate">{sub.name}</span>
                      </button>
                      
                      {subStats && (
                        <span className={clsx(
                          "text-xs tabular-nums flex-shrink-0",
                          subStats.selected > 0
                            ? "text-[hsl(var(--accent))]"
                            : "text-[hsl(var(--ink-muted))]"
                        )}>
                          {subStats.selected}/{subStats.total}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>

        {/* 右侧：权限列表 */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 操作类型过滤 Tab */}
          <div className="flex items-center gap-1 px-4 py-2 border-b border-[hsl(var(--line))] bg-[hsl(var(--sand))]/10">
            <button
              type="button"
              onClick={() => setActionFilter(null)}
              className={clsx(
                "px-3 py-1.5 text-xs font-medium rounded-lg transition-colors cursor-pointer",
                actionFilter === null
                  ? "bg-[hsl(var(--accent))] text-white"
                  : "text-[hsl(var(--ink-muted))] hover:bg-[hsl(var(--sand-2))]"
              )}
            >
              全部
            </button>
            {ACTION_TYPES.map((at) => {
              const count = actionStats[at.code] || 0;
              if (count === 0) return null;
              
              return (
                <button
                  key={at.code}
                  type="button"
                  onClick={() => setActionFilter(actionFilter === at.code ? null : at.code)}
                  className={clsx(
                    "px-3 py-1.5 text-xs font-medium rounded-lg transition-colors cursor-pointer",
                    actionFilter === at.code
                      ? "bg-[hsl(var(--accent))] text-white"
                      : "text-[hsl(var(--ink-muted))] hover:bg-[hsl(var(--sand-2))]"
                  )}
                >
                  {at.name} ({count})
                </button>
              );
            })}
            
            {/* 当前分类的快捷操作 */}
            <div className="ml-auto flex items-center gap-1">
              <button
                type="button"
                onClick={selectAllInCategory}
                disabled={disabled || displayPermissions.length === 0}
                className="px-2 py-1 text-xs text-[hsl(var(--accent))] hover:bg-[hsl(var(--accent))]/10 rounded transition-colors disabled:opacity-50 cursor-pointer"
              >
                全选
              </button>
              <button
                type="button"
                onClick={clearAllInCategory}
                disabled={disabled || displayPermissions.length === 0}
                className="px-2 py-1 text-xs text-[hsl(var(--ink-muted))] hover:bg-[hsl(var(--sand-2))] rounded transition-colors disabled:opacity-50 cursor-pointer"
              >
                清空
              </button>
            </div>
          </div>

          {/* 权限网格 - 按子分类分组显示 */}
          <div className="flex-1 overflow-y-auto p-4">
            {currentCategory ? (
              <PermissionGroupedView
                category={currentCategory}
                selectedSet={selectedSet}
                searchQuery={searchQuery}
                actionFilter={actionFilter}
                disabled={disabled}
                onTogglePermission={togglePermission}
                onToggleSubcategory={toggleCategory}
                getCategoryCheckState={getCategoryCheckState}
              />
            ) : (
              <div className="flex flex-col items-center justify-center h-full text-[hsl(var(--ink-muted))]">
                <Shield className="h-12 w-12 mb-3 opacity-30" />
                <p className="text-sm">请选择左侧分类</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// 分组视图组件 - 按子分类分组显示权限
type PermissionGroupedViewProps = {
  category: PermissionCategory;
  selectedSet: Set<string>;
  searchQuery: string;
  actionFilter: string | null;
  disabled: boolean;
  onTogglePermission: (code: string) => void;
  onToggleSubcategory: (category: PermissionCategory) => void;
  getCategoryCheckState: (category: PermissionCategory) => "all" | "partial" | "none";
};

function PermissionGroupedView({
  category,
  selectedSet,
  searchQuery,
  actionFilter,
  disabled,
  onTogglePermission,
  onToggleSubcategory,
  getCategoryCheckState,
}: PermissionGroupedViewProps) {
  // 过滤权限
  const filterPermissions = (perms: Permission[]): Permission[] => {
    let filtered = perms;
    
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          p.code.toLowerCase().includes(query) ||
          p.description?.toLowerCase().includes(query)
      );
    }
    
    if (actionFilter) {
      filtered = filtered.filter((p) => p.action_type === actionFilter);
    }
    
    return filtered;
  };

  // 如果有子分类，按子分类分组显示
  const hasSubcategories = category.subcategories && category.subcategories.length > 0;
  
  // 当前分类自身的权限（不属于任何子分类）
  const ownPermissions = filterPermissions(category.permissions);
  
  // 子分类及其权限
  const subcategoriesWithPermissions = hasSubcategories
    ? category.subcategories!
        .map((sub) => ({
          ...sub,
          filteredPermissions: filterPermissions(getAllPermissions(sub)),
        }))
        .filter((sub) => sub.filteredPermissions.length > 0)
    : [];

  // 如果没有任何权限显示
  const totalVisible = ownPermissions.length + subcategoriesWithPermissions.reduce((sum, s) => sum + s.filteredPermissions.length, 0);
  
  if (totalVisible === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-[hsl(var(--ink-muted))]">
        <Shield className="h-12 w-12 mb-3 opacity-30" />
        <p className="text-sm">
          {searchQuery || actionFilter ? "没有找到匹配的权限" : "该分类下暂无权限"}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 当前分类自身的权限 */}
      {ownPermissions.length > 0 && (
        <PermissionGroup
          title={category.name}
          permissions={ownPermissions}
          selectedSet={selectedSet}
          disabled={disabled}
          onTogglePermission={onTogglePermission}
          category={category}
          onToggleCategory={onToggleSubcategory}
          getCategoryCheckState={getCategoryCheckState}
        />
      )}
      
      {/* 子分类的权限 */}
      {subcategoriesWithPermissions.map((sub) => (
        <PermissionGroup
          key={sub.code}
          title={sub.name}
          permissions={sub.filteredPermissions}
          selectedSet={selectedSet}
          disabled={disabled}
          onTogglePermission={onTogglePermission}
          category={sub}
          onToggleCategory={onToggleSubcategory}
          getCategoryCheckState={getCategoryCheckState}
        />
      ))}
    </div>
  );
}

// 单个权限分组
type PermissionGroupProps = {
  title: string;
  permissions: Permission[];
  selectedSet: Set<string>;
  disabled: boolean;
  onTogglePermission: (code: string) => void;
  category: PermissionCategory;
  onToggleCategory: (category: PermissionCategory) => void;
  getCategoryCheckState: (category: PermissionCategory) => "all" | "partial" | "none";
};

function PermissionGroup({
  title,
  permissions,
  selectedSet,
  disabled,
  onTogglePermission,
  category,
  onToggleCategory,
  getCategoryCheckState,
}: PermissionGroupProps) {
  const checkState = getCategoryCheckState(category);
  
  return (
    <div className="rounded-xl border border-[hsl(var(--line))] overflow-hidden">
      {/* 分组标题栏 */}
      <div className="flex items-center gap-3 px-4 py-3 bg-[hsl(var(--sand))]/30 border-b border-[hsl(var(--line))]">
        {/* 分组勾选框 */}
        <button
          type="button"
          onClick={() => onToggleCategory(category)}
          disabled={disabled}
          className={clsx(
            "flex h-4 w-4 items-center justify-center rounded border transition-colors flex-shrink-0 cursor-pointer",
            checkState === "all"
              ? "bg-[hsl(var(--accent))] border-[hsl(var(--accent))]"
              : checkState === "partial"
              ? "bg-[hsl(var(--accent))]/50 border-[hsl(var(--accent))]"
              : "border-[hsl(var(--line))] hover:border-[hsl(var(--accent))]"
          )}
        >
          {checkState === "all" && <Check className="h-3 w-3 text-white" />}
          {checkState === "partial" && <Minus className="h-3 w-3 text-white" />}
        </button>
        
        <span className="text-[hsl(var(--ink-muted))]">
          {getCategoryIcon(category.code)}
        </span>
        <span className="text-sm font-semibold text-[hsl(var(--ink))]">{title}</span>
        <span className="text-xs text-[hsl(var(--ink-muted))]">
          ({permissions.length} 项权限)
        </span>
      </div>
      
      {/* 权限网格 */}
      <div className="p-3 grid grid-cols-2 xl:grid-cols-3 gap-2">
        {permissions.map((perm) => {
          const isSelected = selectedSet.has(perm.code);
          const actionConfig = getActionTypeConfig(perm.action_type);
          
          return (
            <button
              key={perm.code}
              type="button"
              onClick={() => onTogglePermission(perm.code)}
              disabled={disabled}
              className={clsx(
                "group flex items-start gap-2.5 rounded-lg border px-3 py-2.5 text-left cursor-pointer transition-all duration-200",
                isSelected
                  ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))]/5"
                  : "border-[hsl(var(--line))]/60 hover:border-[hsl(var(--accent))]/50 hover:bg-[hsl(var(--sand))]/30",
                disabled && "opacity-50 cursor-not-allowed"
              )}
            >
              {/* 复选框 */}
              <span
                className={clsx(
                  "flex h-4 w-4 items-center justify-center rounded border transition-colors flex-shrink-0 mt-0.5",
                  isSelected
                    ? "bg-[hsl(var(--accent))] border-[hsl(var(--accent))]"
                    : "border-[hsl(var(--line))] group-hover:border-[hsl(var(--accent))]"
                )}
              >
                {isSelected && <Check className="h-3 w-3 text-white" />}
              </span>
              
              {/* 权限信息 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="text-sm font-medium text-[hsl(var(--ink))]">
                    {perm.name}
                  </span>
                  {perm.action_type && (
                    <span className={clsx(
                      "px-1.5 py-0.5 text-xs rounded font-medium",
                      actionConfig.bg,
                      actionConfig.color
                    )}>
                      {perm.action_type_display || actionConfig.name}
                    </span>
                  )}
                </div>
                {perm.description && (
                  <p className="text-xs text-[hsl(var(--ink-muted))] mt-0.5 line-clamp-1">
                    {perm.description}
                  </p>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
