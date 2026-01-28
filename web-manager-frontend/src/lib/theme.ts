export type Theme = "light" | "dark";

export const THEME_STORAGE_KEY = "funboost-theme";

export const getStoredTheme = (): Theme | null => {
  if (typeof window === "undefined") return null;
  const value = window.localStorage.getItem(THEME_STORAGE_KEY);
  return value === "light" || value === "dark" ? value : null;
};

export const getSystemTheme = (): Theme => {
  if (typeof window === "undefined") return "light";
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
};

export const applyTheme = (theme: Theme) => {
  if (typeof document === "undefined") return;
  document.documentElement.dataset.theme = theme;
};

export const setStoredTheme = (theme: Theme) => {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(THEME_STORAGE_KEY, theme);
};
