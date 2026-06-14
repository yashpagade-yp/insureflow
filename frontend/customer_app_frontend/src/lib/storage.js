const SESSION_STORAGE_KEY = "insureflow_main_session";
const PENDING_AUTH_STORAGE_KEY = "insureflow_main_pending_auth";

export function storeSession(session) {
  localStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(session));
}

export function getStoredSession() {
  const rawValue = localStorage.getItem(SESSION_STORAGE_KEY);
  return rawValue ? JSON.parse(rawValue) : null;
}

export function removeStoredSession() {
  localStorage.removeItem(SESSION_STORAGE_KEY);
}

export function storePendingAuth(pendingAuth) {
  localStorage.setItem(PENDING_AUTH_STORAGE_KEY, JSON.stringify(pendingAuth));
}

export function getStoredPendingAuth() {
  const rawValue = localStorage.getItem(PENDING_AUTH_STORAGE_KEY);
  return rawValue ? JSON.parse(rawValue) : null;
}

export function removeStoredPendingAuth() {
  localStorage.removeItem(PENDING_AUTH_STORAGE_KEY);
}
