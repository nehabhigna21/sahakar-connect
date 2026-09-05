import { useEffect, useState } from "react";
import * as api from "../../api";
import StatusBadge from "../../components/StatusBadge";

export default function Grievances() {
  const [grievances, setGrievances] = useState([]);

  function refresh() {
    api.listGrievances().then(setGrievances);
  }

  useEffect(refresh, []);

  async function handleResolve(id, status, suspend) {
    await api.resolveGrievance(id, {
      status,
      resolution_note: `${status} by admin`,
      suspend_worker: suspend,
    });
    refresh();
  }

  return (
    <section className="card">
      <h1 className="page-title">Grievance dashboard</h1>
      <ul className="list">
        {grievances.map((g) => (
          <li key={g.id}>
            <div className="booking-row">
              <div>
                <strong>#{g.id}</strong> {g.description}
              </div>
              <StatusBadge status={g.status} />
            </div>
            <div className="muted">
              filed by user #{g.filed_by_id}
              {g.against_worker_id ? `, against worker #${g.against_worker_id}` : ""}
            </div>
            {g.status === "open" && (
              <div className="actions">
                <button onClick={() => handleResolve(g.id, "resolved", false)}>Resolve</button>
                <button onClick={() => handleResolve(g.id, "resolved", true)} className="danger">
                  Resolve + suspend worker
                </button>
                <button onClick={() => handleResolve(g.id, "dismissed", false)}>Dismiss</button>
              </div>
            )}
          </li>
        ))}
        {grievances.length === 0 && <li className="muted">No grievances.</li>}
      </ul>
    </section>
  );
}
