import { Link, Outlet } from "react-router-dom";

export function Layout() {
  return (
    <div className="layout">
      <header className="layout__header">
        <Link to="/targets" className="layout__brand">
          VulnScan Platform
        </Link>
      </header>
      <main className="layout__content">
        <Outlet />
      </main>
    </div>
  );
}
