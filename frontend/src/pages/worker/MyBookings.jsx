import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "../../api";
import StatusBadge from "../../components/StatusBadge";

export default function MyBookings() {
  const [bookings, setBookings] = useState([]);

  function refresh() {
    api.listMyBookings().then(setBookings);
  }

  useEffect(refresh, []);

  async function handleComplete(id) {
    await api.completeBooking(id);
    refresh();
  }

  return (
    <section className="card">
      <h1 className="page-title">My bookings</h1>
      <ul className="list">
        {bookings.map((b) => (
          <li key={b.id}>
            <div className="booking-row">
              <div>
                <strong>#{b.id}</strong> · Rs.{b.price}
              </div>
              <StatusBadge status={b.status} />
            </div>
            {b.match_reason && <div className="muted">{b.match_reason}</div>}
            <div className="actions">
              {b.status === "matched" && (
                <button onClick={() => handleComplete(b.id)}>Mark completed</button>
              )}
              <Link to={`/grievances?booking_id=${b.id}`}>
                <button className="danger">File a grievance</button>
              </Link>
            </div>
          </li>
        ))}
        {bookings.length === 0 && <li className="muted">No bookings yet.</li>}
      </ul>
    </section>
  );
}
