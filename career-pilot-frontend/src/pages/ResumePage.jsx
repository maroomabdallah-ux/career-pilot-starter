import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowDown,
  ArrowUp,
  Check,
  Download,
  Eye,
  EyeOff,
  Plus,
  Palette,
  RefreshCw,
  Save,
  Sparkles,
  X,
} from "lucide-react";
import {
  ResumePreview,
  getResumeTemplate,
} from "../features/resume/templates/registry";
import { apiErrorMessage, careerApi } from "../services/careerApi";
import ResumeBlockEditor from "../features/resume/ResumeBlockEditor";

const generationStages = [
  "Preparing your career profile",
  "Reviewing your experience",
  "Structuring your resume",
  "Improving your content",
  "Validating facts",
  "Creating your draft",
];
const clone = (value) => JSON.parse(JSON.stringify(value));
const sectionNames = {
  summary: "Summary",
  experience: "Experience",
  education: "Education",
  projects: "Projects",
  skills: "Skills",
};

export default function ResumePage() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const client = useQueryClient();
  const [selectedId, setSelectedId] = useState(resumeId || "");
  const [draft, setDraft] = useState(null);
  const [generationStage, setGenerationStage] = useState(0);
  const [mobilePreview, setMobilePreview] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [rightMode, setRightMode] = useState(null);
  const [resumeTitle, setResumeTitle] = useState("");
  const [pdfFilename, setPdfFilename] = useState("");
  const [saveState, setSaveState] = useState("saved");
  const [selection, setSelection] = useState({ section: "summary" });
  const [coachResult, setCoachResult] = useState(null);
  const [answer, setAnswer] = useState("");
  const [dismissed, setDismissed] = useState([]);
  const [pendingTemplate, setPendingTemplate] = useState(
    () =>
      localStorage.getItem("careerpilot_resume_template") ||
      "careerpilot_classic",
  );
  const [design, setDesign] = useState({
    accent: localStorage.getItem("careerpilot_resume_accent") || "#1769d2",
    font: "professional",
    textSize: 100,
    lineSpacing: 1.45,
    sectionSpacing: 16,
    pageMargins: 16,
  });
  useEffect(() => {
    localStorage.setItem("careerpilot_resume_accent", design.accent);
  }, [design.accent]);
  const resumes = useQuery({
    queryKey: ["resumes"],
    queryFn: careerApi.listResumes,
  });
  const readiness = useQuery({
    queryKey: ["resume-readiness"],
    queryFn: careerApi.getResumeReadiness,
  });
  const selected = useMemo(
    () => resumes.data?.find((item) => item.id === (resumeId || selectedId)),
    [resumes.data, selectedId, resumeId],
  );
  const analysis = useQuery({
    queryKey: ["resume-analysis", selected?.id],
    queryFn: () => careerApi.analyzeResume(selected.id),
    enabled: Boolean(selected?.id),
  });

  useEffect(() => {
    if (selected) {
      setSelectedId(selected.id);
      setDraft(clone(selected.content));
      setResumeTitle(selected.title);
      setPdfFilename(`${selected.title.replace(/[^a-z0-9]+/gi, "_")}.pdf`);
      setSaveState("saved");
    }
  }, [selected?.id, selected?.updated_at]);
  const refresh = () => client.invalidateQueries({ queryKey: ["resumes"] });
  const generate = useMutation({
    mutationFn: () =>
      careerApi.generateResume({
        title: `Resume V${(resumes.data?.length || 0) + 1}`,
        template_id: pendingTemplate,
      }),
    onMutate: () => setGenerationStage(0),
    onSuccess: async (created) => {
      setSelectedId(created.id);
      await refresh();
    },
  });
  useEffect(() => {
    if (!generate.isPending) return;
    const timer = setInterval(
      () =>
        setGenerationStage((x) => Math.min(x + 1, generationStages.length - 1)),
      1100,
    );
    return () => clearInterval(timer);
  }, [generate.isPending]);
  const save = useMutation({
    mutationFn: () =>
      careerApi.updateResume(selected.id, {
        content: draft,
        title: resumeTitle.trim(),
      }),
    onMutate: () => setSaveState("saving"),
    onSuccess: async () => {
      await refresh();
      setSaveState("saved");
    },
    onError: () => setSaveState("unsaved"),
  });
  const template = useMutation({
    mutationFn: (templateId) =>
      careerApi.updateResume(selected.id, { template_id: templateId }),
    onSuccess: refresh,
  });
  const approve = useMutation({
    mutationFn: (id) =>
      selected.status === "draft"
        ? careerApi.reviewResume(id)
        : careerApi.approveResume(id),
    onSuccess: refresh,
  });
  const regenerate = useMutation({
    mutationFn: (section) =>
      careerApi.regenerateResumeSection(selected.id, section),
    onSuccess: refresh,
  });
  const coach = useMutation({
    mutationFn: (payload) => careerApi.coachResume(selected.id, payload),
    onSuccess: setCoachResult,
  });
  const applySuggestion = useMutation({
    mutationFn: ({ suggestion, edited_text }) =>
      careerApi.applyResumeSuggestion(selected.id, { suggestion, edited_text }),
    onSuccess: async () => {
      setCoachResult(null);
      await refresh();
      client.invalidateQueries({ queryKey: ["resume-analysis", selected.id] });
    },
  });
  const exportPdf = useMutation({
    mutationFn: () => careerApi.exportResume(selected.id),
    onSuccess: ({ data }) => {
      const url = URL.createObjectURL(data);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = pdfFilename.trim().endsWith(".pdf")
        ? pdfFilename.trim()
        : `${pdfFilename.trim() || selected.title}.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    },
  });
  const error =
    resumes.error ||
    readiness.error ||
    generate.error ||
    save.error ||
    template.error ||
    regenerate.error ||
    exportPdf.error;
  const update = (path, value) => (
    setSaveState("unsaved"),
    setDraft((current) => {
      const next = clone(current);
      let target = next;
      path.slice(0, -1).forEach((key) => {
        target = target[key];
      });
      target[path.at(-1)] = value;
      return next;
    })
  );
  const boldSelection = (path, value) => {
    const field = document.activeElement;
    const start = field?.tagName === "TEXTAREA" ? field.selectionStart : 0;
    const end =
      field?.tagName === "TEXTAREA" ? field.selectionEnd : value.length;
    const selectedText = value.slice(start, end) || "important text";
    update(
      path,
      `${value.slice(0, start)}**${selectedText}**${value.slice(end)}`,
    );
  };
  const toggleSection = (key) =>
    setDraft((current) => ({
      ...current,
      hidden_sections: current.hidden_sections?.includes(key)
        ? current.hidden_sections.filter((x) => x !== key)
        : [...(current.hidden_sections || []), key],
    }));
  const moveSection = (index, direction) =>
    setDraft((current) => {
      const order = [...current.section_order];
      const to = index + direction;
      if (to < 0 || to >= order.length) return current;
      [order[index], order[to]] = [order[to], order[index]];
      return { ...current, section_order: order };
    });
  const moveSectionTo = (from, to) =>
    setDraft((current) => {
      const order = [...current.section_order];
      const [section] = order.splice(from, 1);
      order.splice(to, 0, section);
      return { ...current, section_order: order };
    });
  const choosePendingTemplate = (id) => {
    setPendingTemplate(id);
    localStorage.setItem("careerpilot_resume_template", id);
  };
  const selectedAnalysis =
    coachResult?.analysis ||
    analysis.data?.analyses?.find(
      (item) =>
        item.section === selection.section &&
        (item.item_index ?? null) === (selection.item_index ?? null),
    ) ||
    analysis.data?.top_priority;
  const inspect = (next) => {
    setSelection(next);
    setCoachResult(null);
  };
  const openBlockAI = (message) => {
    setAiOpen(true);
    setRightMode("ai");
    coach.mutate({ selection, message });
  };
  const askCoach = (message = "Analyze this section", user_answer) =>
    coach.mutate({
      selection,
      message,
      ...(user_answer ? { user_answer } : {}),
    });

  if (resumes.isLoading || readiness.isLoading)
    return (
      <main className="page">
        <section className="surface async-state">
          <p>Opening Resume Studio…</p>
        </section>
      </main>
    );
  if (!resumes.data?.length)
    return (
      <main className="page resume-studio-page">
        <section className="surface resume-studio-toolbar">
          <div>
            <span className="section-eyebrow">Resume Studio</span>
            <h1>Create your first professional resume</h1>
            <p>
              Choose a design, then let CareerPilot structure your verified
              profile.
            </p>
          </div>
          <div className="button-row">
            <span className="studio-save-state">Not generated</span>
            <button
              className="button primary"
              disabled={!readiness.data?.ready || generate.isPending}
              onClick={() => generate.mutate()}
            >
              <Plus size={16} />
              {generate.isPending
                ? generationStages[generationStage]
                : "Generate resume"}
            </button>
          </div>
        </section>
        <div className="resume-studio-grid resume-empty-studio">
          <aside className="surface resume-controls">
            <div className="control-heading">
              <div>
                <span>Start with design</span>
                <strong>Resume templates</strong>
              </div>
            </div>
            <TemplateSelector
              value={pendingTemplate}
              onChange={choosePendingTemplate}
            />
            <div className="resume-edit-block">
              <strong>Profile sources</strong>
              {Object.entries(readiness.data?.available || {}).map(
                ([name, count]) => (
                  <div className="source-line" key={name}>
                    <span>
                      {count ? "✓" : "○"} {sectionNames[name] || name}
                    </span>
                    <small>{count}</small>
                  </div>
                ),
              )}
            </div>
          </aside>
          <section className="resume-preview-workspace">
            <div className="preview-topline">
              <span>A4 document workspace</span>
              <small>{pendingTemplate.replaceAll("_", " ")}</small>
            </div>
            <div
              className={`resume-document resume-generation-canvas template-${pendingTemplate}`}
            >
              <div className="generation-in-document">
                <span className="document-kicker">
                  CareerPilot Resume Agent
                </span>
                <h2>
                  {generate.isPending
                    ? generationStages[generationStage]
                    : "Your Career Profile is ready to become a resume."}
                </h2>
                <p>
                  {generate.isPending
                    ? "Your profile is safe while CareerPilot prepares and validates the draft."
                    : "Generate a structured draft using only your verified profile facts. You can edit every section afterward."}
                </p>
                {generate.isPending && (
                  <div className="generation-progress">
                    <i
                      style={{
                        width: `${((generationStage + 1) / generationStages.length) * 100}%`,
                      }}
                    />
                  </div>
                )}
                <button
                  className="button primary"
                  disabled={!readiness.data?.ready || generate.isPending}
                  onClick={() => generate.mutate()}
                >
                  {generate.isPending ? "Working…" : "Generate resume"}
                </button>
                {generate.error && (
                  <div className="compact-generation-error">
                    <strong>
                      CareerPilot couldn't finish this resume draft.
                    </strong>
                    <span>Your profile was not changed.</span>
                    <button onClick={() => generate.mutate()}>Retry</button>
                  </div>
                )}
              </div>
            </div>
          </section>
          <aside className="surface resume-inspector">
            <span className="section-eyebrow">What happens next</span>
            <h2>A real editable draft</h2>
            <p>
              CareerPilot selects and rewrites verified content, validates
              facts, and saves a new independent version.
            </p>
            <div className="empty-section-list">
              {Object.values(sectionNames).map((name) => (
                <span key={name}>{name}</span>
              ))}
            </div>
            {readiness.data?.missing?.length > 0 && (
              <div className="readiness-note">
                <strong>Optional improvements</strong>
                <small>
                  Add {readiness.data.missing.join(", ")} for a stronger draft.
                </small>
              </div>
            )}
          </aside>
        </div>
      </main>
    );

  return (
    <main
      className={`page resume-studio-page resume-word-workspace ${mobilePreview ? "show-mobile-preview" : ""} ${aiOpen ? "show-resume-ai" : ""} right-mode-${rightMode}`}
    >
      <section className="surface resume-studio-toolbar">
        <div>
          <span className="section-eyebrow">Resume Studio</span>
          <input
            className="resume-title-input"
            value={resumeTitle}
            aria-label="Resume name"
            disabled={selected?.status === "approved"}
            onChange={(event) => {
              setResumeTitle(event.target.value);
              setSaveState("unsaved");
            }}
          />
          <p>
            Version {selected?.version} · {selected?.status} · changes stay
            inside this resume version.
          </p>
        </div>
        <div className="button-row">
          <button
            className="button secondary"
            onClick={() => {
              setRightMode(null);
              setAiOpen(false);
            }}
          >
            Edit content
          </button>
          <button
            className="button secondary"
            onClick={() => {
              setRightMode("design");
              setAiOpen(false);
            }}
          >
            <Palette size={16} /> Design
          </button>
          <button
            className="button secondary resume-ai-toggle"
            onClick={() => {
              setRightMode("ai");
              setAiOpen(true);
            }}
          >
            <Sparkles size={16} /> AI Writer
          </button>
          <select
            value={selectedId}
            onChange={(e) => navigate(`/app/resume/${e.target.value}/edit`)}
          >
            {resumes.data.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title} · V{item.version}
              </option>
            ))}
          </select>
          <button
            className="button secondary mobile-preview-toggle"
            onClick={() => setMobilePreview((x) => !x)}
          >
            <Eye size={16} />
            {mobilePreview ? "Back to editor" : "Full preview"}
          </button>
          <button
            className="button primary"
            onClick={() => generate.mutate()}
            disabled={generate.isPending}
          >
            <Plus size={16} />
            {generate.isPending
              ? generationStages[generationStage]
              : "New version"}
          </button>
        </div>
      </section>
      {error && (
        <section className="async-state error">
          <p>{apiErrorMessage(error)}</p>
        </section>
      )}
      {selected && draft && (
        <div className="resume-studio-grid">
          <ResumeBlockEditor
            draft={draft}
            update={update}
            setDraft={(updater) => {
              setSaveState("unsaved");
              setDraft(updater);
            }}
            selection={selection}
            inspect={inspect}
            disabled={selected.status === "approved"}
            onAI={openBlockAI}
          />
          <aside className="surface resume-controls legacy-resume-controls">
            <div className="control-heading">
              <div>
                <span>Resume content</span>
                <strong>{selected.title}</strong>
              </div>
              <button
                className="button primary compact"
                disabled={selected.status === "approved" || save.isPending}
                onClick={() => save.mutate()}
              >
                <Save size={14} />
                Save
              </button>
            </div>
            <section className="ai-writer-launchpad">
              <div className="ai-writer-title">
                <span>
                  <Sparkles size={15} />
                </span>
                <div>
                  <strong>Write it with CareerPilot AI</strong>
                  <small>
                    Uses your verified Profile and saved career context.
                  </small>
                </div>
              </div>
              <div className="ai-write-actions">
                <button
                  disabled={
                    regenerate.isPending || selected.status === "approved"
                  }
                  onClick={() => regenerate.mutate("summary")}
                >
                  <Sparkles size={12} />
                  Write summary
                </button>
                <button
                  disabled={
                    regenerate.isPending || selected.status === "approved"
                  }
                  onClick={() => regenerate.mutate("experience")}
                >
                  <Sparkles size={12} />
                  Write experience bullets
                </button>
                <button
                  disabled={
                    regenerate.isPending || selected.status === "approved"
                  }
                  onClick={() => regenerate.mutate("projects")}
                >
                  <Sparkles size={12} />
                  Write project descriptions
                </button>
                <button
                  disabled={
                    regenerate.isPending || selected.status === "approved"
                  }
                  onClick={() => regenerate.mutate("skills")}
                >
                  <Sparkles size={12} />
                  Organize skills
                </button>
              </div>
              {regenerate.isPending && (
                <p className="ai-writing-status">
                  Reviewing your verified information and preparing grounded
                  wording…
                </p>
              )}
              {regenerate.error && (
                <p className="ai-writing-error">
                  {apiErrorMessage(regenerate.error)}
                </p>
              )}
            </section>
            <div className="resume-edit-block template-editor-block">
              <strong>Design</strong>
              <div className="current-template-line">
                <span>{getResumeTemplate(selected.template_id).name}</span>
                <Link to={`/app/resume/templates?resume=${selected.id}`}>
                  Change template
                </Link>
              </div>
              <label>
                Accent color
                <select
                  value={design.accent}
                  onChange={(e) =>
                    setDesign({ ...design, accent: e.target.value })
                  }
                >
                  {[
                    ["#1769d2", "Blue"],
                    ["#17324d", "Navy"],
                    ["#334155", "Slate"],
                    ["#0f766e", "Teal"],
                    ["#171717", "Black"],
                    ["#786c61", "Warm gray"],
                  ].map(([value, name]) => (
                    <option value={value} key={value}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Font pairing
                <select
                  value={design.font}
                  onChange={(e) =>
                    setDesign({ ...design, font: e.target.value })
                  }
                >
                  <option value="professional">Professional Sans</option>
                  <option value="modern">Modern Sans</option>
                  <option value="classic">Classic Serif</option>
                  <option value="editorial">Editorial</option>
                </select>
              </label>
              <label>
                Text size
                <input
                  type="range"
                  min="90"
                  max="110"
                  value={design.textSize}
                  onChange={(e) =>
                    setDesign({ ...design, textSize: Number(e.target.value) })
                  }
                />
              </label>
              <label>
                Line spacing
                <input
                  type="range"
                  min="1.25"
                  max="1.7"
                  step=".05"
                  value={design.lineSpacing}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      lineSpacing: Number(e.target.value),
                    })
                  }
                />
              </label>
              <label>
                Section spacing
                <input
                  type="range"
                  min="10"
                  max="26"
                  value={design.sectionSpacing}
                  onChange={(e) =>
                    setDesign({
                      ...design,
                      sectionSpacing: Number(e.target.value),
                    })
                  }
                />
              </label>
              <small>
                Safe design presets update instantly without calling AI.
              </small>
            </div>
            <label onFocus={() => inspect({ section: "summary" })}>
              Professional summary{" "}
              <QualityMark analysis={analysis.data} section="summary" />
              <textarea
                rows="7"
                value={draft.summary || ""}
                disabled={selected.status === "approved"}
                onChange={(e) => update(["summary"], e.target.value)}
              />
            </label>
            <button
              className="text-action"
              onClick={() => {
                inspect({ section: "summary" });
                askCoach("Improve this summary");
              }}
            >
              <Sparkles size={13} />
              Improve summary with AI
            </button>
            <button
              className="format-action"
              onMouseDown={(event) => {
                event.preventDefault();
                boldSelection(["summary"], draft.summary || "");
              }}
            >
              <strong>B</strong> Bold selected text
            </button>
            <div className="resume-edit-block">
              <strong>Experience bullets</strong>
              {draft.experience.map((item, index) => (
                <div
                  key={`${item.company}-${index}`}
                  onFocus={() =>
                    inspect({ section: "experience", item_index: index })
                  }
                >
                  <small>
                    {item.job_title} · {item.company}{" "}
                    <QualityMark
                      analysis={analysis.data}
                      section="experience"
                      index={index}
                    />
                  </small>
                  {item.bullets.map((bullet, bulletIndex) => (
                    <div className="bullet-editor" key={bulletIndex}>
                      <span>•</span>
                      <textarea
                        rows="3"
                        value={bullet}
                        disabled={selected.status === "approved"}
                        onChange={(e) =>
                          update(
                            ["experience", index, "bullets", bulletIndex],
                            e.target.value,
                          )
                        }
                      />
                      <div className="bullet-tools">
                        <button
                          type="button"
                          title="Bold selected text"
                          onMouseDown={(event) => {
                            event.preventDefault();
                            boldSelection(
                              ["experience", index, "bullets", bulletIndex],
                              bullet,
                            );
                          }}
                        >
                          <strong>B</strong>
                        </button>
                        <button
                          type="button"
                          aria-label="Delete bullet"
                          onClick={() =>
                            update(
                              ["experience", index, "bullets"],
                              item.bullets.filter((_, i) => i !== bulletIndex),
                            )
                          }
                        >
                          <X size={12} />
                        </button>
                      </div>
                    </div>
                  ))}
                  <button
                    type="button"
                    className="add-content-button"
                    onClick={() =>
                      update(
                        ["experience", index, "bullets"],
                        [...item.bullets, ""],
                      )
                    }
                  >
                    <Plus size={12} />
                    Add bullet point
                  </button>
                  <button
                    className="text-action"
                    onClick={() => {
                      inspect({ section: "experience", item_index: index });
                      setAiOpen(true);
                      askCoach(
                        "Suggest stronger resume bullets using only my verified information",
                      );
                    }}
                  >
                    <Sparkles size={12} />
                    Suggest stronger bullets
                  </button>
                </div>
              ))}
            </div>
            <div className="resume-edit-block">
              <strong>Projects</strong>
              {draft.projects.map((item, index) => (
                <label
                  key={`${item.name}-${index}`}
                  onFocus={() =>
                    inspect({ section: "projects", item_index: index })
                  }
                >
                  <small>
                    {item.name}{" "}
                    <QualityMark
                      analysis={analysis.data}
                      section="projects"
                      index={index}
                    />
                  </small>
                  <textarea
                    rows="3"
                    value={item.description || ""}
                    disabled={selected.status === "approved"}
                    onChange={(e) =>
                      update(["projects", index, "description"], e.target.value)
                    }
                  />
                  <button
                    type="button"
                    className="text-action"
                    onClick={() => {
                      inspect({ section: "projects", item_index: index });
                      setAiOpen(true);
                      askCoach(
                        "Improve this project description using only verified project information",
                      );
                    }}
                  >
                    <Sparkles size={12} />
                    Improve project with AI
                  </button>
                  <button
                    type="button"
                    className="format-action"
                    onMouseDown={(event) => {
                      event.preventDefault();
                      boldSelection(
                        ["projects", index, "description"],
                        item.description || "",
                      );
                    }}
                  >
                    <strong>B</strong> Bold selected text
                  </button>
                </label>
              ))}
            </div>
            <div className="resume-edit-block">
              <strong>Skills inclusion</strong>
              {draft.skill_groups.map((group, groupIndex) => (
                <label className="visibility-row" key={group.category}>
                  <input
                    type="checkbox"
                    checked={group.visible !== false}
                    disabled={selected.status === "approved"}
                    onChange={(e) =>
                      update(
                        ["skill_groups", groupIndex, "visible"],
                        e.target.checked,
                      )
                    }
                  />
                  <span>{group.category}</span>
                  <small>{group.items.length}</small>
                </label>
              ))}
            </div>
            <div className="resume-edit-block">
              <strong>Section order & visibility</strong>
              {draft.section_order.map((key, index) => (
                <div
                  className="section-control"
                  key={key}
                  draggable
                  onDragStart={(event) =>
                    event.dataTransfer.setData("text/plain", String(index))
                  }
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={(event) =>
                    moveSectionTo(
                      Number(event.dataTransfer.getData("text/plain")),
                      index,
                    )
                  }
                >
                  <button
                    title="Toggle section"
                    onClick={() => toggleSection(key)}
                    disabled={selected.status === "approved"}
                  >
                    {draft.hidden_sections?.includes(key) ? (
                      <EyeOff size={13} />
                    ) : (
                      <Eye size={13} />
                    )}
                  </button>
                  <span>{sectionNames[key]}</span>
                  <button
                    onClick={() => moveSection(index, -1)}
                    disabled={index === 0 || selected.status === "approved"}
                  >
                    <ArrowUp size={12} />
                  </button>
                  <button
                    onClick={() => moveSection(index, 1)}
                    disabled={
                      index === draft.section_order.length - 1 ||
                      selected.status === "approved"
                    }
                  >
                    <ArrowDown size={12} />
                  </button>
                </div>
              ))}
            </div>
          </aside>
          <section className="resume-preview-workspace">
            <div className="preview-topline">
              <span>Live A4 preview</span>
              <small>Selectable text · print-safe layout</small>
            </div>
            <ResumePreview
              content={draft}
              templateId={selected.template_id}
              design={design}
              onSelect={(next) => {
                inspect(next);
                setRightMode(null);
                setAiOpen(false);
              }}
            />
          </section>
          {rightMode === "design" && (
            <DesignPanel
              selected={selected}
              design={design}
              setDesign={setDesign}
              contextual
            />
          )}
          <aside className="surface resume-inspector copilot-panel">
            <div>
              <button
                className="resume-ai-close"
                onClick={() => {
                  setAiOpen(false);
                  setRightMode("content");
                }}
                aria-label="Close AI writer"
              >
                <X size={16} />
              </button>
              <span className="section-eyebrow">CareerPilot Suggestions</span>
              <small className="ai-panel-mode-label">
                AI Writer · your resume stays visible
              </small>
              <h2>
                {selection.section}{" "}
                {selection.item_index != null
                  ? `· ${selection.item_index + 1}`
                  : ""}
              </h2>
              <p>Contextual guidance for the selected resume content.</p>
            </div>
            {coach.isPending || analysis.isLoading ? (
              <p className="copilot-loading">
                CareerPilot is reviewing this {selection.section}…
              </p>
            ) : (
              selectedAnalysis && (
                <>
                  <span
                    className={`quality-label quality-${selectedAnalysis.quality}`}
                  >
                    {selectedAnalysis.quality.replaceAll("_", " ")}
                  </span>
                  {selectedAnalysis.issues?.[0] && (
                    <div className="copilot-card">
                      <strong>{selectedAnalysis.issues[0].message}</strong>
                      <p>
                        {selectedAnalysis.supported_suggestions?.[0]?.reason}
                      </p>
                    </div>
                  )}
                  {selectedAnalysis.clarification_questions?.[0] && (
                    <div className="copilot-card question-card">
                      <strong>
                        {selectedAnalysis.clarification_questions[0]}
                      </strong>
                      <textarea
                        rows="3"
                        value={answer}
                        onChange={(e) => setAnswer(e.target.value)}
                        placeholder="Answer CareerPilot"
                      />
                      <button
                        className="button primary compact"
                        disabled={!answer.trim() || coach.isPending}
                        onClick={() => {
                          askCoach(
                            selectedAnalysis.clarification_questions[0],
                            answer,
                          );
                          setAnswer("");
                        }}
                      >
                        Use my answer
                      </button>
                    </div>
                  )}
                  {selectedAnalysis.supported_suggestions
                    ?.filter((s) => s.suggestion && !dismissed.includes(s.id))
                    .map((suggestion) => (
                      <div
                        className="copilot-card suggestion-card"
                        key={suggestion.id}
                      >
                        <small>{suggestion.label}</small>
                        <p>{suggestion.suggestion}</p>
                        <em>
                          {suggestion.evidence
                            ?.map((e) =>
                              e.source_type.replace(
                                "career_knowledge",
                                "saved context",
                              ),
                            )
                            .join(" · ")}
                        </em>
                        <div className="suggestion-actions">
                          <button
                            disabled={
                              suggestion.requires_confirmation ||
                              selected.status === "approved"
                            }
                            onClick={() =>
                              applySuggestion.mutate({ suggestion })
                            }
                          >
                            <Check size={13} />
                            Use this
                          </button>
                          <button
                            onClick={() => {
                              const edited = window.prompt(
                                "Edit before applying",
                                suggestion.suggestion,
                              );
                              if (edited)
                                applySuggestion.mutate({
                                  suggestion,
                                  edited_text: edited,
                                });
                            }}
                          >
                            Edit
                          </button>
                          <button
                            onClick={() =>
                              setDismissed((x) => [...x, suggestion.id])
                            }
                          >
                            <X size={12} />
                            Not accurate
                          </button>
                          <button
                            onClick={() =>
                              askCoach(
                                `Generate another ${selection.section} option`,
                              )
                            }
                          >
                            <RefreshCw size={12} />
                            Generate another
                          </button>
                        </div>
                        {suggestion.requires_confirmation && (
                          <small>
                            Confirm this saved context in your answer before
                            applying.
                          </small>
                        )}
                      </div>
                    ))}
                </>
              )
            )}
            <button
              className="button secondary"
              disabled={coach.isPending}
              onClick={() => askCoach("What could I improve here?")}
            >
              <Sparkles size={14} />
              Analyze selected section
            </button>
            <p className="profile-boundary">
              Suggestions update this Resume version only. New facts need
              separate Profile approval.
            </p>
            <button
              className="button secondary"
              onClick={() => approve.mutate(selected.id)}
              disabled={selected.status === "approved"}
            >
              <Check size={15} />
              {selected.status === "approved"
                ? "Approved"
                : selected.status === "draft"
                  ? "Submit for review"
                  : "Approve resume"}
            </button>
            <button
              className="button primary"
              onClick={() => exportPdf.mutate()}
              disabled={exportPdf.isPending}
            >
              <Download size={15} />
              {exportPdf.isPending ? "Rendering PDF…" : "Export PDF"}
            </button>
          </aside>
          <section className="resume-save-dock">
            <div>
              <strong>
                {saveState === "saving"
                  ? "Saving…"
                  : saveState === "unsaved"
                    ? "Unsaved changes"
                    : "Saved"}
              </strong>
              <small>Changes apply only to this Resume version.</small>
            </div>
            <label>
              PDF filename
              <input
                value={pdfFilename}
                onChange={(event) => setPdfFilename(event.target.value)}
              />
            </label>
            <button
              className="button secondary"
              disabled={save.isPending || saveState === "saved"}
              onClick={() => save.mutate()}
            >
              <Save size={15} />
              Save changes
            </button>
            <button
              className="button primary"
              disabled={save.isPending}
              onClick={async () => {
                await save.mutateAsync();
                navigate("/app/resume");
              }}
            >
              <Check size={15} />
              Save & close
            </button>
          </section>
        </div>
      )}
    </main>
  );
}

function DesignPanel({ selected, design, setDesign, contextual = false }) {
  const updateDesign = (key, value) => setDesign({ ...design, [key]: value });
  return (
    <aside
      className={`surface resume-design-panel ${contextual ? "context-design-panel" : ""}`}
    >
      <header>
        <span>01</span>
        <div>
          <strong>Design & formatting</strong>
          <small>Style the document while keeping it readable.</small>
        </div>
      </header>
      <div className="design-control-group">
        <label>Template</label>
        <Link
          className="design-template-button"
          to={`/app/resume/templates?resume=${selected.id}`}
        >
          <span>{getResumeTemplate(selected.template_id).name}</span>
          <strong>Change</strong>
        </Link>
      </div>
      <div className="design-control-group">
        <label>Accent color</label>
        <div className="builder-color-grid">
          {[
            "#1769d2",
            "#17324d",
            "#334155",
            "#0f766e",
            "#7c3aed",
            "#9f1239",
            "#9a3412",
            "#171717",
          ].map((color) => (
            <button
              key={color}
              className={design.accent === color ? "active" : ""}
              style={{ "--color": color }}
              onClick={() => updateDesign("accent", color)}
              aria-label={`Use ${color}`}
            >
              {design.accent === color && <Check size={11} />}
            </button>
          ))}
        </div>
        <input
          type="color"
          value={design.accent}
          onChange={(event) => updateDesign("accent", event.target.value)}
        />
      </div>
      <div className="design-control-group">
        <label>Font pairing</label>
        <select
          value={design.font}
          onChange={(event) => updateDesign("font", event.target.value)}
        >
          <option value="professional">Professional Sans</option>
          <option value="modern">Modern Sans</option>
          <option value="classic">Classic Serif</option>
          <option value="editorial">Editorial</option>
        </select>
      </div>
      <div className="design-control-group range-control">
        <label>
          <span>Text size</span>
          <b>{design.textSize}%</b>
        </label>
        <input
          type="range"
          min="88"
          max="112"
          value={design.textSize}
          onChange={(event) =>
            updateDesign("textSize", Number(event.target.value))
          }
        />
      </div>
      <div className="design-control-group range-control">
        <label>
          <span>Page margins</span>
          <b>{design.pageMargins}mm</b>
        </label>
        <input
          type="range"
          min="10"
          max="24"
          value={design.pageMargins}
          onChange={(event) =>
            updateDesign("pageMargins", Number(event.target.value))
          }
        />
      </div>
      <div className="design-control-group range-control">
        <label>
          <span>Line spacing</span>
          <b>{design.lineSpacing}</b>
        </label>
        <input
          type="range"
          min="1.2"
          max="1.8"
          step=".05"
          value={design.lineSpacing}
          onChange={(event) =>
            updateDesign("lineSpacing", Number(event.target.value))
          }
        />
      </div>
      <div className="design-control-group range-control">
        <label>
          <span>Section spacing</span>
          <b>{design.sectionSpacing}px</b>
        </label>
        <input
          type="range"
          min="8"
          max="30"
          value={design.sectionSpacing}
          onChange={(event) =>
            updateDesign("sectionSpacing", Number(event.target.value))
          }
        />
      </div>
      <div className="design-tip">
        <strong>Drag sections</strong>
        <p>
          Open Content on the right and drag section rows to reorder the
          document.
        </p>
      </div>
    </aside>
  );
}

function QualityMark({ analysis, section, index = null }) {
  const item = analysis?.analyses?.find(
    (x) => x.section === section && (x.item_index ?? null) === index,
  );
  if (!item) return null;
  const label =
    item.quality === "insufficient_information"
      ? "Needs detail"
      : item.quality.replaceAll("_", " ");
  return (
    <span className={`inline-quality quality-${item.quality}`}>{label}</span>
  );
}
