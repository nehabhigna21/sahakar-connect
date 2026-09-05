import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Register from "./pages/Register";

import BookService from "./pages/customer/BookService";
import CustomerBookings from "./pages/customer/MyBookings";
import CustomerPayments from "./pages/customer/MyPayments";
import FileGrievance from "./pages/customer/FileGrievance";

import WorkerProfile from "./pages/worker/Profile";
import WorkerBookings from "./pages/worker/MyBookings";
import Earnings from "./pages/worker/Earnings";
import Piggybank from "./pages/worker/Piggybank";

import Categories from "./pages/admin/Categories";
import Federations from "./pages/admin/Federations";
import AdminGrievances from "./pages/admin/Grievances";
import Verification from "./pages/admin/Verification";
import Forecast from "./pages/admin/Forecast";

import "./App.css";

const HOME_BY_ROLE = {
  customer: "/customer/book",
  worker: "/worker/profile",
  admin: "/admin/categories",
};

function RoleHome() {
  const { user } = useAuth();
  return <Navigate to={HOME_BY_ROLE[user.role]} replace />;
}

function RequireAuth() {
  const { user, loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;
  if (!user) return <Navigate to="/login" replace />;
  return <Layout />;
}

function AppRoutes() {
  const { loading } = useAuth();
  if (loading) return <p className="center">Loading...</p>;

  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<RequireAuth />}>
        <Route index element={<RoleHome />} />

        <Route path="customer/book" element={<BookService />} />
        <Route path="customer/bookings" element={<CustomerBookings />} />
        <Route path="customer/payments" element={<CustomerPayments />} />
        <Route path="customer/grievances" element={<FileGrievance />} />

        <Route path="worker/profile" element={<WorkerProfile />} />
        <Route path="worker/bookings" element={<WorkerBookings />} />
        <Route path="worker/earnings" element={<Earnings />} />
        <Route path="worker/piggybank" element={<Piggybank />} />

        <Route path="admin/categories" element={<Categories />} />
        <Route path="admin/federations" element={<Federations />} />
        <Route path="admin/grievances" element={<AdminGrievances />} />
        <Route path="admin/verification" element={<Verification />} />
        <Route path="admin/forecast" element={<Forecast />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
