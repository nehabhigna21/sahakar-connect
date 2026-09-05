import { useEffect, useState } from "react";
import * as api from "../../api";
import { CategoryIcon } from "../../categoryIcons";
import { useLocationSearch } from "../../context/LocationSearchContext";

export default function BookService() {
  const { zone, search } = useLocationSearch();
  const [categories, setCategories] = useState([]);
  const [selected, setSelected] = useState(null);
  const [isEmergency, setIsEmergency] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.listCategories().then(setCategories);
  }, []);

  const visibleCategories = categories.filter((c) =>
    c.name.toLowerCase().includes(search.trim().toLowerCase())
  );

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
      <p className="page-subtitle">
        Booking in <strong>{zone}</strong> - change your zone in the top bar.
      </p>

      <div className="category-grid">
        {visibleCategories.map((c) => (
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
        {categories.length > 0 && visibleCategories.length === 0 && (
          <p className="muted">No services match "{search}".</p>
        )}
      </div>

      {selected && (
        <form onSubmit={handleBook} className="grid-form" style={{ marginTop: 20 }}>
          <p>
            Booking <strong>{selected.name}</strong> in <strong>{zone}</strong> - Rs.
            {selected.base_price}
          </p>
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
