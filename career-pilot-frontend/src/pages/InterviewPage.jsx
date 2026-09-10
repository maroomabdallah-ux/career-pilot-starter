import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { MessageSquareText, Star } from "lucide-react";
import { apiErrorMessage, careerApi } from "../services/careerApi";
import "../features/jobs/workspace.css";

export default function InterviewPage() {
  const [params] = useSearchParams();
  const applicationId = params.get("application");
  const [kit, setKit] = useState(null);
  const [answers, setAnswers] = useState(() => {
    try {
      return (
        JSON.parse(localStorage.getItem(`interview:${applicationId}`)) || {}
      );
    } catch {
      return {};
    }
  });
  const [error, setError] = useState("");
  useEffect(() => {
    if (applicationId)
      careerApi
        .getInterviewKit(applicationId)
        .then(setKit)
        .catch((e) => setError(apiErrorMessage(e)));
  }, [applicationId]);
  const update = (index, value) => {
    const next = { ...answers, [index]: value };
    setAnswers(next);
    localStorage.setItem(`interview:${applicationId}`, JSON.stringify(next));
  };
  if (!applicationId)
    return (
      <main className="page cp-workspace">
        <div className="cp-empty">
          <MessageSquareText />
          <h2>Choose an application first</h2>
          <p>Interview preparation is grounded in a saved job.</p>
          <Link className="button primary" to="/app/applications">
            Open applications
          </Link>
        </div>
      </main>
    );
  return (
    <main className="page cp-workspace">
      <header className="cp-page-header">
        <div>
          <span className="cp-eyebrow">
            <MessageSquareText size={14} /> INTERVIEW PREP
          </span>
          <h1>
            Practice with evidence<span>.</span>
          </h1>
          <p>Draft STAR answers using only facts you can support.</p>
        </div>
        <Link
          className="button secondary"
          to={`/app/applications/${applicationId}`}
        >
          Back to application
        </Link>
      </header>
      {error && <div className="cp-notice cp-error">{error}</div>}
      {!kit ? (
        <div className="cp-loading">Building your interview kit…</div>
      ) : (
        <section className="cp-interview-kit">
          <div className="cp-notice">{kit.grounding_note}</div>
          <h2>Practice questions</h2>
          {kit.questions.map((question, index) => (
            <label key={question}>
              <strong>
                {index + 1}. {question}
              </strong>
              <textarea
                rows={6}
                value={answers[index] || ""}
                onChange={(e) => update(index, e.target.value)}
                placeholder="Use Situation, Task, Action, Result…"
              />
            </label>
          ))}
          <h2>
            <Star size={18} /> STAR checklist
          </h2>
          <ul>
            {kit.star_prompts.map((x) => (
              <li key={x}>{x}</li>
            ))}
          </ul>
          <h2>Technical preparation</h2>
          <div className="cp-skill-chips">
            {kit.technical_topics.map((x) => (
              <span key={x}>{x}</span>
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
