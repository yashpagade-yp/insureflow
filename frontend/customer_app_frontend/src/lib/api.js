import axios from "axios";

const mainApi = axios.create({
  baseURL: import.meta.env.VITE_MAIN_API_BASE_URL ?? "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

mainApi.interceptors.request.use((config) => {
  const nextConfig = { ...config };

  if (accessToken) {
    nextConfig.headers = {
      ...nextConfig.headers,
      Authorization: `Bearer ${accessToken}`,
    };
  }

  return nextConfig;
});

function extractError(error) {
  if (error.response?.data?.detail) {
    return typeof error.response.data.detail === "string"
      ? error.response.data.detail
      : "Request failed.";
  }

  return error.message || "Unexpected request failure.";
}

async function unwrapRequest(requestPromise) {
  try {
    const response = await requestPromise;
    return response.data;
  } catch (error) {
    throw new Error(extractError(error));
  }
}

export function createJourney(payload) {
  return unwrapRequest(mainApi.post("/v1/insurance-details", payload));
}

export function updateJourney(transactionId, payload) {
  return unwrapRequest(
    mainApi.patch(`/v1/insurance-details/${transactionId}`, payload)
  );
}

export function customerLoginOtp(payload) {
  return unwrapRequest(mainApi.post("/v1/users/login-otp", payload));
}

export function customerVerifyOtp(payload) {
  return unwrapRequest(mainApi.post("/v1/users/login-otp/verify", payload));
}

export function adminLogin(payload) {
  return unwrapRequest(mainApi.post("/v1/admins/login", payload));
}

export function adminVerifyOtp(payload) {
  return unwrapRequest(mainApi.post("/v1/admins/login/verify", payload));
}

export function getLatestIncompleteJourney(mobileNumber) {
  return unwrapRequest(
    mainApi.get(`/v1/users/${mobileNumber}/latest-incomplete-journey`)
  );
}

export function getQuotes(transactionId) {
  return unwrapRequest(mainApi.get(`/v1/quotes/${transactionId}`));
}

export function selectPlan(payload) {
  return unwrapRequest(mainApi.patch("/v1/transactions/select-plan", payload));
}

export function selectAddOns(payload) {
  return unwrapRequest(
    mainApi.patch("/v1/transactions/select-add-ons", payload)
  );
}

export function getTransaction(transactionId) {
  return unwrapRequest(mainApi.get(`/v1/transactions/${transactionId}`));
}

export function listUserTransactions(userId) {
  return unwrapRequest(mainApi.get(`/v1/users/${userId}/transactions`));
}

export function createPayment(payload) {
  return unwrapRequest(mainApi.post("/v1/payments", payload));
}

export function sendPaymentOtp(paymentReference) {
  return unwrapRequest(
    mainApi.post(`/v1/payments/${paymentReference}/send-otp`)
  );
}

export function verifyPaymentOtp(payload) {
  return unwrapRequest(mainApi.post("/v1/payments/verify-otp", payload));
}

export function getPaymentStatus(paymentReference) {
  return unwrapRequest(
    mainApi.get(`/v1/payments/${paymentReference}/status`)
  );
}

export function listUserPolicies(userId) {
  return unwrapRequest(mainApi.get(`/v1/users/${userId}/policies`));
}

export function getPolicy(policyNumber) {
  return unwrapRequest(mainApi.get(`/v1/policies/${policyNumber}`));
}

export function issuePolicy(payload) {
  return unwrapRequest(mainApi.post("/v1/policies/issue", payload));
}

export function attachPolicyPdf(policyNumber, payload) {
  return unwrapRequest(
    mainApi.patch(`/v1/policies/${policyNumber}/pdf`, payload)
  );
}

export function getUserProfile(userId) {
  return unwrapRequest(mainApi.get(`/v1/users/${userId}`));
}

export function createTicket(userId, payload) {
  return unwrapRequest(mainApi.post(`/v1/users/${userId}/tickets`, payload));
}

export function listUserTickets(userId) {
  return unwrapRequest(mainApi.get(`/v1/users/${userId}/tickets`));
}

export function updateUserTicket(userId, ticketId, payload) {
  return unwrapRequest(
    mainApi.patch(`/v1/users/${userId}/tickets/${ticketId}`, payload)
  );
}

export function listAdminUsers() {
  return unwrapRequest(mainApi.get("/v1/admins/users"));
}

export function listAdminTransactions() {
  return unwrapRequest(mainApi.get("/v1/admins/transactions"));
}

export function listAdminPendingForms() {
  return unwrapRequest(mainApi.get("/v1/admins/transactions/pending-forms"));
}

export function listAdminCompletedJourneys() {
  return unwrapRequest(
    mainApi.get("/v1/admins/transactions/completed-journeys")
  );
}

export function listAdminPolicies() {
  return unwrapRequest(mainApi.get("/v1/admins/policies"));
}

export function listAdminTickets() {
  return unwrapRequest(mainApi.get("/v1/admins/tickets"));
}

export function respondToAdminTicket(ticketId, payload) {
  return unwrapRequest(mainApi.patch(`/v1/admins/tickets/${ticketId}`, payload));
}

export function getCallingBotConfig() {
  return unwrapRequest(mainApi.get("/v1/admins/calling-bot/config"));
}

export function listCallingBotCalls() {
  return unwrapRequest(mainApi.get("/v1/admins/calling-bot/calls"));
}

export function getCallingBotCall(callReference) {
  return unwrapRequest(mainApi.get(`/v1/admins/calling-bot/calls/${callReference}`));
}

export function startCallingBotCall(payload) {
  return unwrapRequest(mainApi.post("/v1/admins/calling-bot/calls", payload));
}

export function prepareCallingBotPurchase(callReference, payload) {
  return unwrapRequest(
    mainApi.post(
      `/v1/admins/calling-bot/calls/${callReference}/prepare-purchase`,
      payload
    )
  );
}

export function completeCallingBotPurchase(callReference, payload) {
  return unwrapRequest(
    mainApi.post(
      `/v1/admins/calling-bot/calls/${callReference}/complete-purchase`,
      payload
    )
  );
}

export default mainApi;
