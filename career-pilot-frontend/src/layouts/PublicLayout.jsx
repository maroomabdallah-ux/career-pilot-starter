import { useEffect, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";

const sections = [
  ["Home", "top"],
  ["How it works", "how"],
  ["Features", "features"],
  ["Why CareerPilot", "career-system"],
];

export default function PublicLayout() {
  const location = useLocation();
  const isLanding = location.pathname === "/";
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState("top");

  useEffect(() => {
    const updateHeader = () => setScrolled(window.scrollY > 28);
    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
    return () => window.removeEventListener("scroll", updateHeader);
  }, []);

  useEffect(() => {
    setMenuOpen(false);
    if (!isLanding) return undefined;

    const targets = sections
      .map(([, id]) => document.getElementById(id))
      .filter(Boolean);
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) setActiveSection(visible.target.id);
      },
      { rootMargin: "-24% 0px -58%", threshold: [0, 0.15, 0.35] },
    );
    targets.forEach((target) => observer.observe(target));
    return () => observer.disconnect();
  }, [isLanding, location.pathname]);

  useEffect(() => {
    if (!menuOpen) return undefined;
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setMenuOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [menuOpen]);

  const goToSection = (event, id) => {
    if (!isLanding) return;
    event.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
    setActiveSection(id);
    setMenuOpen(false);
  };

  return (
    <div className="public-shell">
      <header
        className={`public-header ${scrolled ? "is-scrolled" : ""} ${menuOpen ? "menu-open" : ""}`}
      >
        <div className="public-nav-inner">
          <Link to="/" className="public-logo" aria-label="CareerPilot AI home">
            <img src="/careerpilot-logo.png" alt="CareerPilot AI" />
          </Link>

          {isLanding && (
            <nav className="public-section-nav" aria-label="Page sections">
              {sections.map(([label, id]) => (
                <a
                  key={id}
                  href={`#${id}`}
                  className={activeSection === id ? "active" : ""}
                  aria-current={activeSection === id ? "location" : undefined}
                  onClick={(event) => goToSection(event, id)}
                >
                  {label}
                </a>
              ))}
            </nav>
          )}

          <div className="public-nav-actions">
            <Link className="nav-signin" to="/login">
              Sign in
            </Link>
            <Link className="button primary nav-cta" to="/signup">
              Get started
            </Link>
          </div>

          {isLanding && (
            <button
              type="button"
              className="public-menu-toggle"
              aria-label={
                menuOpen ? "Close navigation menu" : "Open navigation menu"
              }
              aria-expanded={menuOpen}
              aria-controls="public-mobile-menu"
              onClick={() => setMenuOpen((open) => !open)}
            >
              <span />
              <span />
              <span />
            </button>
          )}
        </div>

        {isLanding && (
          <nav
            id="public-mobile-menu"
            className="public-mobile-menu"
            aria-label="Mobile navigation"
          >
            {sections.map(([label, id]) => (
              <a
                key={id}
                href={`#${id}`}
                className={activeSection === id ? "active" : ""}
                onClick={(event) => goToSection(event, id)}
              >
                {label}
              </a>
            ))}
            <div>
              <Link to="/login">Sign in</Link>
              <Link className="button primary" to="/signup">
                Get started
              </Link>
            </div>
          </nav>
        )}
      </header>
      <Outlet />
    </div>
  );
}
