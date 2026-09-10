import { Link, useLocation } from "react-router-dom";

export default function LegalPage() {
  const privacy = useLocation().pathname.endsWith("privacy");
  return (
    <main className="legal-page">
      <Link to="/">← CareerPilot</Link>
      <h1>{privacy ? "Privacy notice" : "Terms of use"}</h1>
      <p>Last updated: September 10, 2026</p>
      {privacy ? (
        <>
          <h2>Data we process</h2>
          <p>
            CareerPilot processes account, career profile, resume, saved job,
            application and usage data to provide the service.
          </p>
          <h2>AI and external providers</h2>
          <p>
            Only the context needed for a requested feature is sent to
            configured providers. CareerPilot does not submit a job application
            without explicit approval.
          </p>
          <h2>Your choices</h2>
          <p>
            You may edit or delete career data and request account deletion.
            Production contact and retention periods must be configured before
            launch.
          </p>
        </>
      ) : (
        <>
          <h2>Service boundaries</h2>
          <p>
            CareerPilot assists with career materials and external application
            handoff. It does not guarantee employment or independently verify
            external submissions.
          </p>
          <h2>Your responsibilities</h2>
          <p>
            You must provide truthful information, review generated materials,
            and comply with employer and job-board terms.
          </p>
          <h2>Launch requirement</h2>
          <p>
            This operational draft requires legal review and company contact
            details before public launch.
          </p>
        </>
      )}
    </main>
  );
}
