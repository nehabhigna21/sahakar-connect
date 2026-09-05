import { useEffect, useState } from "react";
import * as api from "../../api";
import { useAuth } from "../../context/AuthContext";
import Avatar from "../../components/Avatar";
import { Star } from "lucide-react";

export default function Profile() {
  const { user } = useAuth();
  const [profile, setProfile] = useState(null);
  const [form, setForm] = useState(null);
  const [message, setMessage] = useState("");

  function refresh() {
    api.getMyWorkerProfile().then((prof) => {
      setProfile(prof);
      setForm({
        skills: prof.skills,
        zone: prof.zone,
        is_available: prof.is_available,
        eshram_id: prof.eshram_id,
        piggybank_enrolled: prof.piggybank_enrolled,
      });
    });
  }

  useEffect(refresh, []);

  async function handleSave(e) {
    e.preventDefault();
    setMessage("");
    try {
      await api.updateMyWorkerProfile(form);
      setMessage("Profile updated.");
      refresh();
    } catch (err) {
      setMessage(err.message);
    }
  }

  if (!profile || !form) return <p className="center">Loading...</p>;

  return (
    <section className="card">
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 4 }}>
        <Avatar name={user.name} size={44} />
        <h1 className="page-title" style={{ margin: 0 }}>
          {user.name}
        </h1>
      </div>
      <p className="rating-badge" style={{ marginBottom: 12 }}>
        <Star size={14} fill="#ca8a04" color="#ca8a04" /> {profile.rating_avg.toFixed(1)} (
        {profile.rating_count} reviews)
      </p>
      <p>
        Verification: <strong>{profile.verification_status}</strong>
        {profile.is_suspended && <span className="tag danger">suspended</span>}
      </p>
      {profile.certification_note && <p className="muted">{profile.certification_note}</p>}
      <form onSubmit={handleSave} className="grid-form">
        <label>
          Skills (comma-separated)
          <input value={form.skills} onChange={(e) => setForm({ ...form, skills: e.target.value })} />
        </label>
        <label>
          Zone
          <input value={form.zone} onChange={(e) => setForm({ ...form, zone: e.target.value })} />
        </label>
        <label>
          e-Shram / NSDC ID
          <input
            value={form.eshram_id}
            onChange={(e) => setForm({ ...form, eshram_id: e.target.value })}
          />
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.is_available}
            onChange={(e) => setForm({ ...form, is_available: e.target.checked })}
          />
          Available for jobs
        </label>
        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.piggybank_enrolled}
            onChange={(e) => setForm({ ...form, piggybank_enrolled: e.target.checked })}
          />
          Join the patronage-dividend piggybank
        </label>
        <button type="submit">Save</button>
      </form>
      {message && <p className="notice">{message}</p>}
    </section>
  );
}
