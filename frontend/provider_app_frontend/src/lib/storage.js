const AUTH_STORAGE_KEY = "insureflow_provider_auth";
const PENDING_LOGIN_STORAGE_KEY = "insureflow_provider_pending_login";

export function storeAuth(auth) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
}

export function getStoredAuth() {
  const rawValue = localStorage.getItem(AUTH_STORAGE_KEY);
  return rawValue ? JSON.parse(rawValue) : null;
}

export function removeStoredAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

export function storePendingLogin(pendingLogin) {
  localStorage.setItem(
    PENDING_LOGIN_STORAGE_KEY,
    JSON.stringify(pendingLogin)
  );
}

export function getStoredPendingLogin() {
  const rawValue = localStorage.getItem(PENDING_LOGIN_STORAGE_KEY);
  return rawValue ? JSON.parse(rawValue) : null;
}

export function removeStoredPendingLogin() {
  localStorage.removeItem(PENDING_LOGIN_STORAGE_KEY);
}
