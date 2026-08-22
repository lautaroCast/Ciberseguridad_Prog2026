import { useCallback, useEffect, useState } from "react";

export type ThemePreference = "system" | "light" | "dark";

const STORAGE_KEY = "vulnscan-theme";

function readStored(): ThemePreference {
  if (typeof localStorage === "undefined") return "system";
  const stored = localStorage.getItem(STORAGE_KEY);
  return stored === "light" || stored === "dark" ? stored : "system";
}

/**
 * Theme preference, persisted and reflected as `data-theme` on <html>.
 *
 * "system" removes the attribute entirely so the stylesheet's
 * prefers-color-scheme block takes over; the explicit values override it
 * in both directions.
 */
export function useTheme(): [ThemePreference, () => void] {
  const [preference, setPreference] = useState<ThemePreference>(readStored);

  useEffect(() => {
    const root = document.documentElement;
    if (preference === "system") {
      root.removeAttribute("data-theme");
      localStorage.removeItem(STORAGE_KEY);
    } else {
      root.setAttribute("data-theme", preference);
      localStorage.setItem(STORAGE_KEY, preference);
    }
  }, [preference]);

  const cycle = useCallback(() => {
    setPreference((current) => {
      if (current === "system") return "light";
      if (current === "light") return "dark";
      return "system";
    });
  }, []);

  return [preference, cycle];
}
