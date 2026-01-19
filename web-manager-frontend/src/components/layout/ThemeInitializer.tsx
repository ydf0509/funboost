"use client";

import { useEffect } from "react";

import { applyTheme, getStoredTheme, getSystemTheme } from "@/lib/theme";

export function ThemeInitializer() {
  useEffect(() => {
    const stored = getStoredTheme();
    if (stored) {
      applyTheme(stored);
      return;
    }

    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const applyFromMedia = (matches: boolean) => {
      applyTheme(matches ? "dark" : "light");
    };

    applyFromMedia(media.matches);

    const handleChange = (event: MediaQueryListEvent) => {
      if (!getStoredTheme()) {
        applyFromMedia(event.matches);
      }
    };

    if (media.addEventListener) {
      media.addEventListener("change", handleChange);
      return () => media.removeEventListener("change", handleChange);
    }

    media.addListener(handleChange);
    return () => media.removeListener(handleChange);
  }, []);

  return null;
}
