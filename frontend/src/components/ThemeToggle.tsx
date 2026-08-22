import { MoonIcon, SunIcon, SystemIcon } from "./Icon";
import { useTheme } from "../lib/useTheme";

const LABELS = {
  system: "Tema del sistema",
  light: "Tema claro",
  dark: "Tema oscuro",
} as const;

export function ThemeToggle() {
  const [preference, cycle] = useTheme();
  return (
    <button
      type="button"
      className="btn"
      onClick={cycle}
      title={LABELS[preference]}
      aria-label={LABELS[preference]}
      style={{ padding: "6px 9px", color: "var(--ink-2)" }}
    >
      {preference === "system" && <SystemIcon />}
      {preference === "light" && <SunIcon />}
      {preference === "dark" && <MoonIcon />}
    </button>
  );
}
