import { Navigate, Route, Routes } from "react-router-dom";

import AppShell from "./components/AppShell";
import ProtectedRoute from "./components/ProtectedRoute";
import CompaniesPage from "./pages/CompaniesPage";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import PlansPage from "./pages/PlansPage";
import VerifyOtpPage from "./pages/VerifyOtpPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/verify-otp" element={<VerifyOtpPage />} />

      <Route
        path="/app"
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/app/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="companies" element={<CompaniesPage />} />
        <Route path="plans" element={<PlansPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
