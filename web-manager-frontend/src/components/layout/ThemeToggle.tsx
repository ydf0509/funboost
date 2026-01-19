"use client";

import clsx from "clsx";
import { Moon, Sun } from "lucide-react";
import { useEffect, useState } from "react";

import { applyTheme, getStoredTheme, getSystemTheme, setStoredTheme, type Theme } from "@/lib/theme";

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>("light");

  useEffect(() => {
    const stored = getStoredTheme();
    const initial = stored ?? getSystemTheme();
    setTheme(initial);
    applyTheme(initial);
  }, []);

  const toggleTheme = () => {
    const next: Theme = theme === "dark" ? "light" : "dark";
    setTheme(next);
    applyTheme(next);
    setStoredTheme(next);
  };

  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-pressed={isDark}
      aria-label={`切换为${isDark ? "亮色" : "暗色"}模式`}
      className={clsx(
        "inline-flex items-center gap-2 rounded-full border border-[hsl(var(--line))] bg-[hsl(var(--card))]/80 px-3 py-1 text-[11px] font-semibold",
        "uppercase tracking-[0.18em] text-[hsl(var(--ink))] transition hover:border-[hsl(var(--accent))]",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(var(--accent))] focus-visible:ring-offset-2 focus-visible:ring-offset-[hsl(var(--sand))]"
      )}
    >
      <span>{isDark ? "暗色" : "亮色"}</span>
      {isDark ? (
        <Moon className="h-3.5 w-3.5 text-[hsl(var(--accent-2))]" />
      ) : (
        <Sun className="h-3.5 w-3.5 text-[hsl(var(--accent-3))]" />
      )}
    </button>
  );
}
