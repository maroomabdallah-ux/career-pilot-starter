import { useLayoutEffect, useRef } from "react";
import {
  ArrowDown,
  ArrowRight,
  BadgeCheck,
  BrainCircuit,
  BriefcaseBusiness,
  Check,
  FileText,
  Search,
  Sparkles,
  Target,
  UserRound,
  WandSparkles,
} from "lucide-react";
import { Link } from "react-router-dom";

function useScrollReveal() {
  const pageRef = useRef(null);

  useLayoutEffect(() => {
    const page = pageRef.current;
    if (!page) return undefined;
    const elements = [...page.querySelectorAll("[data-reveal]")];
    page.classList.add("reveal-ready");

    if (!("IntersectionObserver" in window)) {
      elements.forEach((element) => element.classList.add("is-revealed"));
      return undefined;
    }

    const observer = new IntersectionObserver(
      (entries) =>
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-revealed");
          observer.unobserve(entry.target);
        }),
      { threshold: 0.14, rootMargin: "0px 0px -7%" },
    );

    elements.forEach((element) => observer.observe(element));
    return () => observer.disconnect();
  }, []);

  return pageRef;
}

function ResumeCreationVisual() {
  return (
    <div className="resume-hero-visual">
      <div className="ambient-orbit" />
      <aside className="profile-float">
        <UserRound size={18} />
        <div>
          <small>Career profile</small>
          <strong>Backend Developer</strong>
          <span>Experience · Skills · Projects</span>
        </div>
      </aside>
      <div className="hero-paper-back" />
      <article className="hero-resume">
        <header>
          <div>
            <h3>MAROOM ABDALLA</h3>
            <p>Backend Developer</p>
          </div>
          <span>AM</span>
        </header>
        <section>
          <h4>PROFILE</h4>
          <p>
            Backend developer focused on reliable application systems and clear
            product outcomes.
          </p>
        </section>
        <section>
          <h4>EXPERIENCE</h4>
          <strong>Backend Developer</strong>
          <small>Sample Technology Company · Demonstration</small>
          <p className="typing-line">
            Built and maintained scalable FastAPI endpoints supporting core
            application workflows.
          </p>
        </section>
        <section>
          <h4>EDUCATION</h4>
          <strong>BSc Computer Science</strong>
        </section>
        <section className="resume-split">
          <div>
            <h4>SKILLS</h4>
            <p>Python · FastAPI · PostgreSQL</p>
          </div>
          <div>
            <h4>PROJECTS</h4>
            <p>Career platform · API systems</p>
          </div>
        </section>
        <em>Sample product demonstration</em>
      </article>
      <aside className="suggestion-float">
        <Sparkles size={17} />
        <small>CareerPilot suggestion</small>
        <p>
          <s>Worked on backend APIs.</s>
        </p>
        <strong>Built and maintained scalable FastAPI endpoints…</strong>
      </aside>
      <aside className="strength-float">
        <span>Profile data ready</span>
        <strong>4 / 6</strong>
        <i>
          <b />
        </i>
      </aside>
    </div>
  );
}

export default function LandingPage() {
  const pageRef = useScrollReveal();
  const flow = [
    [
      UserRound,
      "01",
      "Tell your story once",
      "Bring your experience, skills, education, and goals into one living career profile.",
    ],
    [
      WandSparkles,
      "02",
      "Create with context",
      "Generate focused resumes and guidance shaped around the role you actually want.",
    ],
    [
      BriefcaseBusiness,
      "03",
      "Move with clarity",
      "Discover opportunities, prepare stronger applications, and keep every next step connected.",
    ],
  ];

  return (
    <main id="top" ref={pageRef} className="landing premium-landing">
      <section className="landing-hero">
        <div data-reveal="fade-up">
          <span className="hero-kicker">
            Your global career operating system
          </span>
          <h1>Build your career profile once. Turn it into opportunity.</h1>
          <p>
            Create stronger resumes, prepare for relevant opportunities, and
            navigate your career with intelligent guidance.
          </p>
          <div className="button-row">
            <Link className="button primary" to="/signup">
              Build my career profile <ArrowRight size={17} />
            </Link>
            <a className="button secondary" href="#how">
              See how it works <ArrowDown size={16} />
            </a>
          </div>
          <small>
            <Check size={15} /> Global by design · Your career data stays yours
          </small>
        </div>
        <div data-reveal="slide-left" style={{ "--reveal-delay": "120ms" }}>
          <ResumeCreationVisual />
        </div>
      </section>

      <section className="value-ribbon" aria-label="CareerPilot benefits">
        {[
          ["One profile", "Your professional foundation"],
          ["Every opportunity", "Tailored with real context"],
          ["Always evolving", "Built to grow with you"],
        ].map(([title, copy], index) => (
          <div
            key={title}
            data-reveal="fade-up"
            style={{ "--reveal-delay": `${index * 70}ms` }}
          >
            <Check size={16} />
            <span>
              <strong>{title}</strong>
              <small>{copy}</small>
            </span>
          </div>
        ))}
      </section>

      <section className="connected-story" id="how">
        <header data-reveal="fade-up">
          <div>
            <span className="section-eyebrow">
              One connected career journey
            </span>
            <h2>Less busywork. More forward motion.</h2>
          </div>
          <p>
            CareerPilot remembers the details that matter, so every tool starts
            with your real experience—not a blank page.
          </p>
        </header>
        <div className="journey-grid">
          {flow.map(([Icon, num, title, copy], index) => (
            <article
              key={title}
              data-reveal="fade-up"
              style={{ "--reveal-delay": `${index * 90}ms` }}
            >
              <div className="journey-icon">
                <Icon size={22} />
              </div>
              <span>{num}</span>
              <h3>{title}</h3>
              <p>{copy}</p>
              <i>
                <ArrowRight size={18} />
              </i>
            </article>
          ))}
        </div>
      </section>

      <section className="intelligence-showcase" id="features">
        <header data-reveal="fade-up">
          <span className="section-eyebrow">Built around your ambition</span>
          <h2>Not another collection of disconnected career tools.</h2>
          <p>
            One intelligent workspace turns what you have done into what you can
            do next.
          </p>
        </header>
        <div className="career-bento">
          <article className="bento-primary" data-reveal="slide-right">
            <span className="bento-icon">
              <BrainCircuit size={24} />
            </span>
            <small>CAREER INTELLIGENCE</small>
            <h3>Guidance that already knows your background.</h3>
            <p>
              Your goals, strengths, and experience stay connected across every
              decision.
            </p>
            <div className="insight-card">
              <Sparkles size={17} />
              <span>
                <small>Career insight</small>
                <strong>
                  Your backend experience aligns strongly with platform
                  engineering roles.
                </strong>
              </span>
            </div>
          </article>
          <article
            data-reveal="slide-left"
            style={{ "--reveal-delay": "80ms" }}
          >
            <span className="bento-icon">
              <FileText size={22} />
            </span>
            <small>RESUME STUDIO</small>
            <h3>From experience to impact.</h3>
            <div className="mini-score">
              <span>Resume strength</span>
              <strong>92%</strong>
              <i>
                <b />
              </i>
            </div>
          </article>
          <article
            data-reveal="slide-left"
            style={{ "--reveal-delay": "150ms" }}
          >
            <span className="bento-icon">
              <Search size={22} />
            </span>
            <small>OPPORTUNITY MATCHING</small>
            <h3>Focus on roles that fit your direction.</h3>
            <div className="match-pills">
              <span>Backend</span>
              <span>Remote</span>
              <span>High match</span>
            </div>
          </article>
        </div>
      </section>

      <section className="career-system career-system-dark" id="career-system">
        <div data-reveal="slide-right">
          <span className="section-eyebrow">Your career, connected</span>
          <h2>Every step gets smarter because nothing starts from zero.</h2>
          <p>
            Your profile becomes the context behind your resumes, opportunities,
            applications, and long-term direction.
          </p>
          <div className="system-checks">
            <span>
              <BadgeCheck size={17} />
              One source of truth
            </span>
            <span>
              <BadgeCheck size={17} />
              Built for continuous growth
            </span>
          </div>
          <Link className="button primary" to="/signup">
            Start your foundation <ArrowRight size={17} />
          </Link>
        </div>
        <div
          data-reveal="slide-left"
          style={{ "--reveal-delay": "100ms" }}
          className="career-map"
        >
          <div className="system-orbit">
            <span>
              <UserRound />
              Profile
            </span>
            <span>
              <FileText />
              Resume
            </span>
            <span>
              <Target />
              Direction
            </span>
            <b>CP</b>
          </div>
        </div>
      </section>

      <section className="final-cta" data-reveal="fade-up">
        <span className="cta-spark">
          <Sparkles size={22} />
        </span>
        <h2>Your next chapter deserves a stronger starting point.</h2>
        <p>
          Build the foundation now. Let every future CareerPilot tool begin with
          the real you.
        </p>
        <Link className="button primary" to="/signup">
          Create your account <ArrowRight size={17} />
        </Link>
      </section>
      <footer className="public-footer" data-reveal="fade-up">
        <img src="/careerpilot-logo.png" alt="CareerPilot" />
        <span>© 2026 CareerPilot AI · Global careers, thoughtfully guided</span>
      </footer>
    </main>
  );
}
