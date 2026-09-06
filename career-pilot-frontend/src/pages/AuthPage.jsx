import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, LoaderCircle } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { z } from "zod";
import { authApi } from "../features/auth/auth.api";
import { useAuthStore } from "../features/auth/auth.store";
import { apiErrorMessage } from "../services/careerApi";
const password = z
  .string()
  .min(8, "Use at least 8 characters")
  .regex(/[A-Za-z]/, "Include a letter")
  .regex(/\d/, "Include a number");
const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});
const signupSchema = z
  .object({
    first_name: z.string().min(1, "First name is required"),
    last_name: z.string().min(1, "Last name is required"),
    email: z.string().email("Enter a valid email"),
    password,
    confirm_password: z.string(),
  })
  .refine((v) => v.password === v.confirm_password, {
    path: ["confirm_password"],
    message: "Passwords do not match",
  });
export default function AuthPage({ mode }) {
  const signup = mode === "signup";
  const admin = mode === "admin";
  const status = useAuthStore((s) => s.status);
  const currentUser = useAuthStore((s) => s.user);
  const [visible, setVisible] = useState(false);
  const [serverError, setServerError] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(signup ? signupSchema : loginSchema) });
  if (status === "authenticated" && (!admin || currentUser?.is_admin))
    return (
      <Navigate
        to={
          admin
            ? "/app/admin/ai-usage"
            : useAuthStore.getState().user?.onboarding_completed
              ? "/app/dashboard"
              : "/onboarding"
        }
        replace
      />
    );
  const submit = async (values) => {
    setServerError("");
    try {
      const payload = { ...values };
      delete payload.confirm_password;
      const result = await (signup
        ? authApi.signup(payload)
        : authApi.login(payload));
      if (admin && !result.user.is_admin) {
        await authApi.logout();
        useAuthStore.getState().clearSession();
        setServerError("This account does not have administrator access.");
        return;
      }
      useAuthStore.getState().setSession(result.access_token, result.user);
      navigate(
        admin
          ? "/app/admin/ai-usage"
          : result.user.onboarding_completed
            ? location.state?.from || "/app/dashboard"
            : "/onboarding",
        { replace: true },
      );
    } catch (error) {
      setServerError(
        error.response?.status === 401
          ? "Invalid email or password"
          : apiErrorMessage(error),
      );
    }
  };
  return (
    <main className="auth-page">
      <section className="auth-card">
        <span className="section-eyebrow">
          {signup
            ? "Create your workspace"
            : admin
              ? "Restricted access"
              : "Welcome back"}
        </span>
        <h1>
          {signup
            ? "Start building your career foundation."
            : admin
              ? "CareerPilot administration."
              : "Continue your career journey."}
        </h1>
        <p>
          {signup
            ? "A focused workspace for your professional story and next move."
            : admin
              ? "Sign in with an authorized administrator account."
              : "Sign in to return to your CareerPilot workspace."}
        </p>
        {admin && status === "authenticated" && !currentUser?.is_admin && (
          <div className="admin-access-notice">
            <p>Your current account is not an administrator.</p>
            <button
              className="button secondary full"
              onClick={async () => {
                await authApi.logout();
                useAuthStore.getState().clearSession();
              }}
            >
              Sign out and use an admin account
            </button>
          </div>
        )}
        {(!admin || status !== "authenticated") && (
          <form onSubmit={handleSubmit(submit)}>
            {signup && (
              <div className="form-grid">
                <label>
                  <span>First name</span>
                  <input autoFocus {...register("first_name")} />
                  <small className="field-error">
                    {errors.first_name?.message}
                  </small>
                </label>
                <label>
                  <span>Last name</span>
                  <input {...register("last_name")} />
                  <small className="field-error">
                    {errors.last_name?.message}
                  </small>
                </label>
              </div>
            )}
            <label>
              <span>Email</span>
              <input
                type="email"
                autoFocus={!signup}
                autoComplete="email"
                {...register("email")}
              />
              <small className="field-error">{errors.email?.message}</small>
            </label>
            <label>
              <span>Password</span>
              <div className="password-input">
                <input
                  type={visible ? "text" : "password"}
                  autoComplete={signup ? "new-password" : "current-password"}
                  {...register("password")}
                />
                <button
                  type="button"
                  onClick={() => setVisible(!visible)}
                  aria-label="Toggle password visibility"
                >
                  {visible ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              <small className="field-error">{errors.password?.message}</small>
            </label>
            {signup && (
              <label>
                <span>Confirm password</span>
                <input
                  type={visible ? "text" : "password"}
                  autoComplete="new-password"
                  {...register("confirm_password")}
                />
                <small className="field-error">
                  {errors.confirm_password?.message}
                </small>
              </label>
            )}
            {serverError && <p className="form-error">{serverError}</p>}
            <button
              type="submit"
              className="button primary full"
              disabled={isSubmitting}
            >
              {isSubmitting && <LoaderCircle className="spin" size={17} />}{" "}
              {signup
                ? "Create account"
                : admin
                  ? "Sign in as admin"
                  : "Sign in"}
            </button>
          </form>
        )}
        {!admin && (
          <p className="auth-switch">
            {signup ? "Already have an account?" : "New to CareerPilot?"}{" "}
            <Link to={signup ? "/login" : "/signup"}>
              {signup ? "Sign in" : "Create account"}
            </Link>
          </p>
        )}
        <p className="auth-switch">
          {admin ? "Not an administrator?" : "Administrator?"}{" "}
          <Link to={admin ? "/login" : "/admin/login"}>
            {admin ? "User sign in" : "Admin sign in"}
          </Link>
        </p>
      </section>
    </main>
  );
}
