import { useEffect } from "react";
import { authApi } from "./auth.api";
import { useAuthStore } from "./auth.store";
import { configureAuthClient } from "../../services/apiClient";

configureAuthClient({
  getToken: () => useAuthStore.getState().accessToken,
  setToken: (token, user) => useAuthStore.getState().setSession(token, user),
  sessionLost: () => useAuthStore.getState().clearSession(),
});

export default function AuthBootstrap({ children }) {
  const status = useAuthStore((state) => state.status);
  useEffect(() => {
    authApi.refresh().then(({ access_token, user }) => useAuthStore.getState().setSession(access_token, user)).catch(() => useAuthStore.getState().clearSession());
  }, []);
  if (status === "loading") return <div className="auth-loading"><img src="/careerpilot-logo.png" alt="CareerPilot"/><span className="skeleton-line"/></div>;
  return children;
}
