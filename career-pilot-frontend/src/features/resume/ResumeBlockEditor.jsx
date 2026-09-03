import {
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  GripVertical,
  Plus,
  Trash2,
} from "lucide-react";
import RichTextField from "./RichTextField";

const names = {
  header: "Header",
  summary: "Professional Summary",
  experience: "Experience",
  education: "Education",
  projects: "Projects",
  skills: "Skills",
};
const input = (value, onChange, placeholder) => (
  <input
    value={value || ""}
    onChange={(e) => onChange(e.target.value)}
    placeholder={placeholder}
  />
);

function ReorderButtons({ index, length, move }) {
  return (
    <span className="reorder-buttons">
      <button
        type="button"
        disabled={!index}
        onClick={() => move(index, index - 1)}
      >
        <ChevronUp size={12} />
      </button>
      <button
        type="button"
        disabled={index === length - 1}
        onClick={() => move(index, index + 1)}
      >
        <ChevronDown size={12} />
      </button>
    </span>
  );
}

export default function ResumeBlockEditor({
  draft,
  update,
  setDraft,
  selection,
  inspect,
  disabled,
  onAI,
}) {
  const order = draft.section_order || [
    "summary",
    "experience",
    "projects",
    "education",
    "skills",
  ];
  const moveArray = (path, from, to) =>
    setDraft((current) => {
      const next = structuredClone(current);
      let rows = next;
      path.forEach((key) => {
        rows = rows[key];
      });
      const [row] = rows.splice(from, 1);
      rows.splice(to, 0, row);
      return next;
    });
  const moveSection = (from, to) =>
    setDraft((current) => {
      const next = structuredClone(current);
      const rows = [...next.section_order];
      const [row] = rows.splice(from, 1);
      rows.splice(to, 0, row);
      next.section_order = rows;
      return next;
    });
  const toggle = (key) =>
    setDraft((current) => ({
      ...current,
      hidden_sections: current.hidden_sections?.includes(key)
        ? current.hidden_sections.filter((x) => x !== key)
        : [...(current.hidden_sections || []), key],
    }));
  const selected = (key) => selection.section === key;
  const field = (path, value, placeholder) =>
    input(value, (next) => update(path, next), placeholder);
  return (
    <aside className="surface resume-block-editor">
      <header>
        <div>
          <strong>Resume blocks</strong>
          <small>Click a block to edit. Drag sections to reorder.</small>
        </div>
      </header>
      <div className="block-list">
        <section
          className={`editor-block fixed-block ${selected("header") ? "selected" : ""}`}
          onClick={() => inspect({ section: "header" })}
        >
          <div className="editor-block-heading">
            <GripVertical size={15} />
            <strong>Header</strong>
            <span>Fixed</span>
          </div>
        </section>
        {order.map((key, index) => (
          <section
            key={key}
            className={`editor-block ${selected(key) ? "selected" : ""}`}
            onClick={() => inspect({ section: key })}
            draggable={!disabled}
            onDragStart={(e) =>
              e.dataTransfer.setData("text/resume-section", String(index))
            }
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) =>
              moveSection(
                Number(e.dataTransfer.getData("text/resume-section")),
                index,
              )
            }
          >
            <div className="editor-block-heading">
              <GripVertical size={15} />
              <strong>{names[key] || key}</strong>
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  toggle(key);
                }}
              >
                {draft.hidden_sections?.includes(key) ? (
                  <EyeOff size={14} />
                ) : (
                  <Eye size={14} />
                )}
              </button>
            </div>
          </section>
        ))}
      </div>
      <div className="selected-block-editor">
        {selection.section === "header" && (
          <fieldset>
            <legend>Resume header</legend>
            <div className="field-grid">
              {field(
                ["header", "full_name"],
                draft.header.full_name,
                "Full name",
              )}
              {field(
                ["header", "professional_title"],
                draft.header.professional_title,
                "Professional title",
              )}
              {field(["header", "email"], draft.header.email, "Email")}
              {field(["header", "phone"], draft.header.phone, "Phone")}
              {field(["header", "location"], draft.header.location, "Location")}
              {field(["header", "linkedin"], draft.header.linkedin, "LinkedIn")}
              {field(["header", "github"], draft.header.github, "GitHub")}
              {field(
                ["header", "portfolio"],
                draft.header.portfolio,
                "Portfolio",
              )}
            </div>
          </fieldset>
        )}
        {selection.section === "summary" && (
          <>
            <RichTextField
              value={draft.summary || ""}
              disabled={disabled}
              onChange={(value) => update(["summary"], value)}
              ariaLabel="Professional summary"
            />
            <BlockAI
              onAI={onAI}
              actions={["Improve", "Shorten", "Make more technical"]}
            />
          </>
        )}
        {selection.section === "experience" &&
          draft.experience.map((item, i) => (
            <fieldset
              key={i}
              onFocus={() => inspect({ section: "experience", item_index: i })}
            >
              <legend>Experience {i + 1}</legend>
              <div className="field-grid">
                {field(["experience", i, "job_title"], item.job_title, "Role")}
                {field(["experience", i, "company"], item.company, "Company")}
                {field(
                  ["experience", i, "location"],
                  item.location,
                  "Location",
                )}
                {field(
                  ["experience", i, "start_date"],
                  item.start_date,
                  "Start date",
                )}
                {field(
                  ["experience", i, "end_date"],
                  item.end_date,
                  "End date",
                )}
              </div>
              <label>Bullets</label>
              {item.bullets.map((bullet, b) => (
                <div className="compact-list-row" key={b}>
                  <GripVertical size={13} />
                  <RichTextField
                    value={bullet}
                    disabled={disabled}
                    onChange={(value) =>
                      update(["experience", i, "bullets", b], value)
                    }
                    ariaLabel={`Experience ${i + 1} bullet ${b + 1}`}
                  />
                  <ReorderButtons
                    index={b}
                    length={item.bullets.length}
                    move={(from, to) =>
                      moveArray(["experience", i, "bullets"], from, to)
                    }
                  />
                  <button
                    type="button"
                    onClick={() =>
                      update(
                        ["experience", i, "bullets"],
                        item.bullets.filter((_, x) => x !== b),
                      )
                    }
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="add-content-button"
                onClick={() =>
                  update(["experience", i, "bullets"], [...item.bullets, ""])
                }
              >
                <Plus size={13} />
                Add bullet
              </button>
              <BlockAI
                onAI={onAI}
                actions={[
                  "Suggest bullets",
                  "Make more technical",
                  "Find missing details",
                ]}
              />
            </fieldset>
          ))}
        {selection.section === "education" &&
          draft.education.map((item, i) => (
            <fieldset key={i}>
              <legend>Education {i + 1}</legend>
              <div className="field-grid">
                {field(
                  ["education", i, "institution"],
                  item.institution,
                  "Institution",
                )}
                {field(["education", i, "degree"], item.degree, "Degree")}
                {field(
                  ["education", i, "field_of_study"],
                  item.field_of_study,
                  "Field",
                )}
                {field(
                  ["education", i, "start_date"],
                  item.start_date,
                  "Start date",
                )}
                {field(["education", i, "end_date"], item.end_date, "End date")}
                {field(["education", i, "grade"], item.grade, "Grade")}
              </div>
              <RichTextField
                value={item.description || ""}
                disabled={disabled}
                onChange={(value) =>
                  update(["education", i, "description"], value)
                }
                ariaLabel="Education highlights"
              />
              <BlockAI
                onAI={onAI}
                actions={[
                  "Improve presentation",
                  "Suggest academic highlights",
                ]}
              />
            </fieldset>
          ))}
        {selection.section === "projects" &&
          draft.projects.map((item, i) => (
            <fieldset key={i}>
              <legend>Project {i + 1}</legend>
              <div className="field-grid">
                {field(["projects", i, "name"], item.name, "Project name")}
                {field(["projects", i, "role"], item.role, "Role")}
                {field(
                  ["projects", i, "project_url"],
                  item.project_url,
                  "Project URL",
                )}
                {field(
                  ["projects", i, "repository_url"],
                  item.repository_url,
                  "Repository URL",
                )}
              </div>
              <RichTextField
                value={item.description || ""}
                disabled={disabled}
                onChange={(value) =>
                  update(["projects", i, "description"], value)
                }
                ariaLabel="Project description"
              />
              <label>Project bullets</label>
              {(item.bullets || []).map((bullet, b) => (
                <div className="compact-list-row" key={b}>
                  <GripVertical size={13} />
                  <RichTextField
                    value={bullet}
                    disabled={disabled}
                    onChange={(value) =>
                      update(["projects", i, "bullets", b], value)
                    }
                    ariaLabel={`Project ${i + 1} bullet ${b + 1}`}
                  />
                  <ReorderButtons
                    index={b}
                    length={item.bullets.length}
                    move={(from, to) =>
                      moveArray(["projects", i, "bullets"], from, to)
                    }
                  />
                  <button
                    type="button"
                    onClick={() =>
                      update(
                        ["projects", i, "bullets"],
                        item.bullets.filter((_, x) => x !== b),
                      )
                    }
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
              <button
                type="button"
                className="add-content-button"
                onClick={() =>
                  update(
                    ["projects", i, "bullets"],
                    [...(item.bullets || []), ""],
                  )
                }
              >
                <Plus size={13} />
                Add project bullet
              </button>
              <label>Technologies</label>
              <input
                value={item.technologies?.join(", ") || ""}
                onChange={(e) =>
                  update(
                    ["projects", i, "technologies"],
                    e.target.value
                      .split(",")
                      .map((x) => x.trim())
                      .filter(Boolean),
                  )
                }
              />
              <BlockAI
                onAI={onAI}
                actions={[
                  "Improve description",
                  "Suggest resume bullets",
                  "Highlight technical contribution",
                ]}
              />
            </fieldset>
          ))}
        {selection.section === "skills" && (
          <>
            {draft.skill_groups.map((group, g) => (
              <fieldset key={g}>
                <legend>Skill group {g + 1}</legend>
                {field(
                  ["skill_groups", g, "category"],
                  group.category,
                  "Group name",
                )}
                <div className="skill-chip-editor">
                  {group.items.map((skill, s) => (
                    <span key={`${skill}-${s}`}>
                      <button
                        type="button"
                        disabled={!s}
                        onClick={() =>
                          moveArray(["skill_groups", g, "items"], s, s - 1)
                        }
                      >
                        ‹
                      </button>
                      {skill}
                      <button
                        type="button"
                        disabled={s === group.items.length - 1}
                        onClick={() =>
                          moveArray(["skill_groups", g, "items"], s, s + 1)
                        }
                      >
                        ›
                      </button>
                      <button
                        type="button"
                        onClick={() =>
                          update(
                            ["skill_groups", g, "items"],
                            group.items.filter((_, x) => x !== s),
                          )
                        }
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
                <input
                  placeholder="Add skill and press Enter"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.currentTarget.value.trim()) {
                      e.preventDefault();
                      update(
                        ["skill_groups", g, "items"],
                        [...group.items, e.currentTarget.value.trim()],
                      );
                      e.currentTarget.value = "";
                    }
                  }}
                />
                <ReorderButtons
                  index={g}
                  length={draft.skill_groups.length}
                  move={(from, to) => moveArray(["skill_groups"], from, to)}
                />
              </fieldset>
            ))}
            <button
              type="button"
              className="add-content-button"
              onClick={() =>
                setDraft((current) => ({
                  ...current,
                  skill_groups: [
                    ...current.skill_groups,
                    { category: "New group", items: [], visible: true },
                  ],
                }))
              }
            >
              <Plus size={13} />
              Add skill group
            </button>
            <BlockAI
              onAI={onAI}
              actions={[
                "Organize",
                "Suggest verified skills",
                "Detect duplicates",
              ]}
            />
          </>
        )}
      </div>
    </aside>
  );
}

function BlockAI({ onAI, actions }) {
  return (
    <div className="block-ai-actions">
      {actions.map((action) => (
        <button type="button" key={action} onClick={() => onAI(action)}>
          {action}
        </button>
      ))}
    </div>
  );
}
