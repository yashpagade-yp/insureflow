import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  getStoredAuth,
  getStoredPendingLogin,
  removeStoredAuth,
  removeStoredPendingLogin,
  storeAuth,
  storePendingLogin,
} from "../lib/storage";
import {
  providerAdminLogin,
  providerAdminVerifyOtp,
  setAccessToken,
} from "../lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const navigate = useNavigate();
  const [auth, setAuth] = useState(() => getStoredAuth());
  const [pendingLogin, setPendingLogin] = useState(() => getStoredPendingLogin());

  useEffect(() => {
    setAccessToken(auth?.accessToken ?? null);
  }, [auth]);

  const startLogin = async (payload) => {
    const response = await providerAdminLogin(payload);
    const nextPendingLogin = {
      email: response.email,
      otpExpiresAt: response.otp_expires_at,
    };

    setPendingLogin(nextPendingLogin);
    storePendingLogin(nextPendingLogin);
    navigate("/verify-otp");
    return response;
  };

  const verifyOtp = async (payload) => {
    const response = await providerAdminVerifyOtp(payload);
    const nextAuth = {
      accessToken: response.access_token,
      tokenType: response.token_type,
      adminId: response.admin_id,
      email: response.email,
    };

    setAuth(nextAuth);
    storeAuth(nextAuth);
    removeStoredPendingLogin();
    setPendingLogin(null);
    setAccessToken(response.access_token);
    navigate("/app/dashboard");
    return response;
  };

  const logout = () => {
    setAuth(null);
    setPendingLogin(null);
    removeStoredAuth();
    removeStoredPendingLogin();
    setAccessToken(null);
    navigate("/login");
  };

  const value = useMemo(
    () => ({
      auth,
      pendingLogin,
      isAuthenticated: Boolean(auth?.accessToken),
      startLogin,
      verifyOtp,
      logout,
    }),
    [auth, pendingLogin]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}
