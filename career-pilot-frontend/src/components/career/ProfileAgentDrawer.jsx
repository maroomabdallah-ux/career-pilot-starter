import { ArrowUpRight, Bot, BriefcaseBusiness, MapPin, Send, Sparkles, X } from "lucide-react";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { apiErrorMessage, careerApi } from "../../services/careerApi";
import { dateLabel, jobKey } from "../../features/jobs/JobComponents";

export default function ProfileAgentDrawer() {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState("");
  const [threadId, setThreadId] = useState();
  const [items, setItems] = useState([]);
  const [busy, setBusy] = useState(false);
  const client = useQueryClient();
  const navigate = useNavigate();
  const send = async (message = text) => {
    if (!message.trim() || busy) return;
    setItems((old) => [...old, { type: "user", message }]); setText(""); setBusy(true);
    try {
      const reply = await careerApi.profileAgentChat({ message, thread_id: threadId });
      setThreadId(reply.thread_id); setItems((old) => [...old, reply]);
    } catch (error) { setItems((old) => [...old, { type: "error", message: apiErrorMessage(error) }]); }
    finally { setBusy(false); }
  };
  const openJobs = (item, job = null) => {
    const criteria = item.search_criteria || {};
    navigate("/app/jobs", {
      state: {
        jobSearch: {
          query: criteria.query || "",
          location: criteria.location || "",
          workplace_type: criteria.workplace_type,
          employment_type: criteria.employment_type,
        },
        selectedJob: job,
        selectedJobKey: job ? jobKey(job) : null,
      },
    });
  };
  const decide = async (decision) => {
    setBusy(true);
    try { const reply = await careerApi.profileAgentApprove({ thread_id: threadId, decision }); setItems((old) => [...old, reply]); if (decision === "approve") { client.invalidateQueries({ queryKey: ["profile"] }); client.invalidateQueries({ queryKey: ["profile-completion"] }); client.invalidateQueries({ queryKey: ["dashboard"] }); } }
    catch { setItems((old) => [...old, { type: "error", message: "I couldn't save that change. Your profile has not been modified." }]); }
    finally { setBusy(false); }
  };
  return <>
    <button className="profile-agent-launch" onClick={() => setOpen(true)}><Sparkles size={16}/> Ask CareerPilot AI</button>
    {open && <aside className="profile-agent-drawer" aria-label="CareerPilot AI Assistant">
      <header><span><Bot size={18}/> CareerPilot AI</span><button className="icon-button" onClick={() => setOpen(false)}><X size={16}/></button></header>
      <div className="profile-agent-messages">
        {!items.length && <p className="agent-intro">Tell me about your career. I’ll always ask for approval before saving changes.</p>}
        {items.map((item, index) => <article key={index} className={`agent-message ${item.type}`}><p>{item.message}</p>
          {!!item.jobs?.length && <div className="agent-job-results">
            {item.jobs.map((job) => <button type="button" className="agent-job-card" key={jobKey(job)} onClick={() => openJobs(item, job)}>
              <strong>{job.title}</strong>
              <span className="agent-job-company">{job.company}</span>
              {job.location && <span><MapPin size={12}/>{job.location}</span>}
              <span className="agent-job-meta">
                {job.workplace_type && job.workplace_type !== "unknown" && <small>{job.workplace_type}</small>}
                {job.employment_type && <small><BriefcaseBusiness size={11}/>{job.employment_type}</small>}
                {job.posted_at && <small>{dateLabel(job.posted_at)}</small>}
              </span>
              {!!(job.matched_skills?.length || job.skills?.length) && <span className="agent-job-skills">{(job.matched_skills?.length ? job.matched_skills : job.skills).slice(0, 4).join(" · ")}</span>}
              <span className="agent-job-view">View Job <ArrowUpRight size={12}/></span>
            </button>)}
            {item.has_more_jobs && <button type="button" className="agent-view-all" onClick={() => openJobs(item)}>View all jobs <ArrowUpRight size={13}/></button>}
          </div>}
          {item.proposal && <div className="agent-proposal"><strong>{item.proposal.operation} {item.proposal.domain}</strong>{Object.entries(item.proposal.fields).map(([key, value]) => <span key={key}><small>{key.replaceAll("_", " ")}</small>{Array.isArray(value) ? value.join(", ") : String(value)}</span>)}<footer><button className="button secondary" onClick={() => decide("reject")} disabled={busy}>Reject</button><button className="button primary" onClick={() => decide("approve")} disabled={busy}>Approve</button></footer></div>}
        </article>)}
      </div>
      <form onSubmit={(event) => { event.preventDefault(); send(); }}><input value={text} onChange={(event) => setText(event.target.value)} placeholder="e.g. Add Python to my skills"/><button className="button primary" disabled={busy}><Send size={15}/></button></form>
    </aside>}
  </>;
}
