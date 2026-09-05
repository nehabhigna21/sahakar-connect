import { useState } from "react";
import * as api from "../../api";

export default function Forecast() {
  const [weekStart, setWeekStart] = useState("");
  const [message, setMessage] = useState("");

  async function handleRecompute(e) {
    e.preventDefault();
    setMessage("");
    try {
      const result = await api.recomputeForecast(weekStart);
      setMessage(
        `Recomputed: ${result.forecasts_recomputed} forecasts, ${result.shifts_created} shifts.`
      );
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <section className="card">
      <h1 className="page-title">Demand forecast / shift scheduling</h1>
      <form onSubmit={handleRecompute} className="grid-form">
        <label>
          Week start (Monday)
          <input
            type="date"
            value={weekStart}
            onChange={(e) => setWeekStart(e.target.value)}
            required
          />
        </label>
        <button type="submit">Recompute + schedule</button>
      </form>
      {message && <p className="notice">{message}</p>}
    </section>
  );
}
