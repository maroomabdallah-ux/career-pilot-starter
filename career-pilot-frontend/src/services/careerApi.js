import apiClient from "./apiClient";

const data = (request) => request.then((response) => response.data);

export const careerApi = {
  getUser: (id) => data(apiClient.get(`/users/${id}`)),
  createUser: (payload) => data(apiClient.post("/users", payload)),
  updateUser: (id, payload) => data(apiClient.patch(`/users/${id}`, payload)),
  getProfileByUser: (id) => data(apiClient.get(`/career-profiles/user/${id}`)),
  createProfile: (payload) => data(apiClient.post("/career-profiles", payload)),
  updateProfile: (id, payload) => data(apiClient.patch(`/career-profiles/${id}`, payload)),
  createChild: (profileId, resource, payload) =>
    data(apiClient.post(`/career-profiles/${profileId}/${resource}`, payload)),
  updateChild: (resource, id, payload) => data(apiClient.patch(`/${resource}/${id}`, payload)),
  deleteChild: (resource, id) => apiClient.delete(`/${resource}/${id}`),
};

export function apiErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (Array.isArray(detail)) return detail[0]?.msg || "Please review the form.";
  return detail || "We couldn’t complete that request. Please try again.";
}
