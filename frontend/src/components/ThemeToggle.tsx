import { MoonIcon, SunIcon } from "./Icon";
import { useTheme } from "../lib/useTheme";

// The label and icon name what the click does, not the current state: a
// button labelled "Tema oscuro" reads the same whether it means "you are in
// dark" or "switch to dark".
export function ThemeToggle() {
  const [theme, toggle] = useTheme();
  const label = theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro";
  return (
    <button
      type="button"
      className="btn"
      onClick={toggle}
      title={label}
      aria-label={label}
      style={{ padding: "6px 9px", color: "var(--ink-2)" }}
    >
      {theme === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}
