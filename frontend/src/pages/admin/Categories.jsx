import { useEffect, useState } from "react";
import * as api from "../../api";

export default function Categories() {
  const [categories, setCategories] = useState([]);
  const [form, setForm] = useState({ name: "", base_price: 300 });
  const [message, setMessage] = useState("");

  function refresh() {
    api.listCategories().then(setCategories);
  }

  useEffect(refresh, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    try {
      await api.createCategory({ name: form.name, base_price: Number(form.base_price) });
      setForm({ name: "", base_price: 300 });
      refresh();
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <section className="card">
      <h1 className="page-title">Service categories</h1>
      <form onSubmit={handleSubmit} className="grid-form">
        <label>
          Name
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required />
        </label>
        <label>
          Base price
          <input
            type="number"
            value={form.base_price}
            onChange={(e) => setForm({ ...form, base_price: e.target.value })}
          />
        </label>
        <button type="submit">Add</button>
      </form>
      {message && <p className="notice">{message}</p>}
      <ul className="list">
        {categories.map((c) => (
          <li key={c.id}>
            {c.name} - Rs.{c.base_price}
          </li>
        ))}
        {categories.length === 0 && <li className="muted">No categories yet.</li>}
      </ul>
    </section>
  );
}
