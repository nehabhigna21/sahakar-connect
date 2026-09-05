import { useEffect, useState } from "react";
import * as api from "../../api";

export default function Piggybank() {
  const [profile, setProfile] = useState(null);
  const [ledger, setLedger] = useState([]);

  useEffect(() => {
    api.getMyWorkerProfile().then(setProfile);
    api.listMyPiggybankLedger().then(setLedger);
  }, []);

  return (
    <section className="card">
      <h1 className="page-title">Piggybank ledger</h1>
      <p>
        Balance: <strong>Rs.{profile ? profile.piggybank_balance : "..."}</strong>
      </p>
      <ul className="list">
        {ledger.map((entry) => (
          <li key={entry.id}>
            +Rs.{entry.amount} - balance Rs.{entry.balance_after}
          </li>
        ))}
        {ledger.length === 0 && <li className="muted">No entries yet.</li>}
      </ul>
    </section>
  );
}
