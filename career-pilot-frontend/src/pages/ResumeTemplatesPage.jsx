import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Check,
  ChevronDown,
  Eye,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  demoResume,
  ResumePreview,
  templateList,
} from "../features/resume/templates/registry";
import { apiErrorMessage, careerApi } from "../services/careerApi";
const categories = [
  "all",
  "ats",
  "professional",
  "modern",
  "simple",
  "tech",
  "creative",
  "executive",
  "entry_level",
  "two_column",
];
const labels = {
  entry_level: "Entry level",
  two_column: "Two column",
  one_column: "One column",
  one_page: "One page",
  multi_page: "Multi page",
  senior: "Senior / Executive",
};
const title = (s) =>
  labels[s] || s.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const accentColors = [
  ["#1769d2", "Career blue"],
  ["#17324d", "Navy"],
  ["#334155", "Slate"],
  ["#0f766e", "Teal"],
  ["#7c3aed", "Violet"],
  ["#9f1239", "Burgundy"],
  ["#9a3412", "Terracotta"],
  ["#171717", "Black"],
];
function recommend(readiness, template) {
  const stage = (readiness?.career_stage || "").toLowerCase();
  if (
    stage.includes("student") ||
    stage.includes("graduate") ||
    stage.includes("entry")
  )
    return template.id === "graduate_launch" || template.id === "clear_ats";
  if (
    stage.includes("senior") ||
    stage.includes("executive") ||
    stage.includes("manager")
  )
    return (
      template.id === "executive_line" || template.id === "careerpilot_classic"
    );
  return template.id === "horizon" || template.id === "clear_ats";
}
export default function ResumeTemplatesPage() {
  const navigate = useNavigate();
  const client = useQueryClient();
  const [params] = useSearchParams();
  const resumeId = params.get("resume");
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({
    style: "",
    layout: "",
    level: "",
    industry: "",
    access: "",
  });
  const [preview, setPreview] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [accent, setAccent] = useState(
    () => localStorage.getItem("careerpilot_resume_accent") || "#1769d2",
  );
  const resumes = useQuery({
    queryKey: ["resumes"],
    queryFn: careerApi.listResumes,
  });
  const readiness = useQuery({
    queryKey: ["resume-readiness"],
    queryFn: careerApi.getResumeReadiness,
  });
  const current = resumes.data?.find((x) => x.id === resumeId);
  const items = useMemo(
    () =>
      templateList.filter(
        (t) =>
          (category === "all" || t.categories.includes(category)) &&
          (!search ||
            `${t.name} ${t.description} ${t.categories.join(" ")}`
              .toLowerCase()
              .includes(search.toLowerCase())) &&
          (!filters.style || t.styles.includes(filters.style)) &&
          (!filters.layout || t.layouts.includes(filters.layout)) &&
          (!filters.level || t.careerLevels.includes(filters.level)) &&
          (!filters.industry || t.industries.includes(filters.industry)) &&
          (!filters.access || t.tier === filters.access),
      ),
    [category, search, filters],
  );
  const choose = useMutation({
    mutationFn: async (id) =>
      resumeId
        ? careerApi.updateResume(resumeId, { template_id: id })
        : careerApi.generateResume({
            title: `Resume V${(resumes.data?.length || 0) + 1}`,
            template_id: id,
          }),
    onSuccess: async (result) => {
      localStorage.setItem("careerpilot_resume_template", result.template_id);
      localStorage.setItem("careerpilot_resume_accent", accent);
      await client.invalidateQueries({ queryKey: ["resumes"] });
      navigate(`/app/resume/${result.id}/edit`);
    },
  });
  const reason = (readiness.data?.career_stage || "")
    .toLowerCase()
    .includes("student")
    ? "Recommended because your profile is early-career; education and projects receive more space."
    : "Recommended for a clear, flexible presentation of your current profile.";
  return (
    <main className="template-gallery-page">
      <header className="gallery-header">
        <Link to={resumeId ? `/app/resume/${resumeId}/edit` : "/app/resume"}>
          <ArrowLeft size={17} />
          Back
        </Link>
        <div>
          <span className="section-eyebrow">CareerPilot templates</span>
          <h1>Choose a resume template</h1>
          <p>
            Start with an original, professionally structured design. Your
            content stays yours when you switch.
          </p>
        </div>
      </header>
      <div className="gallery-controls">
        <div className="gallery-search">
          <Search size={17} />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search templates"
          />
        </div>
        <button
          className="filter-toggle"
          onClick={() => setShowFilters((x) => !x)}
        >
          Filters <ChevronDown size={15} />
        </button>
      </div>
      <nav className="category-tabs" aria-label="Template categories">
        {categories.map((c) => (
          <button
            className={category === c ? "active" : ""}
            key={c}
            onClick={() => setCategory(c)}
          >
            {title(c)}
          </button>
        ))}
      </nav>
      <section className="gallery-color-control" aria-label="Resume color">
        <div>
          <strong>Choose your color</strong>
          <small>Preview it instantly on every template</small>
        </div>
        <div className="resume-color-swatches">
          {accentColors.map(([value, name]) => (
            <button
              type="button"
              key={value}
              className={accent === value ? "active" : ""}
              style={{ "--swatch-color": value }}
              title={name}
              aria-label={name}
              aria-pressed={accent === value}
              onClick={() => {
                setAccent(value);
                localStorage.setItem("careerpilot_resume_accent", value);
              }}
            >
              {accent === value && <Check size={12} />}
            </button>
          ))}
          <label className="custom-color-picker" title="Custom color">
            <input
              type="color"
              value={accent}
              onChange={(event) => {
                setAccent(event.target.value);
                localStorage.setItem(
                  "careerpilot_resume_accent",
                  event.target.value,
                );
              }}
            />
            Custom
          </label>
        </div>
      </section>
      <div className={`filter-panel ${showFilters ? "open" : ""}`}>
        {[
          [
            "style",
            [
              "professional",
              "modern",
              "minimal",
              "elegant",
              "creative",
              "corporate",
            ],
          ],
          ["layout", ["one_column", "two_column", "one_page", "multi_page"]],
          ["level", ["student", "entry", "mid", "senior"]],
          [
            "industry",
            [
              "technology",
              "business",
              "healthcare",
              "education",
              "engineering",
              "finance",
              "general",
            ],
          ],
          ["access", ["free"]],
        ].map(([key, values]) => (
          <label key={key}>
            <span>{title(key)}</span>
            <select
              value={filters[key]}
              onChange={(e) =>
                setFilters({ ...filters, [key]: e.target.value })
              }
            >
              <option value="">All</option>
              {values.map((x) => (
                <option key={x} value={x}>
                  {title(x)}
                </option>
              ))}
            </select>
          </label>
        ))}
      </div>
      <div className="gallery-result-line">
        <p>
          <strong>{items.length}</strong> templates
        </p>
        {Object.values(filters).some(Boolean) && (
          <button
            onClick={() =>
              setFilters({
                style: "",
                layout: "",
                level: "",
                industry: "",
                access: "",
              })
            }
          >
            <X size={13} />
            Clear filters
          </button>
        )}
      </div>
      <section className="template-gallery-grid">
        {items.map((template) => {
          const recommended = recommend(readiness.data, template);
          return (
            <article className="gallery-template-card" key={template.id}>
              <div className="gallery-preview-shell">
                <div className="gallery-paper">
                  <ResumePreview
                    content={current?.content || demoResume}
                    templateId={template.id}
                    design={{ accent }}
                    demo={!current}
                  />
                </div>
                <div className="template-hover-actions">
                  <button
                    className="button secondary"
                    onClick={() => setPreview(template)}
                  >
                    <Eye size={15} />
                    Preview
                  </button>
                  <button
                    className="button primary"
                    disabled={choose.isPending}
                    onClick={() => choose.mutate(template.id)}
                  >
                    Use this template
                  </button>
                </div>
                {!current && <span className="demo-label">Sample content</span>}
                {recommended && (
                  <span className="recommended-badge">
                    <Sparkles size={11} />
                    Recommended
                  </span>
                )}
              </div>
              <div className="gallery-template-meta">
                <div>
                  <h2>{template.name}</h2>
                  <p>
                    {template.categories.slice(0, 2).map(title).join(" · ")}
                  </p>
                </div>
                <span className="tier-badge free">Free</span>
              </div>
              <p className="template-description">{template.description}</p>
              {recommended && (
                <small className="recommendation-reason">{reason}</small>
              )}
              <button
                className="button use-template-mobile"
                onClick={() => choose.mutate(template.id)}
              >
                Use this template
              </button>
            </article>
          );
        })}
      </section>
      {choose.error && (
        <div className="gallery-error">{apiErrorMessage(choose.error)}</div>
      )}
      {preview && (
        <div className="template-preview-modal" role="dialog" aria-modal="true">
          <div className="preview-modal-bar">
            <button onClick={() => setPreview(null)}>
              <ArrowLeft size={16} />
              Back to templates
            </button>
            <div>
              <strong>{preview.name}</strong>
              <span>{preview.description}</span>
            </div>
            <button
              className="button primary"
              onClick={() => choose.mutate(preview.id)}
            >
              <Check size={15} />
              Use this template
            </button>
          </div>
          <div className="preview-modal-canvas">
            <ResumePreview
              content={current?.content || demoResume}
              templateId={preview.id}
              design={{ accent }}
              demo={!current}
            />
          </div>
        </div>
      )}
    </main>
  );
}
