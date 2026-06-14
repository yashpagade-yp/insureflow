import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  adminLogin,
  adminVerifyOtp,
  customerLoginOtp,
  customerVerifyOtp,
  setAccessToken,
} from "../lib/api";
import {
  getStoredPendingAuth,
  getStoredSession,
  removeStoredPendingAuth,
  removeStoredSession,
  storePendingAuth,
  storeSession,
} from "../lib/storage";

const SessionContext = createContext(null);

export function SessionProvider({ children }) {
  const navigate = useNavigate();
  const [session, setSession] = useState(() => getStoredSession());
  const [pendingAuth, setPendingAuth] = useState(() => getStoredPendingAuth());

  useEffect(() => {
    setAccessToken(session?.accessToken ?? null);
  }, [session]);

  const startCustomerLogin = async (payload) => {
    const response = await customerLoginOtp(payload);
    const nextPendingAuth = {
      role: "USER",
      mobileNumber: response.mobile_number,
      otpExpiresAt: response.otp_expires_at,
    };

    setPendingAuth(nextPendingAuth);
    storePendingAuth(nextPendingAuth);
    navigate("/customer/verify");
    return response;
  };

  const verifyCustomerLogin = async (payload) => {
    const response = await customerVerifyOtp(payload);
    const nextSession = {
      role: "USER",
      accessToken: response.access_token,
      tokenType: response.token_type,
      userId: response.user_id,
      mobileNumber: response.mobile_number,
    };

    setSession(nextSession);
    storeSession(nextSession);
    removeStoredPendingAuth();
    setPendingAuth(null);
    setAccessToken(response.access_token);
    navigate("/customer/app/dashboard");
    return response;
  };

  const startAdminLogin = async (payload) => {
    const response = await adminLogin(payload);
    const nextPendingAuth = {
      role: "ADMIN",
      email: response.email,
      otpExpiresAt: response.otp_expires_at,
    };

    setPendingAuth(nextPendingAuth);
    storePendingAuth(nextPendingAuth);
    navigate("/admin/verify");
    return response;
  };

  const verifyAdminLogin = async (payload) => {
    const response = await adminVerifyOtp(payload);
    const nextSession = {
      role: "ADMIN",
      accessToken: response.access_token,
      tokenType: response.token_type,
      adminId: response.admin_id,
      email: response.email,
    };

    setSession(nextSession);
    storeSession(nextSession);
    removeStoredPendingAuth();
    setPendingAuth(null);
    setAccessToken(response.access_token);
    navigate("/admin/app/dashboard");
    return response;
  };

  const logout = () => {
    setSession(null);
    setPendingAuth(null);
    removeStoredSession();
    removeStoredPendingAuth();
    setAccessToken(null);
    navigate("/");
  };

  const value = useMemo(
    () => ({
      session,
      pendingAuth,
      isAuthenticated: Boolean(session?.accessToken),
      startCustomerLogin,
      verifyCustomerLogin,
      startAdminLogin,
      verifyAdminLogin,
      logout,
    }),
    [pendingAuth, session]
  );

  return (
    <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
  );
}

export function useSession() {
  const context = useContext(SessionContext);

  if (!context) {
    throw new Error("useSession must be used within a SessionProvider");
  }

  return context;
}
