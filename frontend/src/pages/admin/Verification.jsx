import { useState } from "react";
import * as api from "../../api";

export default function Verification() {
  const [verifyWorkerId, setVerifyWorkerId] = useState("");
  const [verifyHouseholdId, setVerifyHouseholdId] = useState("");
  const [message, setMessage] = useState("");

  async function handleVerifyWorker(e) {
    e.preventDefault();
    setMessage("");
    try {
      const result = await api.verifyWorker(Number(verifyWorkerId));
      setMessage(`Worker #${result.id}: ${result.verification_status} - ${result.certification_note}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function handleVerifyHousehold(e) {
    e.preventDefault();
    setMessage("");
    try {
      const result = await api.verifyHousehold(Number(verifyHouseholdId));
      setMessage(`User #${result.id} household verified: ${result.household_verified}`);
    } catch (err) {
      setMessage(err.message);
    }
  }

  return (
    <div className="dashboard">
      <section className="card">
        <h2 className="page-title">Verify a worker (e-Shram/NSDC)</h2>
        <form onSubmit={handleVerifyWorker} className="grid-form">
          <label>
            Worker profile ID
            <input value={verifyWorkerId} onChange={(e) => setVerifyWorkerId(e.target.value)} required />
          </label>
          <button type="submit">Run verification</button>
        </form>
      </section>

      <section className="card">
        <h2 className="page-title">Verify a household</h2>
        <form onSubmit={handleVerifyHousehold} className="grid-form">
          <label>
            User ID
            <input
              value={verifyHouseholdId}
              onChange={(e) => setVerifyHouseholdId(e.target.value)}
              required
            />
          </label>
          <button type="submit">Verify</button>
        </form>
      </section>

      {message && <p className="notice">{message}</p>}
    </div>
  );
}
