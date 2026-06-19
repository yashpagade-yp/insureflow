import { Navigate, Route, Routes } from "react-router-dom";

import AdminLayout from "./components/AdminLayout";
import ProtectedRoute from "./components/ProtectedRoute";
import CustomerLayout from "./components/CustomerLayout";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminPolicyHubPage from "./pages/AdminPolicyHubPage";
import AdminVerifyOtpPage from "./pages/AdminVerifyOtpPage";
import CallingBotAdminPage from "./pages/CallingBotAdminPage";
import CustomerDashboardPage from "./pages/CustomerDashboardPage";
import CustomerLoginPage from "./pages/CustomerLoginPage";
import CustomerVerifyOtpPage from "./pages/CustomerVerifyOtpPage";
import HomePage from "./pages/HomePage";
import JourneyPage from "./pages/JourneyPage";
import QuotesPage from "./pages/QuotesPage";
import ChatBotPage from "./pages/ChatBotPage";
import VoiceBotPage from "./pages/VoiceBotPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/chat" element={<ChatBotPage />} />
      <Route path="/voice" element={<VoiceBotPage />} />
      <Route path="/journey/new" element={<JourneyPage />} />
      <Route path="/journey/quotes" element={<QuotesPage />} />
      <Route path="/customer/login" element={<CustomerLoginPage />} />
      <Route path="/customer/verify" element={<CustomerVerifyOtpPage />} />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route path="/admin/verify" element={<AdminVerifyOtpPage />} />

      <Route
        path="/customer/app"
        element={
          <ProtectedRoute expectedRole="USER">
            <CustomerLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/customer/app/dashboard" replace />} />
        <Route path="dashboard" element={<CustomerDashboardPage />} />
        <Route path="quotes" element={<QuotesPage />} />
      </Route>

      <Route
        path="/admin/app"
        element={
          <ProtectedRoute expectedRole="ADMIN">
            <AdminLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/admin/app/dashboard" replace />} />
        <Route path="dashboard" element={<AdminDashboardPage />} />
        <Route path="calling-bot" element={<CallingBotAdminPage />} />
        <Route path="policies" element={<AdminPolicyHubPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
