"use client";

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  useEffect,
  type ReactNode,
} from "react";

import { funboostFetch } from "@/lib/api";

// ============================================================================
// Types
// ============================================================================

/**
 * 项目类型
 */
export interface Project {
  id: number;
  name: string;
  code: string;
  description?: string;
  status: "active" | "archived";
  permission_level?: "read" | "write" | "admin";
  created_at?: string;
  updated_at?: string;
}

/**
 * 项目上下文值
 */
export interface ProjectContextValue {
  /** 用户可访问的项目列表 */
  projects: Project[];
  /** 当前关注项目（空字符串表示全部项目） */
  careProjectName: string;
  /** 当前选中的项目 */
  currentProject: Project | null;
  /** 设置当前项目 */
  setCurrentProject: (project: Project) => void;
  /** 是否正在加载 */
  isLoading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 检查用户是否有项目访问权限 */
  hasProjectAccess: (projectId: number) => boolean;
  /** 刷新项目列表 */
  refresh: () => Promise<void>;
}

// ============================================================================
// Constants
// ============================================================================

const CARE_PROJECT_CHANGED_EVENT = "careProjectChanged";

// ============================================================================
// Context
// ============================================================================

const ProjectContext = createContext<ProjectContextValue | null>(null);

// ============================================================================
// Provider Component
// ============================================================================

interface ProjectProviderProps {
  children: ReactNode;
}

/**
 * 项目上下文 Provider
 *
 * 提供项目列表和当前项目状态管理，支持：
 * - 从 API 获取用户可访问的项目列表
 * - 与关注项目设置联动，统一全局过滤范围
 * - 项目访问权限检查
 *
 * @example
 * ```tsx
 * // 在 app layout 中使用
 * <ProjectProvider>
 *   {children}
 * </ProjectProvider>
 *
 * // 在组件中使用
 * const { projects, currentProject, setCurrentProject } = useProject();
 *
 * // 切换项目
 * setCurrentProject(project);
 *
 * // 检查项目访问权限
 * if (hasProjectAccess(projectId)) {
 *   // 显示项目数据
 * }
 * ```
 */
export function ProjectProvider({ children }: ProjectProviderProps) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [currentProject, setCurrentProjectState] = useState<Project | null>(null);
  const [careProjectName, setCareProjectName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 项目 ID 集合（用于快速查找）
  const projectIdSet = useMemo(
    () => new Set(projects.map((p) => p.id)),
    [projects]
  );

  /**
   * 从 API 获取用户可访问的项目列表
   */
  const fetchProjects = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      const response = await fetch("/api/user/projects", {
        credentials: "include",
        cache: "no-store",
      });

      if (!response.ok) {
        if (response.status === 401) {
          setProjects([]);
          setCurrentProjectState(null);
          setIsLoading(false);
          return;
        }
        throw new Error(`获取项目列表失败: ${response.status}`);
      }

      const result = await response.json();

      if (result.success && result.data) {
        const projectList: Project[] = result.data.projects || [];
        setProjects(projectList);
      } else {
        throw new Error(result.error || "获取项目列表失败");
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "获取项目列表失败";
      setError(message);
      console.error("获取项目列表失败:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * 设置当前项目
   */
  const setCurrentProject = useCallback((project: Project) => {
    void (async () => {
      try {
        await funboostFetch("/funboost/set_care_project_name", {
          method: "POST",
          json: { care_project_name: project.code },
          cache: "no-store",
        });
        setCareProjectName(project.code);
        if (typeof window !== "undefined") {
          window.dispatchEvent(
            new CustomEvent(CARE_PROJECT_CHANGED_EVENT, {
              detail: { careProjectName: project.code },
            })
          );
        }
      } catch (err) {
        console.error("更新关注项目失败:", err);
      }
    })();
  }, []);

  /**
   * 检查用户是否有项目访问权限
   */
  const hasProjectAccess = useCallback(
    (projectId: number): boolean => {
      return projectIdSet.has(projectId);
    },
    [projectIdSet]
  );

  // 初始加载项目列表
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  const fetchCareProjectName = useCallback(async () => {
    try {
      const data = await funboostFetch<{ care_project_name?: string }>("/funboost/get_care_project_name", {
        cache: "no-store",
      });
      setCareProjectName(data?.care_project_name || "");
    } catch (err) {
      console.error("获取关注项目失败:", err);
      setCareProjectName("");
    }
  }, []);

  useEffect(() => {
    fetchCareProjectName();
  }, [fetchCareProjectName]);

  useEffect(() => {
    if (careProjectName === null) return;

    if (!careProjectName) {
      setCurrentProjectState(null);
      return;
    }

    const matched = projects.find((project) => project.code === careProjectName) || null;
    setCurrentProjectState(matched);
  }, [careProjectName, projects]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleCareProjectChanged = (event: Event) => {
      const detail = (event as CustomEvent<{ careProjectName?: string }>).detail;
      if (detail && typeof detail.careProjectName === "string") {
        setCareProjectName(detail.careProjectName);
        return;
      }
      void fetchCareProjectName();
    };

    window.addEventListener(CARE_PROJECT_CHANGED_EVENT, handleCareProjectChanged);
    return () => {
      window.removeEventListener(CARE_PROJECT_CHANGED_EVENT, handleCareProjectChanged);
    };
  }, [fetchCareProjectName]);

  const contextValue = useMemo<ProjectContextValue>(
    () => ({
      projects,
      careProjectName: careProjectName ?? "",
      currentProject,
      setCurrentProject,
      isLoading,
      error,
      hasProjectAccess,
      refresh: fetchProjects,
    }),
    [
      projects,
      careProjectName,
      currentProject,
      setCurrentProject,
      isLoading,
      error,
      hasProjectAccess,
      fetchProjects,
    ]
  );

  return (
    <ProjectContext.Provider value={contextValue}>
      {children}
    </ProjectContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

/**
 * 使用项目上下文
 *
 * 必须在 ProjectProvider 内部使用
 *
 * @example
 * ```tsx
 * const {
 *   projects,
 *   currentProject,
 *   setCurrentProject,
 *   isLoading,
 *   hasProjectAccess
 * } = useProject();
 *
 * // 获取当前项目
 * console.log(currentProject?.name);
 *
 * // 切换项目
 * setCurrentProject(anotherProject);
 *
 * // 检查项目访问权限
 * if (hasProjectAccess(123)) {
 *   // 用户有权限访问项目 123
 * }
 * ```
 */
export function useProject(): ProjectContextValue {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error("useProject must be used within ProjectProvider");
  }
  return context;
}

// ============================================================================
// Exports
// ============================================================================

export { ProjectContext };
