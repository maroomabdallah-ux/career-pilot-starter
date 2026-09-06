import { Navigate, Route, Routes } from "react-router-dom";
import {
  AdminRoute,
  OnboardingGuard,
  ProtectedRoute,
} from "../features/auth/ProtectedRoute";
import AppLayout from "../layouts/AppLayout";
import PublicLayout from "../layouts/PublicLayout";
import AuthPage from "../pages/AuthPage";
import AdminAIUsagePage from "../pages/AdminAIUsagePage";
import DashboardPage from "../pages/DashboardPage";
import LandingPage from "../pages/LandingPage";
import JobsPage from "../pages/JobsPage";
import OnboardingPage from "../pages/OnboardingPage";
import PlaceholderPage from "../pages/PlaceholderPage";
import ProfilePage from "../pages/ProfilePage";
import ResumePage from "../pages/ResumePage";
import ResumeHomePage from "../pages/ResumeHomePage";
import ResumeTemplatesPage from "../pages/ResumeTemplatesPage";
import SettingsPage from "../pages/SettingsPage";

export default function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/signup" element={<AuthPage mode="signup" />} />
        <Route path="/admin/login" element={<AuthPage mode="admin" />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route path="/onboarding" element={<OnboardingPage />} />
        <Route element={<OnboardingGuard />}>
          <Route path="/app" element={<AppLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="profile/:section" element={<ProfilePage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="resume" element={<ResumeHomePage />} />
            <Route path="resume/templates" element={<ResumeTemplatesPage />} />
            <Route path="resume/:resumeId/edit" element={<ResumePage />} />
            <Route path="jobs" element={<JobsPage />} />
            <Route element={<AdminRoute />}>
              <Route path="admin/ai-usage" element={<AdminAIUsagePage />} />
            </Route>
            {["applications", "interview", "roadmap", "billing"].map((path) => (
              <Route key={path} path={path} element={<PlaceholderPage />} />
            ))}
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
