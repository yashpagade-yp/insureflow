import axios from "axios";

const providerApi = axios.create({
  baseURL:
    import.meta.env.VITE_PROVIDER_API_BASE_URL ?? "http://127.0.0.1:8001",
  headers: {
    "Content-Type": "application/json",
  },
});

let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

providerApi.interceptors.request.use((config) => {
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

export function providerAdminLogin(payload) {
  return unwrapRequest(providerApi.post("/v1/provider-auth/login", payload));
}

export function providerAdminVerifyOtp(payload) {
  return unwrapRequest(providerApi.post("/v1/provider-auth/verify-otp", payload));
}

export function listCompanies() {
  return unwrapRequest(providerApi.get("/v1/companies"));
}

export function createCompany(payload) {
  return unwrapRequest(providerApi.post("/v1/companies", payload));
}

export function getCompany(companyId) {
  return unwrapRequest(providerApi.get(`/v1/companies/${companyId}`));
}

export function updateCompany(companyId, payload) {
  return unwrapRequest(providerApi.patch(`/v1/companies/${companyId}`, payload));
}

export function listPlans() {
  return unwrapRequest(providerApi.get("/v1/plans"));
}

export function createPlan(payload) {
  return unwrapRequest(providerApi.post("/v1/plans", payload));
}

export function getPlan(planCode) {
  return unwrapRequest(providerApi.get(`/v1/plans/${planCode}`));
}

export function updatePlan(planCode, payload) {
  return unwrapRequest(providerApi.patch(`/v1/plans/${planCode}`, payload));
}

export function listQuotes() {
  return unwrapRequest(providerApi.get("/v1/quotes"));
}

export function getAdminQuote(transactionId) {
  return unwrapRequest(providerApi.get(`/v1/quotes/admin/${transactionId}`));
}

export function listPayments() {
  return unwrapRequest(providerApi.get("/v1/payments"));
}

export function getAdminPayment(paymentReference) {
  return unwrapRequest(
    providerApi.get(`/v1/payments/admin/${paymentReference}`)
  );
}

export default providerApi;
