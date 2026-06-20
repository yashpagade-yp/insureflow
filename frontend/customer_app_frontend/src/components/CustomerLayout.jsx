import { NavLink, Outlet } from "react-router-dom";

import { useSession } from "../context/SessionContext";

function CustomerLayout() {
  const { session, logout } = useSession();

  return (
    <div className="portal-layout">
      <aside className="portal-sidebar portal-sidebar-customer">
        <div className="brand-stack">
          <span className="brand-monogram">IF</span>
          <div>
            <p className="eyebrow-text">InsureFlow</p>
            <h1>Customer Care Portal</h1>
            <p className="portal-intro">
              Keep your policy journey, support, and account details in one calm workspace.
            </p>
          </div>
        </div>

        <nav className="portal-nav">
          <NavLink
            to="/customer/app/dashboard"
            className={({ isActive }) =>
              isActive ? "portal-link portal-link-active" : "portal-link"
            }
          >
            Account overview
          </NavLink>
          <NavLink
            to="/customer/app/quotes"
            className={({ isActive }) =>
              isActive ? "portal-link portal-link-active" : "portal-link"
            }
          >
            Purchase journey
          </NavLink>
        </nav>

        <div className="portal-footer">
          <p className="portal-caption">Signed in mobile</p>
          <strong>{session?.mobileNumber}</strong>
          <p className="portal-caption">
            Use this space to resume progress, check policies, and raise support requests.
          </p>
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

export default CustomerLayout;
