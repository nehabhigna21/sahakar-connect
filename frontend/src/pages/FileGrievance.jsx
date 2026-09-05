import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import * as api from "../api";

export default function FileGrievance() {
  const [searchParams] = useSearchParams();
  const [form, setForm] = useState({
    description: "",
    against_worker_id: "",
    booking_id: searchParams.get("booking_id") || "",
  });
  const [message, setMessage] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setMessage("");
    try {
      await api.fileGrievance({
        description: form.description,
        against_worker_id: form.against_worker_id ? Number(form.against_worker_id) : null,
        booking_id: form.booking_id ? Number(form.booking_id) : null,
      });
      setForm({ description: "", against_worker_id: "", booking_id: "" });
      setMessage("Grievance filed - a federation admin will review it.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <section className="card">
      <h1 className="page-title">File a grievance</h1>
      <form onSubmit={handleSubmit} className="grid-form">
        <label>
          Description
          <textarea
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            required
          />
        </label>
        <label>
          Against worker ID (optional)
          <input
            value={form.against_worker_id}
            onChange={(e) => setForm({ ...form, against_worker_id: e.target.value })}
          />
        </label>
        <label>
          Booking ID (optional)
          <input
            value={form.booking_id}
            onChange={(e) => setForm({ ...form, booking_id: e.target.value })}
          />
        </label>
        <button type="submit">Submit</button>
      </form>
      {message && <p className="notice">{message}</p>}
    </section>
  );
}
