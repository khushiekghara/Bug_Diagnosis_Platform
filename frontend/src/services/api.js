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

  // Milestone 4: Defect Pattern Analytics
  getAnalytics: () => request("/analytics/patterns"),

  // Milestone 4: Knowledge base growth -- mark a bug resolved with a
  // confirmed fix so it is added back to the knowledge base.
  resolveBug: (bugId, resolution) =>
    request(`/bugs/${bugId}/resolve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ resolution }),
    }),

  // Milestone 4: knowledge base size / growth stats
  getKnowledgeBaseStats: () => request("/knowledge-base/stats"),
};