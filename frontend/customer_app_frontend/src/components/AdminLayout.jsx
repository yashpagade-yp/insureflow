import { NavLink, Outlet } from "react-router-dom";

import { useSession } from "../context/SessionContext";

function AdminLayout() {
  const { session, logout } = useSession();

  return (
    <div className="portal-layout">
      <aside className="portal-sidebar portal-sidebar-admin">
        <div className="brand-stack">
          <span className="brand-monogram brand-monogram-admin">AD</span>
          <div>
            <p className="eyebrow-text">InsureFlow</p>
            <h1>Admin Operations</h1>
          </div>
        </div>

        <nav className="portal-nav">
          <NavLink
            to="/admin/app/dashboard"
            className={({ isActive }) => (isActive ? "portal-link portal-link-active" : "portal-link")}
          >
            Operations
          </NavLink>
          <NavLink
            to="/admin/app/policy-hub"
            className={({ isActive }) => (isActive ? "portal-link portal-link-active" : "portal-link")}
          >
            Policies and tickets
          </NavLink>
        </nav>

        <div className="portal-footer">
          <p className="portal-caption">Admin email</p>
          <strong>{session?.email}</strong>
          <button type="button" className="secondary-button" onClick={logout}>
            Logout
          </button>
        </div>
      </aside>

      <main className="portal-main">
        <Outlet />
      </main>
    </div>
  );
}

export default AdminLayout;
