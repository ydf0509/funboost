"use client";

import clsx from "clsx";
import { ChevronDown, FolderKanban, Loader2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { useProject, type Project } from "@/contexts/ProjectContext";

/**
 * 项目选择器组件
 *
 * 显示在顶部导航栏，允许用户切换当前查看的项目。
 * 切换项目时会更新 context 和 localStorage。
 *
 * @example
 * ```tsx
 * // 在 TopBar 中使用
 * <ProjectSelector />
 * ```
 */
export function ProjectSelector() {
  const { projects, currentProject, setCurrentProject, isLoading, error } = useProject();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  /**
   * 处理项目选择
   */
  const handleSelectProject = useCallback(
    (project: Project) => {
      setCurrentProject(project);
      setIsOpen(false);
    },
    [setCurrentProject]
  );

  /**
   * 点击外部关闭下拉菜单
   */
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  /**
   * 键盘导航支持
   */
  const handleKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      } else if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setIsOpen((prev) => !prev);
      }
    },
    []
  );

  // 加载中状态
  if (isLoading) {
    return (
      <div className="flex items-center gap-2 rounded-full border border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 px-4 py-2 text-sm text-[hsl(var(--ink-muted))]">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>加载项目...</span>
      </div>
    );
  }

  // 错误状态
  if (error) {
    return (
      <div className="flex items-center gap-2 rounded-full border border-[hsl(var(--danger))]/30 bg-[hsl(var(--danger))]/10 px-4 py-2 text-sm text-[hsl(var(--danger))]">
        <FolderKanban className="h-4 w-4" />
        <span>加载失败</span>
      </div>
    );
  }

  // 无项目状态
  if (projects.length === 0) {
    return (
      <div className="flex items-center gap-2 rounded-full border border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 px-4 py-2 text-sm text-[hsl(var(--ink-muted))]">
        <FolderKanban className="h-4 w-4" />
        <span>无可用项目</span>
      </div>
    );
  }

  return (
    <div ref={dropdownRef} className="relative">
      {/* 触发按钮 */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        onKeyDown={handleKeyDown}
        className={clsx(
          "flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition",
          isOpen
            ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))]/20 text-[hsl(var(--accent-2))]"
            : "border-[hsl(var(--accent))]/30 bg-[hsl(var(--accent))]/10 text-[hsl(var(--accent-2))] hover:bg-[hsl(var(--accent))]/20"
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label="选择项目"
      >
        <FolderKanban className="h-4 w-4" />
        <span className="max-w-[120px] truncate">
          {currentProject?.name || "选择项目"}
        </span>
        <ChevronDown
          className={clsx(
            "h-4 w-4 transition-transform duration-200",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {/* 下拉菜单 */}
      {isOpen && (
        <div
          className="absolute left-0 top-full z-50 mt-2 min-w-[200px] max-w-[280px] rounded-2xl border border-[hsl(var(--line))] bg-[hsl(var(--card))] py-2 shadow-lg backdrop-blur-xl"
          role="listbox"
          aria-label="项目列表"
        >
          {/* 项目列表标题 */}
          <div className="px-4 py-2 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--ink-muted))]">
            切换项目
          </div>

          {/* 项目列表 */}
          <div className="max-h-[300px] overflow-y-auto">
            {projects.map((project) => {
              const isSelected = currentProject?.id === project.id;
              return (
                <button
                  key={project.id}
                  type="button"
                  onClick={() => handleSelectProject(project)}
                  className={clsx(
                    "flex w-full items-start gap-3 px-4 py-2.5 text-left transition",
                    isSelected
                      ? "bg-[hsl(var(--accent))]/10 text-[hsl(var(--accent-2))]"
                      : "text-[hsl(var(--ink))] hover:bg-[hsl(var(--sand-2))]"
                  )}
                  role="option"
                  aria-selected={isSelected}
                >
                  <FolderKanban
                    className={clsx(
                      "mt-0.5 h-4 w-4 flex-shrink-0",
                      isSelected ? "text-[hsl(var(--accent-2))]" : "text-[hsl(var(--ink-muted))]"
                    )}
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="truncate font-medium">{project.name}</span>
                      {project.status === "archived" && (
                        <span className="flex-shrink-0 rounded-full bg-[hsl(var(--ink-muted))]/20 px-1.5 py-0.5 text-[10px] text-[hsl(var(--ink-muted))]">
                          已归档
                        </span>
                      )}
                    </div>
                    {project.description && (
                      <p className="mt-0.5 truncate text-xs text-[hsl(var(--ink-muted))]">
                        {project.description}
                      </p>
                    )}
                    {project.permission_level && (
                      <span
                        className={clsx(
                          "mt-1 inline-block rounded-full px-1.5 py-0.5 text-[10px]",
                          project.permission_level === "admin"
                            ? "bg-[hsl(var(--accent))]/20 text-[hsl(var(--accent-2))]"
                            : project.permission_level === "write"
                            ? "bg-[hsl(var(--success))]/20 text-[hsl(var(--success))]"
                            : "bg-[hsl(var(--ink-muted))]/20 text-[hsl(var(--ink-muted))]"
                        )}
                      >
                        {project.permission_level === "admin"
                          ? "管理员"
                          : project.permission_level === "write"
                          ? "读写"
                          : "只读"}
                      </span>
                    )}
                  </div>
                  {isSelected && (
                    <span className="flex-shrink-0 text-[hsl(var(--accent-2))]">✓</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
