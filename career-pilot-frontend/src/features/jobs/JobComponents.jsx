import { useState } from "react";
import { Bookmark, BookmarkCheck, MapPin, Clock3, BriefcaseBusiness, ArrowUpRight, X } from "lucide-react";

export const jobKey = job => `${job.source}:${job.external_id}`;
export const plainText = value => (value || "").replace(/<[^>]*>/g, " ").replace(/&amp;/g, "&").trim();
export const dateLabel = value => {
  if (!value || !Number.isFinite(Date.parse(value))) return "Date unavailable";
  return new Intl.RelativeTimeFormat("en", { numeric: "auto" }).format(-Math.max(0, Math.floor((Date.now() - Date.parse(value)) / 86400000)), "day");
};

export function JobLogo({ job }) {
  const [failed, setFailed] = useState(null);
  const url = job.company_logo;
  return <div className="cp-company-logo">{url && failed !== url ? <img src={url} alt="" loading="lazy" onError={() => setFailed(url)} /> : <span>{(job.company || "?").split(/\s+/).slice(0, 2).map(x => x[0]).join("").toUpperCase()}</span>}</div>;
}

export function JobMeta({ job }) {
  return <div className="cp-job-meta"><span><MapPin size={13}/>{job.location || "Location not listed"}</span>{job.employment_type && <span><BriefcaseBusiness size={13}/>{job.employment_type}</span>}{job.workplace_type && job.workplace_type !== "unknown" && <span>{job.workplace_type}</span>}<span><Clock3 size={13}/>{dateLabel(job.posted_at)}</span></div>;
}

export function JobCard({ job, selected, saved, busy, onView, onSave, onApply, onSkip }) {
  return <article className={`cp-job-card ${selected ? "is-selected" : ""}`}><div className="cp-card-heading"><JobLogo job={job}/><div><p className="cp-company-name">{job.company}</p><button className="cp-title-button" onClick={onView}>{job.title}</button></div>{job.match_score != null && <span className="cp-match">{job.match_score}% <small>match</small></span>}</div><JobMeta job={job}/>{job.salary && <p className="cp-salary">{job.salary}</p>}{!!job.matched_skills?.length && <div className="cp-skill-chips">{job.matched_skills.slice(0, 4).map(skill => <span key={skill}>{skill}</span>)}</div>}<div className="cp-card-actions"><button className="cp-view" onClick={onView}>View details <ArrowUpRight size={14}/></button><div>{onSkip && <button disabled={busy} onClick={onSkip} aria-label={`Skip ${job.title}`}>Skip</button>}<button disabled={busy} onClick={onSave} aria-label={saved ? `Remove ${job.title} from saved jobs` : `Save ${job.title}`}>{saved ? <BookmarkCheck size={16}/> : <Bookmark size={16}/>} {saved ? "Saved" : "Save"}</button><button className="cp-apply-small" disabled={busy} onClick={onApply}>Apply</button></div></div></article>;
}

export function JobDetails({ job, saved, busy, onSave, onApply, onClose }) {
  if (!job) return <aside className="cp-job-details cp-detail-empty"><div className="cp-empty-icon"><BriefcaseBusiness size={28}/></div><h2>Your next move starts here</h2><p>Select a job to explore the role,<br/>review your match, and prepare an application.</p><div className="cp-empty-steps"><span>01 · Discover</span><span>02 · Review</span><span>03 · Apply</span></div></aside>;
  return <aside className="cp-job-details"><div className="cp-detail-top"><span>OPPORTUNITY DETAILS</span><button onClick={onClose} aria-label="Close job details"><X size={18}/></button></div><JobLogo job={job}/><p className="cp-company-name">{job.company}</p><h2>{job.title}</h2><JobMeta job={job}/>{job.salary && <p className="cp-salary">{job.salary}</p>}<div className="cp-detail-cta"><button className="button primary" disabled={busy} onClick={onApply}>Prepare application <ArrowUpRight size={16}/></button><button className="button secondary" disabled={busy} onClick={onSave}>{saved ? <BookmarkCheck size={17}/> : <Bookmark size={17}/>} {saved ? "Saved" : "Save"}</button></div><p className="cp-small-note">Review your materials before approving. Nothing is submitted automatically.</p>{job.match_score != null && <section className="cp-match-panel"><div><strong>CareerPilot Match</strong><span className="cp-match">{job.match_score}%</span></div><p>Evidence from your saved career data, not a hiring probability.</p><ul>{job.fit_reasons?.map(reason => <li key={reason}>{reason}</li>)}</ul>{!!job.skill_gaps?.length && <p><strong>Not found in your profile:</strong> {job.skill_gaps.join(", ")}. These skills appear in the job description.</p>}</section>}<section className="cp-description"><h3>About the opportunity</h3><p>{plainText(job.description) || "This source has not provided a description."}</p></section><p className="cp-small-note">Listing via {job.via || job.source}. Details are supplied by the job source.</p></aside>;
}
