import apiClient from "./apiClient";

const data = (request) => request.then((response) => response.data);

export const careerApi = {
  getProfile: () => data(apiClient.get("/me/profile")),
  createProfile: (payload) => data(apiClient.post("/me/profile", payload)),
  updateProfile: (payload) => data(apiClient.patch("/me/profile", payload)),
  completeOnboarding: () => data(apiClient.post("/me/onboarding/complete")),
  createChild: (resource, payload) =>
    data(apiClient.post(`/me/${resource}`, payload)),
  updateChild: (resource, id, payload) =>
    data(apiClient.patch(`/me/${resource}/${id}`, payload)),
  deleteChild: (resource, id) => apiClient.delete(`/me/${resource}/${id}`),
  profileAgentChat: (payload) =>
    data(apiClient.post("/ai/profile/chat", payload)),
  profileAgentApprove: (payload) =>
    data(apiClient.post("/ai/profile/approve", payload)),
  listResumes: () => data(apiClient.get("/resumes")),
  generateResume: (payload) =>
    data(apiClient.post("/resumes/generate", payload)),
  approveResume: (id) => data(apiClient.post(`/resumes/${id}/approve`)),
  reviewResume: (id) => data(apiClient.post(`/resumes/${id}/review`)),
  updateResume: (id, payload) =>
    data(apiClient.patch(`/resumes/${id}`, payload)),
  regenerateResumeSection: (id, section) =>
    data(apiClient.post(`/resumes/${id}/regenerate-section`, { section })),
};

export function apiErrorMessage(error) {
  if (!error?.response) {
    return "CareerPilot could not reach the API. Make sure the backend is running on port 8000.";
  }
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) return detail[0]?.msg || "Please review the form.";
  return detail || "We couldn’t complete that request. Please try again.";
}
