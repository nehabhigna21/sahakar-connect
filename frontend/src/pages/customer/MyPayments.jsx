import { useEffect, useState } from "react";
import * as api from "../../api";

export default function MyPayments() {
  const [payments, setPayments] = useState([]);

  useEffect(() => {
    api.listMyPayments().then(setPayments);
  }, []);

  return (
    <section className="card">
      <h1 className="page-title">My payments</h1>
      <ul className="list">
        {payments.map((p) => (
          <li key={p.id}>
            Booking #{p.booking_id} - Rs.{p.amount} total, Rs.{p.platform_fee} platform fee
            <div className="muted">{p.invoice_note}</div>
          </li>
        ))}
        {payments.length === 0 && <li className="muted">No payments yet.</li>}
      </ul>
    </section>
  );
}
