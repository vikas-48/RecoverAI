const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed: ${res.status}`);
  }

  return res.json();
}

export const api = {
  health: () => request("/health"),
  payments: (limit = 25) => request(`/v1/payments?limit=${limit}`),
  payment: (id) => request(`/v1/payments/${id}`),
  runRecovery: (id) => request(`/v1/recovery/run/${id}`, { method: "POST" }),
  audit: (id) => request(`/v1/recovery/audit?payment_id=${id}`),
  externalRecovery: (id) => request(`/v1/recovery/external/${id}`),
  analytics: () => request("/v1/analytics"),
};
