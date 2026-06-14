import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

const navigationItems = [
  { to: "/app/dashboard", label: "Overview" },
  { to: "/app/companies", label: "Companies" },
  { to: "/app/plans", label: "Plans" },
];

function AppShell() {
  const { auth, logout } = useAuth();

  return (
    <div className="app-shell">
      <aside className="sidebar-panel">
        <div className="brand-lockup">
          <span className="brand-badge">IF</span>
          <div>
            <p className="eyebrow-text">InsureFlow</p>
            <h1>Health Provider Console</h1>
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
        <header className="page-topbar">
          <div>
            <p className="eyebrow-text">Health insurance admin workspace</p>
            <h2>Manage insurer onboarding, network partners, and health plans</h2>
          </div>
        </header>
        <Outlet />
      </main>
    </div>
  );
}

export default AppShell;
