import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

// Also read by public/theme-init.js, which applies it before first paint.
const STORAGE_KEY = "vulnscan-theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

// Storage access throws in some private modes; a theme preference is a
// convenience, so failing to read or write it must never break the page.
function readStored(): Theme | null {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored === "light" || stored === "dark" ? stored : null;
  } catch {
    return null;
  }
}

function writeStored(theme: Theme) {
  try {
    localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // Not persisted; the choice still applies for this page view.
  }
}

function systemTheme(): Theme {
  return typeof window.matchMedia === "function" && window.matchMedia(DARK_QUERY).matches
    ? "dark"
    : "light";
}

/**
 * The effective theme and a toggle between light and dark.
 *
 * Two states, not three: a "follow the system" state always looks identical
 * to one of the other two, so cycling through it made one click in three
 * change nothing on screen. Until the viewer clicks, no `data-theme` is set
 * and the stylesheet's prefers-color-scheme block decides; the first click
 * stores an explicit choice, which then wins in both directions.
 */
export function useTheme(): [Theme, () => void] {
  const [chosen, setChosen] = useState<Theme | null>(readStored);
  const [system, setSystem] = useState<Theme>(systemTheme);

  // Keep the button's label right if the OS theme changes while no
  // explicit choice has been made.
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const query = window.matchMedia(DARK_QUERY);
    const onChange = () => setSystem(query.matches ? "dark" : "light");
    query.addEventListener("change", onChange);
    return () => query.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    if (chosen === null) return;
    document.documentElement.setAttribute("data-theme", chosen);
    writeStored(chosen);
  }, [chosen]);

  const theme = chosen ?? system;
  const toggle = useCallback(() => setChosen(theme === "dark" ? "light" : "dark"), [theme]);

  return [theme, toggle];
}
