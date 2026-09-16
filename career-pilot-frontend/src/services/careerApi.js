import apiClient from "./apiClient";

const data = (request) => request.then((response) => response.data);
const AI_REQUEST_TIMEOUT = 180000;

async function profileChat(payload) {
  // A replay must carry the same body and key to retrieve the original result.
  const body = JSON.stringify(payload);
  const headers = { "Idempotency-Key": crypto.randomUUID() };
  const deadline = Date.now() + AI_REQUEST_TIMEOUT;
  while (true) {
    try {
      return await data(apiClient.post("/ai/profile/chat", body, {
        headers,
        timeout: Math.max(1, deadline - Date.now()),
        _transportRetried: true,
      }));
    } catch (error) {
      const processing = error.response?.status === 409 &&
        error.response?.data?.detail?.request_id &&
        error.response?.headers?.["retry-after"];
      if (!processing) throw error;
      const delay = Math.min(10000, Math.max(1000,
        (Number(error.response.headers["retry-after"]) || 3) * 1000));
      if (Date.now() + delay >= deadline) {
        error.response.data = {
          detail: "Your request is still processing. Its result could not be retrieved yet.",
        };
        throw error;
      }
      await new Promise((resolve) => setTimeout(resolve, delay));
    }
  }
}

export const careerApi = {
  getProfile: () => data(apiClient.get("/me/profile")),
  createProfile: (payload) => data(apiClient.post("/me/profile", payload)),
  updateProfile: (payload) => data(apiClient.patch("/me/profile", payload)),
  completeOnboarding: () => data(apiClient.post("/me/onboarding/complete")),
  reviewOnboardingCv: (file) => {
    const form = new FormData();
    form.append("file", file);
    return data(apiClient.post("/me/onboarding/cv/review", form));
  },
  confirmOnboardingCv: (review) =>
    data(apiClient.post("/me/onboarding/cv/confirm", { review })),
  listEducation: () => data(apiClient.get("/me/education")),
  listSkills: () => data(apiClient.get("/me/skills")),
  listExperiences: () => data(apiClient.get("/me/experiences")),
  createChild: (resource, payload) =>
    data(apiClient.post(`/me/${resource}`, payload)),
  updateChild: (resource, id, payload) =>
    data(apiClient.patch(`/me/${resource}/${id}`, payload)),
  deleteChild: (resource, id) => apiClient.delete(`/me/${resource}/${id}`),
  profileAgentChat: profileChat,
  profileAgentApprove: (payload) =>
    data(apiClient.post("/ai/profile/approve", payload)),
  listResumes: () => data(apiClient.get("/resumes")),
  getResumeReadiness: () => data(apiClient.get("/resumes/readiness")),
  generateResume: (payload) =>
    data(
      apiClient.post("/resumes/generate", payload, {
        timeout: AI_REQUEST_TIMEOUT,
      }),
    ),
  approveResume: (id) => data(apiClient.post(`/resumes/${id}/approve`)),
  reviewResume: (id) => data(apiClient.post(`/resumes/${id}/review`)),
  updateResume: (id, payload) =>
    data(apiClient.patch(`/resumes/${id}`, payload)),
  duplicateResume: (id) => data(apiClient.post(`/resumes/${id}/duplicate`)),
  deleteResume: (id) => apiClient.delete(`/resumes/${id}`),
  regenerateResumeSection: (id, section) =>
    data(
      apiClient.post(
        `/resumes/${id}/regenerate-section`,
        { section },
        { timeout: AI_REQUEST_TIMEOUT },
      ),
    ),
  analyzeResume: (id) => data(apiClient.get(`/resumes/${id}/analysis`)),
  coachResume: (id, payload) =>
    data(
      apiClient.post(`/resumes/${id}/copilot`, payload, {
        timeout: AI_REQUEST_TIMEOUT,
      }),
    ),
  applyResumeSuggestion: (id, payload) =>
    data(apiClient.post(`/resumes/${id}/suggestions/apply`, payload)),
  exportResume: (id) =>
    apiClient.post(`/resumes/${id}/export`, null, { responseType: "blob" }),
  searchJobs: (payload) => data(apiClient.post("/jobs/search", payload)),
  searchJobsPage: (params, signal) =>
    data(apiClient.get("/jobs/search", { params, signal, timeout: 90000 })),
  listApplications: () => data(apiClient.get("/applications")),
  getApplication: (id) => data(apiClient.get(`/applications/${id}`)),
  createApplication: (job) => data(apiClient.post("/applications", { job })),
  tailorApplication: (id, payload) =>
    data(apiClient.post(`/applications/${id}/tailor`, payload)),
  generateApplication: (id, payload) =>
    data(apiClient.post(`/applications/${id}/generate`, payload)),
  getInterviewKit: (id) =>
    data(apiClient.get(`/applications/${id}/interview-kit`)),
  prepareApplication: (id, payload) =>
    data(apiClient.post(`/applications/${id}/prepare`, payload)),
  approveApplication: (id, payload) =>
    data(apiClient.post(`/applications/${id}/approve`, payload)),
  trackApplication: (id, payload) =>
    data(apiClient.post(`/applications/${id}/track`, payload)),
  listSavedJobs: () => data(apiClient.get("/jobs/saved")),
  saveJob: (job) => data(apiClient.post("/jobs/saved", { job })),
  unsaveJob: (id) => apiClient.delete(`/jobs/saved/${id}`),
  getJobSearchHistory: () => data(apiClient.get("/jobs/search-history")),
  validateJobLink: (job) => data(apiClient.post("/jobs/validate-link", job)),
  getAIUsageSummary: (params) =>
    data(apiClient.get("/admin/usage/summary", { params })),
  getAIUsageDaily: (params) =>
    data(apiClient.get("/admin/usage/daily", { params })),
  getAIUsageBreakdown: (group, params) =>
    data(apiClient.get(`/admin/usage/by-${group}`, { params })),
};

export function apiErrorMessage(error) {
  if (error?.code === "ECONNABORTED") {
    return "CareerPilot is taking longer than expected to generate your content. Please try again.";
  }
  if (!error?.response) {
    return "CareerPilot could not reach the API. Make sure the backend is running on port 8000.";
  }
  const detail = error?.response?.data?.detail;
  if (error?.response?.data?.error?.message)
    return error.response.data.error.message;
  if (Array.isArray(detail)) return detail[0]?.msg || "Please review the form.";
  if (detail?.error?.message) return detail.error.message;
  if (detail?.message) return detail.message;
  return detail || "We couldn’t complete that request. Please try again.";
}
