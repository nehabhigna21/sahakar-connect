import { useEffect, useState } from "react";
import * as api from "../../api";
import { CategoryIcon } from "../../categoryIcons";

export default function BookService() {
  const [categories, setCategories] = useState([]);
  const [selected, setSelected] = useState(null);
  const [zone, setZone] = useState("Zone-1");
  const [isEmergency, setIsEmergency] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.listCategories().then(setCategories);
  }, []);

  async function handleBook(e) {
    e.preventDefault();
    setMessage("");
    try {
      const booking = await api.createBooking({
        category_id: selected.id,
        zone,
        lat: 0,
        lng: 0,
        is_emergency: isEmergency,
      });
      setMessage(
        booking.status === "matched"
          ? `Booked! ${booking.match_reason}`
          : "Booked, but no worker is available yet."
      );
      setSelected(null);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <section className="card">
      <h1 className="page-title">What do you need done?</h1>
      <p className="page-subtitle">Pick a service to book a verified cooperative worker.</p>

      <div className="category-grid">
        {categories.map((c) => (
          <div
            key={c.id}
            className={"category-card" + (selected?.id === c.id ? " selected" : "")}
            onClick={() => setSelected(c)}
          >
            <span className="category-icon">
              <CategoryIcon name={c.name} />
            </span>
            <div className="category-name">{c.name}</div>
            <div className="category-price">from Rs.{c.base_price}</div>
          </div>
        ))}
        {categories.length === 0 && <p className="muted">No services available yet.</p>}
      </div>

      {selected && (
        <form onSubmit={handleBook} className="grid-form" style={{ marginTop: 20 }}>
          <p>
            Booking <strong>{selected.name}</strong> - Rs.{selected.base_price}
          </p>
          <label>
            Zone
            <input value={zone} onChange={(e) => setZone(e.target.value)} />
          </label>
          <label className="checkbox-row">
            <input
              type="checkbox"
              checked={isEmergency}
              onChange={(e) => setIsEmergency(e.target.checked)}
            />
            Emergency
          </label>
          <button type="submit">Confirm booking</button>
        </form>
      )}
      {message && <p className="notice">{message}</p>}
    </section>
  );
}
