import apiClient from "../../services/apiClient";
const data = (request) => request.then((response) => response.data);
export const authApi = {
  signup: (payload) => data(apiClient.post("/auth/signup", payload)),
  login: (payload) => data(apiClient.post("/auth/login", payload)),
  refresh: () => data(apiClient.post("/auth/refresh")),
  me: () => data(apiClient.get("/auth/me")),
  logout: () => apiClient.post("/auth/logout"),
};
