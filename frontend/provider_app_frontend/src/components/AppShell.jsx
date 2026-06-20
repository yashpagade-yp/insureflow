import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const navigationItems = [
  { to: "/app/dashboard", label: "Command center" },
  { to: "/app/companies", label: "Company network" },
  { to: "/app/plans", label: "Plan studio" },
  { to: "/app/operations", label: "Live operations" },
];

function AppShell() {
  const { auth, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar-panel">
        <div className="brand-lockup">
          <span className="brand-badge">PX</span>
          <div>
            <p className="eyebrow-text">Provider exchange</p>
            <h1 className="sidebar-main-title">InsureFlow Provider OS</h1>
            <p className="sidebar-subcopy">
              Operational workspace for carrier onboarding, plan control, and quote activity.
            </p>
          </div>
        </div>

        <div className="shell-status-card">
          <p className="eyebrow-text">Workspace status</p>
          <div className="shell-status-grid">
            <div className="shell-mini-kpi">
              <strong>Live</strong>
              <span>Provider APIs connected</span>
            </div>
            <div className="shell-mini-kpi">
              <strong>Secure</strong>
              <span>OTP-protected admin access</span>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? "nav-item nav-item-active" : "nav-item"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <p className="sidebar-label">Signed in as</p>
          <p className="sidebar-value">{auth?.email}</p>
          <button type="button" className="ghost-button" onClick={logout}>
            Logout
          </button>
        </div>
      </aside>

      <main className="content-panel">
        <div className="shell-toolbar">
          <div className="toolbar-meta">
            <span className="toolbar-chip">
              <span className="toolbar-dot" />
              Provider backend online
            </span>
            <span className="toolbar-chip">Internal operations console</span>
          </div>
          <div className="toolbar-actions">
            <span className="toolbar-chip">{auth?.email || "Provider admin"}</span>
          </div>
        </div>
        <header className="page-topbar">
          <div>
            <p className="eyebrow-text">Provider operating system</p>
            <h2>Control insurer onboarding, plan publishing, and live quote operations</h2>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}

export default AppShell;
