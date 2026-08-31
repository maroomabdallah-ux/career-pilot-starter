import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api/v1",
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

let accessToken = null;
let refreshPromise = null;
let onSessionLost = () => {};

export const configureAuthClient = ({ getToken, setToken, sessionLost }) => {
  accessToken = getToken;
  configureAuthClient.setToken = setToken;
  onSessionLost = sessionLost;
};

apiClient.interceptors.request.use((config) => {
  const token = typeof accessToken === "function" ? accessToken() : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

apiClient.interceptors.response.use(undefined, async (error) => {
  const original = error.config;
  if (error.response?.status !== 401 || original?._retried || original?.url?.includes("/auth/")) throw error;
  original._retried = true;
  try {
    refreshPromise ||= apiClient.post("/auth/refresh").then((response) => {
      configureAuthClient.setToken?.(response.data.access_token, response.data.user);
      return response.data.access_token;
    }).finally(() => { refreshPromise = null; });
    const token = await refreshPromise;
    original.headers.Authorization = `Bearer ${token}`;
    return apiClient(original);
  } catch (refreshError) {
    onSessionLost();
    throw refreshError;
  }
});

export default apiClient;
