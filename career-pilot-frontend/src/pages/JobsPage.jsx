import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Bookmark, Search, RefreshCw, SlidersHorizontal } from "lucide-react";
import { careerApi, apiErrorMessage } from "../services/careerApi";
import { JobCard, JobDetails, jobKey } from "../features/jobs/JobComponents";
import "../features/jobs/workspace.css";

const PAGE_SIZE = 20;
const initialFilters = { q: "", location: "", country: "", workplace_type: "", date_posted: "", experience_level: "", employment_type: "" };

export default function JobsPage({ savedOnly = false }) {
  const navigate = useNavigate();
  const route = useLocation();
  const incoming = route.state?.jobSearch;
  const [draft, setDraft] = useState({ ...initialFilters, ...incoming });
  const [criteria, setCriteria] = useState({ ...initialFilters, ...incoming });
  const [page, setPage] = useState(1);
  const [feed, setFeed] = useState(null);
  const [saved, setSaved] = useState([]);
  const [selected, setSelected] = useState(route.state?.selectedJob || null);
  const [pendingKey, setPendingKey] = useState(route.state?.selectedJobKey || null);
  const [loading, setLoading] = useState(!savedOnly);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [retry, setRetry] = useState(0);
  const [expanded, setExpanded] = useState(false);
  const requestId = useRef(0);

  useEffect(() => {
    careerApi.listSavedJobs().then(setSaved).catch((err) => setNotice(`Saved jobs unavailable: ${apiErrorMessage(err)}`));
  }, []);
  useEffect(() => {
    if (!route.state?.jobSearch && !route.state?.selectedJob) return;
    const next = { ...initialFilters, ...route.state.jobSearch };
    setDraft(next); setFeed(null); setExpanded(false); setCriteria(next); setPage(1);
    setSelected(route.state.selectedJob || null);
    setPendingKey(route.state.selectedJobKey || null);
    navigate(route.pathname, { replace: true, state: null });
  }, [route.state, route.pathname, navigate]);
  useEffect(() => {
    if (savedOnly) return;
    const controller = new AbortController();
    const id = ++requestId.current;
    setLoading(true); setError(null);
    const params = Object.fromEntries(Object.entries(criteria).filter(([, value]) => value));
    careerApi.searchJobsPage({ ...params, page, page_size: PAGE_SIZE, mode: "feed", expand: expanded }, controller.signal)
      .then((result) => {
        if (requestId.current !== id) return;
        setFeed((previous) => (page === 1 && !expanded) || !previous ? result : {
          ...result,
          jobs: [...previous.jobs, ...result.jobs.filter((job) => !previous.jobs.some((existing) => jobKey(existing) === jobKey(job)))],
        });
        if (page === 1) setSelected((current) => result.jobs.find((job) => jobKey(job) === (pendingKey || (current && jobKey(current)))) || (pendingKey ? current : result.jobs[0] || null));
        setPendingKey(null);
      })
      .catch((err) => { if (err.code !== "ERR_CANCELED" && requestId.current === id) setError(err); })
      .finally(() => { if (!controller.signal.aborted && requestId.current === id) setLoading(false); });
    return () => controller.abort();
  }, [criteria, page, retry, savedOnly, expanded]);

  const savedFor = (job) => saved.find((item) => item.source === job.source && item.external_job_id === job.external_id);
  const act = async (job, operation) => {
    if (!job || busy) return;
    setBusy(true); setNotice("");
    try {
      if (operation === "apply") {
        const application = await careerApi.createApplication(job);
        navigate(`/app/applications/${application.id}`);
      } else {
        const current = savedFor(job);
        if (current) {
          await careerApi.unsaveJob(current.id);
          setSaved((items) => items.filter((item) => item.id !== current.id));
          setNotice("Removed from saved jobs.");
        } else {
          const item = await careerApi.saveJob(job);
          setSaved((items) => [...items, item]);
          setNotice("Job saved.");
        }
      }
    } catch (err) { setNotice(apiErrorMessage(err)); }
    finally { setBusy(false); }
  };
  const update = (name) => (event) => setDraft((old) => ({ ...old, [name]: event.target.value }));
  const search = (event) => { event.preventDefault(); setFeed(null); setExpanded(false); setPage(1); setCriteria({ ...draft }); };
  const savedJobs = saved.map((item) => item.snapshot);
  const savedPages = Math.max(1, Math.ceil(savedJobs.length / PAGE_SIZE));
  const jobs = savedOnly ? savedJobs.slice(0, page * PAGE_SIZE) : feed?.jobs || [];
  const hasMore = savedOnly ? page < savedPages : !!feed && (feed.has_next || (!expanded && !criteria.q));
  return <main className="page cp-workspace cp-feed-page">
    <header className="cp-page-header"><div><span className="cp-eyebrow">CAREERPILOT JOBS</span><h1>{savedOnly ? "Saved jobs" : "Find your next opportunity"}</h1><p>{savedOnly ? "Your shortlist, ready when you are." : "Explore real jobs across every profession, with your strongest matches first."}</p></div>
      <div className="cp-feed-header-links"><Link className="button secondary" to={savedOnly ? "/app/jobs" : "/app/jobs/saved"}>{savedOnly ? "Browse jobs" : <>Saved jobs <Bookmark size={15} /> {saved.length}</>}</Link><Link className="button secondary" to="/app/applications">My applications</Link></div>
    </header>
    {notice && <p className="cp-notice" role="status">{notice}</p>}
    {!savedOnly && <form className="cp-feed-search" onSubmit={search}>
      <label className="cp-feed-search-main"><Search size={18} /><input aria-label="Job title, keyword, skill or company" value={draft.q || ""} onChange={update("q")} placeholder="Job title, skill, or company" /></label>
      <label className="cp-feed-search-place"><input aria-label="City or location" value={draft.location || ""} onChange={update("location")} placeholder="City or location" /></label>
      <button className="button primary" type="submit">Search jobs</button>
      <button className="button secondary cp-filter-trigger" type="button" aria-expanded={filtersOpen} onClick={() => setFiltersOpen((open) => !open)}><SlidersHorizontal size={16} /> Filters</button>
      {filtersOpen && <div className="cp-feed-advanced">
        <label>Country<input aria-label="Country" value={draft.country || ""} onChange={update("country")} placeholder="e.g. Jordan" /></label>
        <label>Workplace<select value={draft.workplace_type || ""} onChange={update("workplace_type")}><option value="">Any workplace</option><option value="remote">Remote</option><option value="hybrid">Hybrid</option><option value="on-site">On-site</option></select></label>
        <label>Date posted<select value={draft.date_posted || ""} onChange={update("date_posted")}><option value="">Any date</option><option value="24h">Past 24 hours</option><option value="7d">Past 7 days</option><option value="30d">Past 30 days</option></select></label>
        <label>Experience level<input value={draft.experience_level || ""} onChange={update("experience_level")} placeholder="e.g. Senior" /></label>
        <label>Employment type<select value={draft.employment_type || ""} onChange={update("employment_type")}><option value="">Any type</option><option value="full-time">Full-time</option><option value="part-time">Part-time</option><option value="contract">Contract</option><option value="internship">Internship</option></select></label>
        <button className="cp-text-button" type="button" onClick={() => { setDraft(initialFilters); setCriteria(initialFilters); setPage(1); }}>Clear filters</button>
      </div>}
    </form>}
    <div className={`cp-unified-grid ${savedOnly ? "cp-saved-grid" : ""}`}>
      <section className="cp-feed-list" aria-label={savedOnly ? "Saved jobs" : "Job opportunities"}>
        <div className="cp-feed-list-head"><div><h2>{savedOnly ? "Saved opportunities" : criteria.q ? `Results for “${criteria.q}”` : "Jobs for you"}</h2><p>{savedOnly ? `${saved.length} saved` : feed?.context_sources?.length ? `Prioritized using ${feed.context_sources.join(" + ")}; all careers remain visible.` : "Browse opportunities across professions."}</p></div></div>
        {!savedOnly && feed?.message && <p className="cp-small-note">{feed.message}</p>}
        {!savedOnly && feed?.source_failures?.length > 0 && <p className="cp-notice">Some sources are unavailable: {feed.source_failures.join(", ")}. Showing available results.</p>}
        {!savedOnly && loading && !feed && <div className="cp-loading" role="status"><RefreshCw className="spin" size={20} /> Loading real jobs…</div>}
        {!savedOnly && error && <div className="cp-empty"><h2>Jobs are temporarily unavailable</h2><p>{error.code === "ECONNABORTED" ? "Job sources took too long to respond. Try again to check for newly cached results." : apiErrorMessage(error)}</p><button className="button secondary" onClick={() => setRetry((x) => x + 1)}>Try again</button></div>}
        {jobs.map((job) => <JobCard key={jobKey(job)} job={job} selected={selected && jobKey(selected) === jobKey(job)} saved={!!savedFor(job)} busy={busy} onView={() => setSelected(job)} onSave={() => act(job, "save")} onApply={() => act(job, "apply")} />)}
        {!loading && !error && !jobs.length && <div className="cp-empty"><h2>{savedOnly ? "No saved jobs yet" : feed?.source_failures?.length ? "No results from available sources" : "No jobs matched these filters"}</h2><p>{savedOnly ? "Save a job from the feed to keep it here." : "Try another role, location, or broader filters."}</p></div>}
        {hasMore && <div className="cp-load-more"><button className="button secondary" disabled={loading} onClick={() => { if (!savedOnly && !feed.has_next) { setPage(1); setExpanded(true); } else setPage((current) => current + 1); }}>{loading ? "Loading…" : "Load more jobs"}</button></div>}
      </section>
      <JobDetails job={selected} saved={selected && !!savedFor(selected)} busy={busy} onSave={() => act(selected, "save")} onApply={() => act(selected, "apply")} onClose={() => setSelected(null)} />
    </div>
  </main>;
}
