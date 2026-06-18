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

export function listBuyerCompanies() {
  return unwrapRequest(providerApi.get("/v1/buyer-companies"));
}

export function createBuyerCompany(payload) {
  return unwrapRequest(providerApi.post("/v1/buyer-companies", payload));
}

export function getBuyerCompany(companyId) {
  return unwrapRequest(providerApi.get(`/v1/buyer-companies/${companyId}`));
}

export function updateBuyerCompany(companyId, payload) {
  return unwrapRequest(providerApi.patch(`/v1/buyer-companies/${companyId}`, payload));
}

export function listProviderCompanies() {
  return unwrapRequest(providerApi.get("/v1/provider-companies"));
}

export function createProviderCompany(payload) {
  return unwrapRequest(providerApi.post("/v1/provider-companies", payload));
}

export function getProviderCompany(companyId) {
  return unwrapRequest(providerApi.get(`/v1/provider-companies/${companyId}`));
}

export function updateProviderCompany(companyId, payload) {
  return unwrapRequest(providerApi.patch(`/v1/provider-companies/${companyId}`, payload));
}

export function activateProviderCompany(companyId) {
  return unwrapRequest(providerApi.post(`/v1/provider-companies/${companyId}/activate`));
}

export function deactivateProviderCompany(companyId) {
  return unwrapRequest(providerApi.post(`/v1/provider-companies/${companyId}/deactivate`));
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
