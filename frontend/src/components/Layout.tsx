import { Link, Outlet } from "react-router-dom";

import { ShieldIcon } from "./Icon";
import { ThemeToggle } from "./ThemeToggle";

export function Layout() {
  return (
    <>
      <header className="topbar">
        <Link to="/targets" className="topbar__brand">
          <span style={{ color: "var(--accent)", display: "flex" }}>
            <ShieldIcon />
          </span>
          VulnScan
        </Link>
        <div style={{ flexGrow: 1 }} />
        <span className="mono" style={{ fontSize: 11, color: "var(--ink-3)" }}>
          laboratorio local
        </span>
        <ThemeToggle />
      </header>
      <main className="content">
        <Outlet />
      </main>
    </>
  );
}

/** Breadcrumb trail; the last entry is the current page and is not a link. */
export function Crumbs({ items }: { items: { label: string; to?: string }[] }) {
  return (
    <nav className="crumbs" style={{ marginBottom: 14 }}>
      {items.map((item, index) => (
        <span key={item.label} className="row" style={{ gap: 7 }}>
          {index > 0 && <span aria-hidden="true">/</span>}
          {item.to ? (
            <Link to={item.to}>{item.label}</Link>
          ) : (
            <span style={{ color: "var(--ink-2)" }}>{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
