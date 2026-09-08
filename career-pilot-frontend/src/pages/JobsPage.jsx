import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, Bookmark, Search, MapPin, Sparkles, SlidersHorizontal, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { careerApi, apiErrorMessage } from "../services/careerApi";
import { JobCard, JobDetails, jobKey } from "../features/jobs/JobComponents";
import "../features/jobs/workspace.css";

export default function JobsPage() {
  const navigate = useNavigate();
  const [tab, setTab] = useState("recommended");
  const [feed, setFeed] = useState(null);
  const [saved, setSaved] = useState([]);
  const [selected, setSelected] = useState(null);
  const [query, setQuery] = useState("");
  const [location, setLocation] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [params, setParams] = useState({ page: 1, page_size: 10 });
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(null);
  const [skipped, setSkipped] = useState(new Set());
  const [savedPage, setSavedPage] = useState(1);
  const actionLock = useRef(false);
  const firstLoad = useRef(true);

  useEffect(() => { careerApi.listSavedJobs().then(setSaved).catch(() => setNotice("Saved jobs could not be loaded. Refresh to try again.")); }, []);
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null); setSelected(null);
    careerApi.searchJobsPage(params, controller.signal).then(result => {
      setFeed(result);
      if (firstLoad.current) { setLocation(result.search_location || ""); firstLoad.current = false; }
    }).catch(err => { if (err.code !== "ERR_CANCELED") setError(err); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [params]);

  const savedFor = job => saved.find(item => item.source === job.source && item.external_job_id === job.external_id);
  const act = async (job, operation) => {
    if (actionLock.current) return;
    actionLock.current = true; setBusy(jobKey(job)); setNotice("");
    try {
      if (operation === "apply") {
        const application = await careerApi.createApplication(job);
        navigate(`/app/applications/${application.id}`);
      } else {
        const current = savedFor(job);
        if (current) {
          await careerApi.unsaveJob(current.id); setSaved(items => items.filter(x => x.id !== current.id));
          setNotice("Removed from saved jobs.");
        } else {
          const item = await careerApi.saveJob(job);
          setSaved(items => [...items.filter(x => x.id !== item.id), item]);
          setNotice("Job saved. You can return to it anytime.");
        }
      }
    } catch (err) { setNotice(apiErrorMessage(err)); }
    finally { actionLock.current = false; setBusy(null); }
  };
  const search = event => {
    event.preventDefault(); setTab("recommended"); setSkipped(new Set());
    setParams({ q: query.trim(), location: location.trim(), page: 1, page_size: 10,
      workplace_type: filter === "remote" ? "remote" : undefined,
      employment_type: filter && filter !== "remote" ? filter : undefined });
  };
  const allSaved = saved.map(item => item.snapshot);
  const savedPages = Math.max(1, Math.ceil(allSaved.length / 10));
  const page = tab === "saved" ? Math.min(savedPage, savedPages) : (feed?.page || 1);
  const jobs = tab === "saved" ? allSaved.slice((page - 1) * 10, page * 10) : (feed?.jobs || []);
  const visible = jobs.filter(job => !skipped.has(jobKey(job)));
  const pages = tab === "saved" ? savedPages : feed?.total_pages || 1;
  const move = target => { setSelected(null); tab === "saved" ? setSavedPage(target) : setParams(old => ({ ...old, page: target })); };
  const changeTab = value => { setTab(value); setSelected(null); };

  return <main className="page cp-workspace"><header className="cp-page-header"><div><span className="cp-eyebrow"><Sparkles size={14}/> YOUR CAREER, IN FOCUS</span><h1>Find your next chapter<span>.</span></h1><p>Opportunities shaped around your experience, skills, and ambitions.</p></div><Link className="button secondary" to="/app/applications">My applications <ArrowRight size={16}/></Link></header>
    <section className="cp-context-bar"><div className="cp-context-icon"><Sparkles size={21}/></div><div><strong>{feed?.context_sources?.length ? "Your career profile is guiding the search" : "Let’s find your next opportunity"}</strong><p>{feed?.context_sources?.length ? `Using ${feed.context_sources.join(" + ")} · ${feed.search_query || "Technology roles"}` : "Add skills or a resume to get more personal recommendations."}</p></div><span className="cp-location-pill"><MapPin size={14}/>{feed?.search_location || "Open to locations"}</span><Link to="/app/profile">Update profile <ArrowRight size={14}/></Link></section>
    <div className="cp-toolbar"><div className="cp-tabs"><button className={tab === "recommended" ? "active" : ""} onClick={() => changeTab("recommended")}>For you</button><button className={tab === "saved" ? "active" : ""} onClick={() => changeTab("saved")}><Bookmark size={15}/> Saved <span>{saved.length}</span></button></div><button className="cp-filter-toggle" onClick={() => setFiltersOpen(x => !x)} aria-expanded={filtersOpen}><SlidersHorizontal size={16}/> Refine search</button></div>
    {filtersOpen && <form className="cp-search-form" onSubmit={search}><label><Search size={17}/><input aria-label="Job title or keyword" value={query} onChange={e => setQuery(e.target.value)} placeholder={feed?.search_query || "Role or keyword (optional)"}/></label><label><MapPin size={17}/><input aria-label="Job location" value={location} onChange={e => setLocation(e.target.value)} placeholder="Location (optional)"/></label><select aria-label="Job type" value={filter} onChange={e => setFilter(e.target.value)}><option value="">All work types</option><option value="remote">Remote</option><option value="full-time">Full-time</option><option value="part-time">Part-time</option><option value="internship">Internship</option></select><button className="button primary" disabled={loading}>Find jobs</button><button type="button" className="cp-text-button" onClick={() => { setQuery(""); setLocation(""); setFilter(""); firstLoad.current = true; setParams({ page: 1, page_size: 10 }); }}>Use my preferences</button></form>}
    {notice && <p className="cp-notice" role="status">{notice}</p>}
    {tab === "recommended" && feed?.message && <p className="cp-small-note">{feed.message}</p>}
    {tab === "recommended" && loading ? <div className="cp-loading" role="status"><RefreshCw className="spin" size={22}/><h2>Finding opportunities for you</h2><p>Checking real listings against your career profile…</p><div className="cp-skeleton"/><div className="cp-skeleton"/></div> : tab === "recommended" && error ? <div className="cp-empty"><h2>We couldn’t load your opportunities</h2><p>{apiErrorMessage(error)}</p><button className="button secondary" onClick={() => setParams(x => ({ ...x }))}>Try again</button></div> : <><div className="cp-results-heading"><div><h2>{tab === "saved" ? "Your saved opportunities" : "Recommended for you"}</h2><p>{tab === "saved" ? "Your shortlist, ready whenever you are." : "Best available matches first. Explore every role at your own pace."}</p></div><span>{visible.length} opportunities · Page {page}</span></div><div className={`cp-jobs-grid ${selected ? "has-selection" : ""}`}><section className="cp-job-list" aria-label="Job opportunities">{visible.map(job => <JobCard key={jobKey(job)} job={job} selected={selected && jobKey(selected) === jobKey(job)} saved={!!savedFor(job)} busy={!!busy} onView={() => setSelected(job)} onSave={() => act(job, "save")} onApply={() => act(job, "apply")} onSkip={tab === "recommended" ? () => { setSkipped(old => new Set([...old, jobKey(job)])); if (selected && jobKey(selected) === jobKey(job)) setSelected(null); } : undefined}/>)}{!visible.length && <div className="cp-empty"><Bookmark size={28}/><h2>{tab === "saved" ? "Build your shortlist" : "No opportunities in this view"}</h2><p>{tab === "saved" ? "Save a role from your recommendations to find it here later." : "Try another role or location, or restore jobs skipped during this visit."}</p>{skipped.size > 0 && <button className="button secondary" onClick={() => setSkipped(new Set())}>Restore skipped jobs</button>}</div>}</section><JobDetails job={selected} saved={selected && !!savedFor(selected)} busy={!!busy} onSave={() => act(selected, "save")} onApply={() => act(selected, "apply")} onClose={() => setSelected(null)}/></div><nav className="cp-pagination" aria-label="Job pages"><button disabled={page <= 1} onClick={() => move(page - 1)}><ChevronLeft size={16}/> Previous</button><span>{page} / {pages}</span><button disabled={page >= pages} onClick={() => move(page + 1)}>Next <ChevronRight size={16}/></button></nav></>}
  </main>;
}
