const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000/api";

const ACCESS_TOKEN_KEY = "kwetu_access_token";
const REFRESH_TOKEN_KEY = "kwetu_refresh_token";

function getStoredAccessToken() {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

function getStoredRefreshToken() {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function storeTokens(access, refresh) {
  if (access) {
    localStorage.setItem(ACCESS_TOKEN_KEY, access);
  }
  if (refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh);
  }
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const data = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  if (!response.ok) {
    const message =
      typeof data === "string"
        ? data
        : data.detail ||
          Object.values(data)
            .flat()
            .join(" ") ||
          "Request failed.";
    throw new Error(message);
  }

  return data;
}

async function refreshAccessToken() {
  const refresh = getStoredRefreshToken();
  if (!refresh) {
    throw new Error("No refresh token found.");
  }

  const response = await fetch(`${API_BASE_URL}/auth/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  const data = await parseResponse(response);
  storeTokens(data.access, refresh);
  return data.access;
}

export async function apiRequest(path, options = {}, retry = true) {
  const token = getStoredAccessToken();
  const headers = {
    ...(options.body ? { "Content-Type": "application/json" } : {}),
    ...(options.headers || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (response.status === 401 && retry && getStoredRefreshToken()) {
    try {
      const newAccessToken = await refreshAccessToken();
      return apiRequest(
        path,
        {
          ...options,
          headers: {
            ...(options.headers || {}),
            Authorization: `Bearer ${newAccessToken}`,
          },
        },
        false
      );
    } catch (error) {
      clearTokens();
      throw error;
    }
  }

  return parseResponse(response);
}

export function signup(payload) {
  return apiRequest("/auth/signup/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(payload) {
  const data = await apiRequest("/auth/login/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  storeTokens(data.access, data.refresh);
  return data;
}

export function fetchCurrentUser() {
  return apiRequest("/auth/me/");
}

export function createPatient(payload) {
  return apiRequest("/patients/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchQueue() {
  return apiRequest("/queue/");
}

export function submitTriage(payload) {
  return apiRequest("/triage/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitConsultation(payload) {
  return apiRequest("/consultations/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchPatientDetail(patientId) {
  return apiRequest(`/patients/${patientId}/`);
}

export function submitDispensing(payload) {
  return apiRequest("/pharmacy/dispense/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchPendingUsers() {
  return apiRequest("/auth/pending-users/");
}

export function approveUser(userId) {
  return apiRequest(`/auth/users/${userId}/approve/`, {
    method: "POST",
  });
}

export function rejectUser(userId) {
  return apiRequest(`/auth/users/${userId}/reject/`, {
    method: "DELETE",
  });
}

export function fetchAdminPatients(params = "") {
  return apiRequest(`/admin/patients/${params}`);
}

export function fetchReportSummary() {
  return apiRequest("/admin/reports/summary/");
}

export function fetchStageTiming() {
  return apiRequest("/admin/reports/stage-timing/");
}

export function fetchInventory(params = "") {
  return apiRequest(`/inventory/${params}`);
}

export function createInventory(payload) {
  return apiRequest("/inventory/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function restockInventoryItem(id, amount) {
  return apiRequest(`/inventory/${id}/restock/`, {
    method: "POST",
    body: JSON.stringify({ amount }),
  });
}

export function getReportExportUrl() {
  return `${API_BASE_URL}/admin/reports/export/`;
}

export { API_BASE_URL, getStoredAccessToken };
