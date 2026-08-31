import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "./auth.store";

export function ProtectedRoute() {
  const status = useAuthStore((state) => state.status);
  const location = useLocation();
  return status === "authenticated" ? <Outlet/> : <Navigate to="/login" replace state={{ from: location.pathname }}/>;
}

export function OnboardingGuard() {
  const user = useAuthStore((state) => state.user);
  return user?.onboarding_completed ? <Outlet/> : <Navigate to="/onboarding" replace/>;
}
