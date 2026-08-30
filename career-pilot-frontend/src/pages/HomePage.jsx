import { ArrowRight, Bookmark, BriefcaseBusiness, Check, ChevronRight, CircleUserRound, Download, Eye, FileCheck2, FilePenLine, FileText, FolderPlus, GraduationCap, MapPin, MessageSquareText, Plus, Send, Sparkles, TrendingUp, UserRoundSearch, Wrench } from "lucide-react";
import { Link } from "react-router-dom";
import AsyncState from "../components/common/AsyncState";
import SectionHeading from "../components/common/SectionHeading";
import { useCareerData } from "../hooks/useCareerData";

const jobs = [
  { role: "Backend Developer", company: "TechCorp", place: "Amman, Jordan", mode: "Remote", score: 98, tags: ["Python", "FastAPI"], age: "2h ago" },
  { role: "AI Engineer", company: "InnovateX", place: "Dubai, UAE", mode: "Hybrid", score: 95, tags: ["LLMs", "Python"], age: "5h ago" },
  { role: "Software Engineer", company: "DataWave", place: "Riyadh, Saudi Arabia", mode: "Remote", score: 92, tags: ["PostgreSQL", "React"], age: "1d ago" },
];

function CareerJourney() {
  const steps = ["Profile", "Resume", "Job matches", "Applications", "Career growth"];
  return <section className="journey-panel"><div className="journey-topline"><span>Your career journey</span><small>2 of 5 stages in motion</small></div><div className="journey-track"><div className="journey-line"><span /></div>{steps.map((step, index) => <div className={`journey-step ${index < 1 ? "complete" : ""} ${index === 1 ? "current" : ""}`} key={step}><span className="journey-dot">{index < 1 ? <Check size={13} /> : index + 1}</span><strong>{step}</strong><small>{index === 1 ? "Current focus" : index < 1 ? "Complete" : "Ahead"}</small></div>)}</div></section>;
}

function MetricCards({ completion }) {
  const metrics = [["Profile completion", `${completion}%`, CircleUserRound, "+12% this month"], ["Job matches", "24", UserRoundSearch, "5 new today"], ["Applications", "7", Send, "3 in review"], ["Profile views", "156", Eye, "+18% this week"]];
  return <div className="metric-grid">{metrics.map(([label, value, Icon, note]) => <article className="metric-card" key={label}><div className="metric-icon"><Icon size={18} /></div><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></article>)}</div>;
}

function CompletionCard({ profile, completion }) {
  const checks = [["Basic information", Boolean(profile?.professional_title)], ["Work experience", Boolean(profile?.experiences?.length)], ["Education", Boolean(profile?.education?.length)], ["Skills", Boolean(profile?.skills?.length)], ["Projects", Boolean(profile?.projects?.length)], ["Achievements", false], ["Certifications", false]];
  return <section className="surface completion-card"><SectionHeading eyebrow="Profile strength" title="Build a profile that gets noticed" copy="A complete profile gives CareerPilot better context for every recommendation." /><div className="progress-row"><div className="progress-track"><span style={{ width: `${completion}%` }} /></div><strong>{completion}%</strong></div><div className="check-grid">{checks.map(([label, done]) => <Link to="/profile" key={label} className={done ? "done" : ""}><span>{done ? <Check size={13} /> : <Plus size={13} />}</span>{label}<ChevronRight size={14} /></Link>)}</div></section>;
}

function AiPanel() {
  const actions = [["Optimize my resume", FileText], ["Find better job matches", BriefcaseBusiness], ["Improve my skills", Wrench], ["Prepare for interviews", MessageSquareText]];
  return <section className="ai-panel"><div className="ai-orbit"><Sparkles size={22} /></div><span className="section-eyebrow">AI career copilot</span><h2>Make your next move with clarity.</h2><p>Use your career profile to get focused, practical guidance—without the noise.</p><div className="ai-actions">{actions.map(([label, Icon]) => <button key={label}><Icon size={17} /><span>{label}</span><ArrowRight size={15} /></button>)}</div></section>;
}

function JobMatches() {
  return <section className="jobs-section"><SectionHeading eyebrow="Curated for your trajectory" title="Top job matches for you" copy="Ranked using your experience, skills, and career preferences." action={<button className="button secondary">View all matches <ArrowRight size={16} /></button>} /><div className="job-grid">{jobs.map((job, i) => <article className="job-card" key={job.role}><div className="job-card-top"><span className={`company-logo logo-${i}`}>{job.company[0]}</span><button className="icon-button quiet"><Bookmark size={18} /></button></div><div className="match-score"><span>{job.score}%</span> match</div><h3>{job.role}</h3><p className="company-name">{job.company}</p><p className="job-meta"><MapPin size={14} /> {job.place}<span />{job.mode}</p><div className="tag-row">{job.tags.map((tag) => <span key={tag}>{tag}</span>)}</div><footer><small>Posted {job.age}</small><button className="text-button">View role <ChevronRight size={14} /></button></footer></article>)}</div></section>;
}

function ProgressChart() {
  return <section className="surface chart-card"><SectionHeading eyebrow="Momentum" title="Career progress" action={<select><option>Last 6 months</option></select>} /><div className="chart-summary"><strong>+31%</strong><span>career readiness</span></div><div className="line-chart"><svg viewBox="0 0 600 180" preserveAspectRatio="none"><defs><linearGradient id="area" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#2f80ed" stopOpacity=".18"/><stop offset="1" stopColor="#2f80ed" stopOpacity="0"/></linearGradient></defs><path className="area" d="M0,146 C75,139 92,120 160,124 S245,104 300,99 S390,75 430,80 S525,45 600,37 L600,180 L0,180Z"/><path className="line" d="M0,146 C75,139 92,120 160,124 S245,104 300,99 S390,75 430,80 S525,45 600,37"/></svg><div className="chart-labels"><span>Mar</span><span>Apr</span><span>May</span><span>Jun</span><span>Jul</span><span>Aug</span></div></div></section>;
}

function ResumePreview() {
  return <section className="resume-panel"><div className="resume-copy"><span className="section-eyebrow">Resume intelligence</span><h2>Your story, sharpened for impact.</h2><p>A focused, ATS-ready presentation of your strongest experience.</p><div className="score-ring"><strong>92</strong><span>Resume score</span></div><ul><li><Check size={14}/> ATS friendly</li><li><Check size={14}/> Strong action verbs</li><li><Check size={14}/> Measurable impact</li></ul><div className="button-row"><button className="button primary"><FilePenLine size={16}/> Edit resume</button><button className="button secondary"><Download size={16}/> Export</button></div></div><div className="paper-stage"><div className="paper-back"/><div className="paper-wrap"><div className="resume-paper"><header><div><h4>ALEX MORGAN</h4><p>Senior Software Engineer</p></div><span>AM</span></header><div className="paper-rule"/><h5>PROFILE</h5><p>Product-minded engineer building reliable, elegant systems for ambitious teams.</p><h5>EXPERIENCE</h5><strong>Senior Software Engineer</strong><small>Technology Company · 2022 — Present</small><div className="paper-lines"><i/><i/><i/></div><h5>CORE EXPERTISE</h5><div className="paper-tags"><span>System design</span><span>Python</span><span>Leadership</span></div></div></div></div></section>;
}

export default function HomePage() {
  const { userId, user, profile } = useCareerData();
  const p = profile.data;
  const completed = p ? [p.professional_title, p.professional_summary, p.education?.length, p.experiences?.length, p.projects?.length, p.skills?.length].filter(Boolean).length : 0;
  const completion = userId ? Math.max(18, Math.round((completed / 6) * 100)) : 0;
  return <main className="page dashboard-page"><section className="dashboard-hero"><div><span className="hero-kicker">Sunday, 30 August</span><h1>Good morning, {user.data?.first_name || "there"}.</h1><p>Here’s the clearest view of your career momentum today.</p></div><Link className="button ai-button" to="/profile"><Sparkles size={17}/> Ask AI assistant</Link></section><div className="command-grid"><CareerJourney/><MetricCards completion={completion}/></div>{!userId ? <section className="setup-banner"><div className="setup-icon"><FileCheck2 size={23}/></div><div><span>Start with your story</span><h2>Create your career profile</h2><p>Give CareerPilot the context it needs to shape better recommendations for you.</p></div><Link className="button primary" to="/profile">Build my profile <ArrowRight size={16}/></Link></section> : <AsyncState loading={user.isLoading || profile.isLoading} error={user.error && user.error?.response?.status !== 404 ? user.error : null}><div className="two-column"><CompletionCard profile={p} completion={completion}/><AiPanel/></div></AsyncState>}<div className="analytics-grid"><ProgressChart/><section className="surface activity-card"><SectionHeading eyebrow="Latest signals" title="Recent activity"/><div className="activity-list">{[["Profile strengthened","Your professional summary was updated","2 hours ago",CircleUserRound],["New job match","Backend Developer at TechCorp","5 hours ago",BriefcaseBusiness],["Resume analyzed","Your score improved to 92","Yesterday",TrendingUp],["Application sent","Software Engineer at DataWave","2 days ago",Send]].map(([title, detail, time, Icon])=><div key={title}><span><Icon size={16}/></span><p><strong>{title}</strong><small>{detail}</small></p><time>{time}</time></div>)}</div></section></div><JobMatches/><ResumePreview/><section className="quick-actions"><SectionHeading eyebrow="Keep moving" title="Quick actions"/><div>{[["Add experience",BriefcaseBusiness],["Add project",FolderPlus],["Add skill",Wrench],["Add education",GraduationCap]].map(([label,Icon])=><Link to="/profile" key={label}><span><Icon size={18}/></span>{label}<ChevronRight size={15}/></Link>)}</div></section></main>;
}
