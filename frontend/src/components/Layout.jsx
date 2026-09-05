import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useLocationSearch } from "../context/LocationSearchContext";
import Avatar from "./Avatar";
import * as api from "../api";
import { PiggyBank } from "lucide-react";

const NAV = {
  customer: [
    { to: "/customer/book", label: "Book a service" },
    { to: "/customer/bookings", label: "My bookings" },
    { to: "/customer/payments", label: "My payments" },
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
  const { zone, setZone, search, setSearch } = useLocationSearch();
  const navigate = useNavigate();
  const [piggybankBalance, setPiggybankBalance] = useState(null);

  useEffect(() => {
    if (user.role === "worker") {
      api.getMyWorkerProfile().then((p) => setPiggybankBalance(p.piggybank_balance));
    }
  }, [user.role]);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const links = NAV[user.role] || [];

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">Sahakar Connect</div>

        {user.role === "customer" && (
          <div className="topbar-search">
            <input
              className="location-input"
              value={zone}
              onChange={(e) => setZone(e.target.value)}
              title="Your service zone"
              placeholder="Zone / location"
            />
            <input
              className="search-input"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search services..."
            />
          </div>
        )}

        <nav>
          {user.role === "worker" && piggybankBalance !== null && (
            <NavLink to="/worker/piggybank" className="piggybank-pill">
              <PiggyBank size={16} /> Rs.{piggybankBalance}
            </NavLink>
          )}
          <Avatar name={user.name} />
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
