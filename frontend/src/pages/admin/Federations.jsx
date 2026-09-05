import { useEffect, useState } from "react";
import * as api from "../../api";

export default function Federations() {
  const [federations, setFederations] = useState([]);
  const [form, setForm] = useState({ name: "", region: "" });
  const [message, setMessage] = useState("");

  function refresh() {
    api.listFederations().then(setFederations);
  }

  useEffect(refresh, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    try {
      await api.createFederation(form);
      setForm({ name: "", region: "" });
      refresh();
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <section className="card">
      <h1 className="page-title">Federations</h1>
      <form onSubmit={handleSubmit} className="grid-form">
        <label>
          Name
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </label>
        <label>
          Region
          <input
            value={form.region}
            onChange={(e) => setForm({ ...form, region: e.target.value })}
            required
          />
        </label>
        <button type="submit">Add</button>
      </form>
      {message && <p className="notice">{message}</p>}
      <ul className="list">
        {federations.map((f) => (
          <li key={f.id}>
            {f.name} - {f.region}
          </li>
        ))}
        {federations.length === 0 && <li className="muted">No federations yet.</li>}
      </ul>
    </section>
  );
}
