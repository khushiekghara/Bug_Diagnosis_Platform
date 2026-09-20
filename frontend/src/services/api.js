export const API_BASE =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE}${endpoint}`, options);

  let data = null;
  try {
    data = await response.json();
  } catch {
    data = null;
  }

  if (!response.ok) {
    throw new Error(data?.detail || `Request failed with ${response.status}`);
  }

  return data;
}

export const api = {
  health: () => request("/"),
  getBugs: () => request("/bugs"),
  getBug: (bugId) => request(`/bugs/${bugId}`),
  getDiagnosis: (bugId) => request(`/bugs/${bugId}/diagnosis`),

  submitPaste: (payload) =>
    request("/bugs/paste", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }),

  uploadBug: (title, file) => {
    const formData = new FormData();
    formData.append("title", title);
    formData.append("file", file);

    return request("/bugs/upload", {
      method: "POST",
      body: formData,
    });
  },

  rerunDiagnosis: (bugId) =>
    request(`/bugs/${bugId}/diagnose`, {
      method: "POST",
    }),
};