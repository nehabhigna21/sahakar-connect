const BASE_URL = "http://localhost:8000";

function getToken() {
  return localStorage.getItem("token");
}

async function parseError(res) {
  try {
    const data = await res.json();
    return data.detail || res.statusText;
  } catch {
    return res.statusText;
  }
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return null;
  return res.json();
}

// ---------- auth ----------
export const register = (payload) =>
  request("/auth/register", { method: "POST", body: payload, auth: false });

export async function login(email, password) {
  const form = new URLSearchParams();
  form.set("username", email);
  form.set("password", password);
  const res = await fetch(`${BASE_URL}/auth/login`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export const resetPassword = (email, new_password) =>
  request("/auth/reset-password", { method: "POST", body: { email, new_password }, auth: false });

export const getMe = () => request("/auth/me");
export const updateMyAddress = (address) =>
  request("/auth/me", { method: "PATCH", body: { address } });
export const verifyHousehold = (userId) =>
  request(`/auth/${userId}/verify-household`, { method: "POST" });

// ---------- catalog ----------
export const listCategories = (lang = "en") =>
  request(`/categories?lang=${lang}`, { auth: false });
export const createCategory = (payload) =>
  request("/categories", { method: "POST", body: payload });
export const listFederations = () => request("/federations", { auth: false });
export const createFederation = (payload) =>
  request("/federations", { method: "POST", body: payload });

// ---------- workers ----------
export const getMyWorkerProfile = () => request("/workers/me");
export const updateMyWorkerProfile = (payload) =>
  request("/workers/me", { method: "PATCH", body: payload });
export const verifyWorker = (workerId) =>
  request(`/workers/${workerId}/verify`, { method: "POST" });

// ---------- bookings ----------
export const createBooking = (payload) =>
  request("/bookings", { method: "POST", body: payload });
export const listMyBookings = () => request("/bookings");
export const completeBooking = (bookingId) =>
  request(`/bookings/${bookingId}/complete`, { method: "POST" });

// ---------- reviews ----------
export const createReview = (payload) =>
  request("/reviews", { method: "POST", body: payload });
export const listMyReviews = () => request("/reviews/mine");

// ---------- payments ----------
export const listMyPayments = () => request("/payments/me");

// ---------- piggybank ----------
export const listMyPiggybankLedger = () => request("/piggybank/me");

// ---------- grievances ----------
export const fileGrievance = (payload) =>
  request("/grievances", { method: "POST", body: payload });
export const listGrievances = () => request("/grievances");
export const resolveGrievance = (id, payload) =>
  request(`/grievances/${id}/resolve`, { method: "POST", body: payload });

// ---------- forecast / shifts ----------
export const listDemandForecasts = () => request("/forecast/demand");
export const recomputeForecast = (weekStart) =>
  request("/forecast/recompute", { method: "POST", body: { week_start: weekStart } });
export const listShifts = () => request("/forecast/shifts");

// ---------- bandit ----------
export const listBanditArms = () => request("/bandit/arms");
