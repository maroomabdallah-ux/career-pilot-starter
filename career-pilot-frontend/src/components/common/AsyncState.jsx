import { AlertCircle, LoaderCircle } from "lucide-react";
import { apiErrorMessage } from "../../services/careerApi";

export default function AsyncState({ loading, error, children }) {
  if (loading) return <div className="async-state"><LoaderCircle className="spin" size={22} /> Loading your career workspace…</div>;
  if (error) return <div className="async-state error"><AlertCircle size={22} /><div><strong>We couldn’t load this section.</strong><p>{apiErrorMessage(error)}</p></div></div>;
  return children;
}
