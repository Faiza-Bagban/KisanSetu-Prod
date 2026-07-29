// ✅ Base URL
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * ✅ SMART fetchWithAuth
 * - Handles JSON & FormData
 * - Automatically attaches JWT
 * - Handles auth + backend errors
 */
export const fetchWithAuth = async (url, options = {}) => {
  const token = localStorage.getItem("ks_token");
  const isFormData = options.body instanceof FormData;

  const res = await fetch(url, {
    ...options,
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(options.headers || {})
    }
  });

  // 🔐 Auto logout if token expired
  if (res.status === 401) {
    localStorage.clear();
    window.location.href = "/login";
    throw new Error("Session expired");
  }

  // ❌ Backend error handling
  if (!res.ok) {
    let errorMessage = "Request failed";

    try {
      const err = await res.json();
      if (typeof err.detail === "string") {
  errorMessage = err.detail;
} else {
  errorMessage = JSON.stringify(err.detail);
}
    } catch (err) {
      console.error(err);
    }

    throw new Error(errorMessage);
  }

  return res;
};

// ─────────────────────────────────────────
// ✅ IDP Extraction
// ─────────────────────────────────────────
export const extractIDP = async (file) => {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetchWithAuth(`${API_BASE}/api/idp/extract`, {
    method: "POST",
    body: formData
  });

  return res.json();
};

// ─────────────────────────────────────────
// ✅ Eligibility
// ─────────────────────────────────────────
export const checkEligibility = async (payload) => {
  const res = await fetchWithAuth(`${API_BASE}/api/eligibility-ai`, {
    method: "POST",
    body: JSON.stringify(payload)
  });

  return res.json();
};

// ─────────────────────────────────────────
// ✅ Grievance
// ─────────────────────────────────────────
export const submitGrievance = async (text) => {
  const res = await fetchWithAuth(`${API_BASE}/api/grievance`, {
    method: "POST",
    body: JSON.stringify({ text })
  });

  return res.json();
};

// ─────────────────────────────────────────
// ✅ District Risk Map
// ─────────────────────────────────────────
export const fetchDistrictRisks = async () => {
  const res = await fetchWithAuth(`${API_BASE}/admin/admin-dashboard`, {
    method: "GET"
  });

  return res.json();
};

// ─────────────────────────────────────────
// ✅ Audit Logs (ADMIN ONLY)
// ─────────────────────────────────────────
export const fetchAuditLogs = async () => {
  const res = await fetchWithAuth(`${API_BASE}/admin/api/audit-logs`, {
    method: "GET"
  });

  return res.json();
};

export const predictCropRisk = async (payload) => {
  const res = await fetchWithAuth(`${API_BASE}/api/crop-loss`, {
    method: "POST",
    body: JSON.stringify(payload)
  });

  return res.json();
};

export const fetchNDVISummary = async () => {
  const res = await fetchWithAuth(`${API_BASE}/api/ndvi-summary`, {
    method: "GET"
  });
  return res.json();
};

export const askChatbot = async (query) => {
  const res = await fetchWithAuth(`${API_BASE}/api/chatbot`, {
    method: "POST",
    body: JSON.stringify({ query })
  });
  return res.json();
};