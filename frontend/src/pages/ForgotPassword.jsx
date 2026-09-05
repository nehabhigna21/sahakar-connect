import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import * as api from "../api";
import { useAuth } from "../context/AuthContext";

export default function ForgotPassword() {
  const { setUser } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    try {
      const data = await api.resetPassword(email, newPassword);
      localStorage.setItem("token", data.access_token);
      setUser(data.user);
      navigate("/");
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="center">
      <div className="card auth-card">
        <h1>Reset password</h1>
        <p className="page-subtitle">
          Prototype note: this resets your password directly by email, with no
          verification link (no email service is wired up yet).
        </p>
        <form onSubmit={handleSubmit} className="grid-form">
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            New password
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit">Reset password</button>
        </form>
        <p className="muted">
          <Link to="/login">Back to login</Link>
        </p>
      </div>
    </div>
  );
}
