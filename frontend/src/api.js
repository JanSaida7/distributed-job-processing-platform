const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, { token, ...options } = {}) {
  const headers = new Headers(options.headers);
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });
  const body = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    throw new ApiError(body?.error?.message || body?.detail || "Request failed.", response.status);
  }
  return body;
}

export const api = {
  register: (data) => request("/api/v1/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data) => request("/api/v1/auth/login", { method: "POST", body: JSON.stringify(data) }),
  listJobs: (token) => request("/api/v1/jobs", { token }),
  listFailedJobs: (token) => request("/api/v1/jobs/failed", { token }),
  listDeadLetterJobs: (token) => request("/api/v1/jobs/dead-letter", { token }),
  createJob: (data, token) => request("/api/v1/jobs", { method: "POST", body: JSON.stringify(data), token }),
  cancelJob: (id, token) => request(`/api/v1/jobs/${id}/cancel`, { method: "POST", token }),
  retryJob: (id, token) => request(`/api/v1/jobs/${id}/retry`, { method: "POST", token }),
};
