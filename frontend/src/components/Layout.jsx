import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV = {
  customer: [
    { to: "/customer/book", label: "Book a service" },
    { to: "/customer/bookings", label: "My bookings" },
    { to: "/customer/payments", label: "My payments" },
    { to: "/customer/grievances", label: "File a grievance" },
  ],
  worker: [
    { to: "/worker/profile", label: "My profile" },
    { to: "/worker/bookings", label: "My bookings" },
    { to: "/worker/earnings", label: "Earnings" },
    { to: "/worker/piggybank", label: "Piggybank" },
  ],
  admin: [
    { to: "/admin/categories", label: "Categories" },
    { to: "/admin/federations", label: "Federations" },
    { to: "/admin/grievances", label: "Grievances" },
    { to: "/admin/verification", label: "Verification" },
    { to: "/admin/forecast", label: "Forecast & shifts" },
  ],
};

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const links = NAV[user.role] || [];

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">Sahakar Connect</div>
        <nav>
          <span className="who">
            {user.name} · {user.role}
          </span>
          <button onClick={handleLogout}>Log out</button>
        </nav>
      </header>
      <div className="body-shell">
        <aside className="sidebar">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => "side-link" + (isActive ? " active" : "")}
            >
              {link.label}
            </NavLink>
          ))}
        </aside>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
