const SESSION_STORAGE_KEY = "insureflow_main_session";
const PENDING_AUTH_STORAGE_KEY = "insureflow_main_pending_auth";
const JOURNEY_DRAFT_STORAGE_KEY = "insureflow_customer_journey_draft";

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

export function storeJourneyDraft(draft) {
  localStorage.setItem(JOURNEY_DRAFT_STORAGE_KEY, JSON.stringify(draft));
}

export function getStoredJourneyDraft() {
  const rawValue = localStorage.getItem(JOURNEY_DRAFT_STORAGE_KEY);
  return rawValue ? JSON.parse(rawValue) : null;
}

export function removeStoredJourneyDraft() {
  localStorage.removeItem(JOURNEY_DRAFT_STORAGE_KEY);
}
