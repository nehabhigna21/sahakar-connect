import { useEffect, useState } from "react";
import * as api from "../../api";

export default function Earnings() {
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    api.listMyPayments().then(setPayments);
  }, []);

  return (
    <section className="card">
      <h1 className="page-title">Earnings breakdown</h1>
      <ul className="list">
        {payments.map((p) => (
          <li key={p.id}>
            Booking #{p.booking_id} - you keep Rs.{p.worker_payout} (flat fee Rs.{p.platform_fee})
          </li>
        ))}
        {payments.length === 0 && <li className="muted">No completed jobs yet.</li>}
      </ul>
    </section>
  );
}
