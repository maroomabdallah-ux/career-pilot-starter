import axios, { AxiosHeaders } from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env?.VITE_API_BASE_URL || "/api/v1",
  timeout: 20000,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

let accessToken = null;
let refreshPromise = null;
let onSessionLost = () => {};

const isRegenerateSectionRequest = (config) =>
  config?.url?.includes("/resumes/") &&
  config.url.endsWith("/regenerate-section");

const safeRegeneratePayload = (data) => {
  try {
    const payload = typeof data === "string" ? JSON.parse(data) : data;
    return { section: payload?.section ?? null };
  } catch {
    return { section: null, malformed_json: true };
  }
};

const logRegenerateRetry = (phase, config) => {
  if (!import.meta.env?.DEV || !isRegenerateSectionRequest(config)) return;
  console.debug("Resume regenerate-section auth retry", {
    phase,
    method: config.method,
    url: config.url,
    payload: safeRegeneratePayload(config.data),
    content_type: AxiosHeaders.from(config.headers).get("Content-Type"),
  });
};

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
  // Axios has already serialized a JSON request by this point. Keep that exact
  // body for the retry instead of rebuilding it after the asynchronous refresh.
  const originalData = original.data;
  const originalHeaders = AxiosHeaders.from(original.headers);
  logRegenerateRetry("original", original);
  try {
    refreshPromise ||= apiClient.post("/auth/refresh").then((response) => {
      configureAuthClient.setToken?.(response.data.access_token, response.data.user);
      return response.data.access_token;
    }).finally(() => { refreshPromise = null; });
    const token = await refreshPromise;
    const retry = {
      ...original,
      _retried: true,
      data: originalData,
      headers: AxiosHeaders.from(originalHeaders),
    };
    retry.headers.set("Authorization", `Bearer ${token}`);
    logRegenerateRetry("retry", retry);
    return apiClient(retry);
  } catch (refreshError) {
    onSessionLost();
    throw refreshError;
  }
});

export default apiClient;
