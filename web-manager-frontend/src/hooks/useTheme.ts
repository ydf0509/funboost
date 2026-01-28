"use client";

import { useCallback, useEffect, useState } from "react";

import { applyTheme, getStoredTheme, getSystemTheme, setStoredTheme, THEME_STORAGE_KEY, type Theme } from "@/lib/theme";

/**
 * 主题管理 Hook
 * 
 * 提供当前主题状态和切换功能，支持：
 * - 从 localStorage 读取用户偏好
 * - 监听系统主题变化
 * - 监听其他组件的主题切换（通过 storage 事件）
 */
export function useTheme() {
  const [theme, setTheme] = useState<Theme>("light");

  // 初始化主题
  useEffect(() => {
    const stored = getStoredTheme();
    const initial = stored ?? getSystemTheme();
    setTheme(initial);
    applyTheme(initial);
  }, []);

  // 监听 localStorage 变化（其他标签页或组件的主题切换）
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === THEME_STORAGE_KEY && e.newValue) {
        const newTheme = e.newValue as Theme;
        if (newTheme === "light" || newTheme === "dark") {
          setTheme(newTheme);
          applyTheme(newTheme);
        }
      }
    };

    // 监听 DOM 属性变化（同一页面内的主题切换）
    const handleThemeChange = () => {
      const currentTheme = document.documentElement.dataset.theme as Theme;
      if (currentTheme && (currentTheme === "light" || currentTheme === "dark")) {
        setTheme(currentTheme);
      }
    };

    // 使用 MutationObserver 监听 data-theme 属性变化
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === "attributes" && mutation.attributeName === "data-theme") {
          handleThemeChange();
        }
      });
    });

    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });

    window.addEventListener("storage", handleStorageChange);

    return () => {
      observer.disconnect();
      window.removeEventListener("storage", handleStorageChange);
    };
  }, []);

  // 切换主题
  const toggleTheme = useCallback(() => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    setStoredTheme(next);
  }, [theme]);

  // 设置指定主题
  const setThemeValue = useCallback((newTheme: Theme) => {
    setTheme(newTheme);
    applyTheme(newTheme);
    setStoredTheme(newTheme);
  }, []);

  return {
    theme,
    isDark: theme === "dark",
    isLight: theme === "light",
    toggleTheme,
    setTheme: setThemeValue,
  };
}
