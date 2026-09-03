import { ExternalLink } from "lucide-react";

export const templateList = [
  {
    id: "careerpilot_classic",
    name: "CareerPilot Classic",
    description: "A timeless, highly readable format for almost any role.",
    categories: ["ats", "professional"],
    styles: ["professional", "corporate"],
    layouts: ["one_column", "multi_page"],
    careerLevels: ["mid", "senior"],
    industries: ["business", "finance", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "clear_ats",
    name: "Clear ATS",
    description:
      "Direct structure and strong headings built for clean parsing.",
    categories: ["ats", "simple"],
    styles: ["minimal", "professional"],
    layouts: ["one_column", "one_page"],
    careerLevels: ["student", "entry", "mid"],
    industries: ["general", "healthcare", "education"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "horizon",
    name: "Horizon",
    description: "A confident modern header with a restrained blue accent.",
    categories: ["modern", "professional"],
    styles: ["modern", "professional"],
    layouts: ["one_column", "multi_page"],
    careerLevels: ["entry", "mid"],
    industries: ["business", "education", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "nova_tech",
    name: "Nova Tech",
    description:
      "Project-forward structure for software and engineering careers.",
    categories: ["tech", "modern", "two_column"],
    styles: ["modern", "creative"],
    layouts: ["two_column", "one_page"],
    careerLevels: ["entry", "mid"],
    industries: ["technology", "engineering"],
    tier: "free",
    supportsResume: true,
    supportsCV: false,
  },
  {
    id: "executive_line",
    name: "Executive Line",
    description: "Experience-led hierarchy with composed executive typography.",
    categories: ["executive", "professional"],
    styles: ["elegant", "corporate"],
    layouts: ["one_column", "multi_page"],
    careerLevels: ["senior"],
    industries: ["business", "finance", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "minimal_edge",
    name: "Minimal Edge",
    description:
      "Editorial whitespace and refined typography for focused stories.",
    categories: ["simple", "professional"],
    styles: ["minimal", "elegant"],
    layouts: ["one_column", "one_page"],
    careerLevels: ["mid", "senior"],
    industries: ["business", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "dual_focus",
    name: "Dual Focus",
    description: "A balanced two-column layout with a logical reading order.",
    categories: ["two_column", "modern"],
    styles: ["modern", "professional"],
    layouts: ["two_column", "multi_page"],
    careerLevels: ["mid", "senior"],
    industries: ["technology", "engineering", "business"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "graduate_launch",
    name: "Graduate Launch",
    description:
      "Education and projects take priority for early-career candidates.",
    categories: ["entry_level", "modern"],
    styles: ["modern", "minimal"],
    layouts: ["one_column", "one_page"],
    careerLevels: ["student", "entry"],
    industries: ["technology", "education", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: false,
  },
  {
    id: "slate_column",
    name: "Slate Column",
    description: "A compact sidebar makes skills and education easy to scan.",
    categories: ["two_column", "professional"],
    styles: ["corporate", "modern"],
    layouts: ["two_column", "one_page"],
    careerLevels: ["entry", "mid"],
    industries: ["business", "finance", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "atlas",
    name: "Atlas",
    description:
      "A bold nameplate and structured timeline for experienced candidates.",
    categories: ["professional", "executive"],
    styles: ["corporate", "professional"],
    layouts: ["one_column", "multi_page"],
    careerLevels: ["mid", "senior"],
    industries: ["business", "engineering", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "cedar",
    name: "Cedar",
    description:
      "Warm, understated styling for education and people-focused roles.",
    categories: ["simple", "professional"],
    styles: ["elegant", "minimal"],
    layouts: ["one_column", "multi_page"],
    careerLevels: ["entry", "mid", "senior"],
    industries: ["education", "healthcare", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "pulse",
    name: "Pulse",
    description:
      "Energetic section markers for product, technology, and startup roles.",
    categories: ["modern", "tech"],
    styles: ["modern", "creative"],
    layouts: ["one_column", "one_page"],
    careerLevels: ["entry", "mid"],
    industries: ["technology", "business"],
    tier: "free",
    supportsResume: true,
    supportsCV: false,
  },
  {
    id: "academic_crest",
    name: "Academic Crest",
    description:
      "A publication-friendly classic hierarchy for research and academia.",
    categories: ["professional", "simple"],
    styles: ["elegant", "professional"],
    layouts: ["one_column", "multi_page"],
    careerLevels: ["student", "mid", "senior"],
    industries: ["education", "healthcare"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
  {
    id: "metro",
    name: "Metro",
    description:
      "Geometric two-column composition with crisp information grouping.",
    categories: ["two_column", "creative", "modern"],
    styles: ["creative", "modern"],
    layouts: ["two_column", "one_page"],
    careerLevels: ["entry", "mid"],
    industries: ["technology", "engineering", "general"],
    tier: "free",
    supportsResume: true,
    supportsCV: false,
  },
  {
    id: "keystone",
    name: "Keystone",
    description:
      "A firm, balanced layout designed for operations and leadership.",
    categories: ["executive", "ats"],
    styles: ["corporate", "professional"],
    layouts: ["one_column", "multi_page"],
    careerLevels: ["mid", "senior"],
    industries: ["business", "finance", "engineering"],
    tier: "free",
    supportsResume: true,
    supportsCV: true,
  },
];
export const resumeTemplates = Object.fromEntries(
  templateList.map((item) => [item.id, item]),
);
const legacyTemplates = {
  ats_classic: "careerpilot_classic",
  ats_modern: "horizon",
  premium_minimal: "minimal_edge",
};
export const getResumeTemplate = (id) =>
  resumeTemplates[legacyTemplates[id] || id] ||
  resumeTemplates.careerpilot_classic;
export const demoResume = {
  header: {
    full_name: "Jordan Lee",
    professional_title: "Product-minded Software Engineer",
    email: "jordan.lee@example.com",
    phone: "+1 555 0142",
    location: "Austin, TX",
    linkedin: "https://linkedin.com",
    github: "https://github.com",
  },
  summary:
    "Software engineer focused on reliable web products, accessible interfaces, and thoughtful collaboration across product and engineering teams.",
  experience: [
    {
      company: "Northstar Labs",
      job_title: "Software Engineer",
      location: "Austin, TX",
      start_date: "2022",
      end_date: "Present",
      bullets: [
        "Built and maintained customer-facing product workflows with a cross-functional team.",
        "Improved application reliability through testing, monitoring, and clear technical documentation.",
      ],
    },
    {
      company: "Brightworks",
      job_title: "Engineering Intern",
      start_date: "2021",
      end_date: "2022",
      bullets: [
        "Supported frontend delivery and resolved usability issues across responsive experiences.",
      ],
    },
  ],
  education: [
    {
      institution: "Central State University",
      degree: "B.S.",
      field_of_study: "Computer Science",
      start_date: "2018",
      end_date: "2022",
    },
  ],
  projects: [
    {
      name: "Open Source Accessibility Toolkit",
      role: "Creator",
      description:
        "A reusable set of tested interface patterns for accessible product teams.",
      technologies: ["React", "TypeScript", "Testing"],
    },
  ],
  skill_groups: [
    { category: "Engineering", items: ["JavaScript", "React", "APIs", "SQL"] },
    {
      category: "Ways of working",
      items: ["Product collaboration", "Testing", "Documentation"],
    },
  ],
  section_order: ["summary", "experience", "projects", "education", "skills"],
  hidden_sections: [],
};
const dateRange = (item) =>
  [item.start_date, item.end_date || (item.is_current ? "Present" : null)]
    .filter(Boolean)
    .join(" – ");
const visible = (content, section) =>
  !content.hidden_sections?.includes(section);
function Contact({ header = {} }) {
  const links = [
    [header.linkedin, "LinkedIn"],
    [header.github, "GitHub"],
    [header.portfolio, "Portfolio"],
  ].filter(([url]) => url);
  return (
    <div className="resume-contact-block">
      <p className="resume-contact">
        {[header.email, header.phone, header.location]
          .filter(Boolean)
          .join(" · ")}
      </p>
      {links.length > 0 && (
        <p className="resume-links">
          {links.map(([url, label]) => (
            <a key={label} href={url} target="_blank" rel="noreferrer">
              {label}
              <ExternalLink size={7} />
            </a>
          ))}
        </p>
      )}
    </div>
  );
}
function Section({ name, children, onSelect }) {
  return (
    <section
      className={`resume-section section-${name}`}
      onClick={() => onSelect?.({ section: name })}
    >
      <h2>
        {
          {
            summary: "Profile",
            experience: "Experience",
            education: "Education",
            projects: "Selected Projects",
            skills: "Expertise",
          }[name]
        }
      </h2>
      {children}
    </section>
  );
}
function InlineText({ text = "" }) {
  return text
    .replace(/^#{1,6}\s*/, "")
    .split(/(\*\*[^*]+\*\*|__[^_]+__|\[[^\]]+]\(https?:\/\/[^)]+\))/g)
    .filter(Boolean)
    .map((part, index) =>
      part.startsWith("**") && part.endsWith("**") ? (
        <strong key={index}>{part.slice(2, -2)}</strong>
      ) : part.startsWith("__") && part.endsWith("__") ? (
        <em key={index}>{part.slice(2, -2)}</em>
      ) : /^\[[^\]]+]\(https?:\/\//.test(part) ? (
        <a key={index} href={part.match(/\(([^)]+)\)$/)?.[1]}>
          {part.match(/^\[([^\]]+)]/)?.[1]}
        </a>
      ) : (
        <span key={index}>{part}</span>
      ),
    );
}
function RichText({ text = "" }) {
  const lines = text
    .replace(/\s+\*\s+(?=[A-Z])/g, "\n* ")
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
  const bullets = lines.filter((line) => /^[-*•]\s+/.test(line));
  const numbered = lines.filter((line) => /^\d+[.)]\s+/.test(line));
  const prose = lines.filter(
    (line) => !/^[-*•]\s+/.test(line) && !/^\d+[.)]\s+/.test(line),
  );
  return (
    <>
      {prose.map((line, index) => (
        <p key={`p-${index}`}>
          <InlineText text={line} />
        </p>
      ))}
      {bullets.length > 0 && (
        <ul>
          {bullets.map((line, index) => (
            <li key={`b-${index}`}>
              <InlineText text={line.replace(/^[-*•]\s+/, "")} />
            </li>
          ))}
        </ul>
      )}
      {numbered.length > 0 && (
        <ol>
          {numbered.map((line, index) => (
            <li key={`n-${index}`}>
              <InlineText text={line.replace(/^\d+[.)]\s+/, "")} />
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
function Sections({ content, templateId, onSelect }) {
  const blocks = {
    summary: content.summary && (
      <Section name="summary" onSelect={onSelect}>
        <RichText text={content.summary} />
      </Section>
    ),
    experience: content.experience?.length > 0 && (
      <Section name="experience" onSelect={onSelect}>
        {content.experience
          .filter((x) => x.visible !== false)
          .map((item, index) => (
            <article key={`${item.company}-${index}`}>
              <div className="resume-row">
                <h3>
                  {item.job_title}
                  <span> · {item.company}</span>
                </h3>
                <time>{dateRange(item)}</time>
              </div>
              {item.location && <small>{item.location}</small>}
              {!!item.bullets?.length && (
                <ul>
                  {item.bullets.map((bullet, i) => (
                    <li key={i}>
                      <InlineText text={bullet} />
                    </li>
                  ))}
                </ul>
              )}
            </article>
          ))}
      </Section>
    ),
    education: content.education?.length > 0 && (
      <Section name="education" onSelect={onSelect}>
        {content.education
          .filter((x) => x.visible !== false)
          .map((item, index) => (
            <article key={`${item.institution}-${index}`}>
              <div className="resume-row">
                <h3>
                  {[item.degree, item.field_of_study]
                    .filter(Boolean)
                    .join(" in ")}
                </h3>
                <time>{dateRange(item)}</time>
              </div>
              <p>{item.institution}</p>
              {item.grade && <small>{item.grade}</small>}
              {item.description && <RichText text={item.description} />}
            </article>
          ))}
      </Section>
    ),
    projects: content.projects?.length > 0 && (
      <Section name="projects" onSelect={onSelect}>
        {content.projects
          .filter((x) => x.visible !== false)
          .map((item, index) => (
            <article key={`${item.name}-${index}`}>
              <h3>
                {item.name}
                {item.role && <span> · {item.role}</span>}
              </h3>
              {item.description && <RichText text={item.description} />}
              {!!item.bullets?.length && (
                <ul>
                  {item.bullets.map((bullet, index) => (
                    <li key={index}>
                      <InlineText text={bullet} />
                    </li>
                  ))}
                </ul>
              )}
              {!!item.technologies?.length && (
                <small className="tech-list">
                  {item.technologies.join(" · ")}
                </small>
              )}
              {(item.project_url || item.repository_url) && (
                <p className="resume-links">
                  {item.project_url && <a href={item.project_url}>Project</a>}
                  {item.repository_url && (
                    <a href={item.repository_url}>Repository</a>
                  )}
                </p>
              )}
            </article>
          ))}
      </Section>
    ),
    skills: content.skill_groups?.length > 0 && (
      <Section name="skills" onSelect={onSelect}>
        {content.skill_groups
          .filter((x) => x.visible !== false)
          .map((group) => (
            <p className="skill-line" key={group.category}>
              <strong>{group.category}</strong>
              {group.items.join(" · ")}
            </p>
          ))}
      </Section>
    ),
  };
  const order = content.section_order || Object.keys(blocks);
  return (
    <div className="resume-sections">
      {order.map((key) =>
        visible(content, key) && blocks[key] ? (
          <div key={key} className={`block-${key}`}>
            {blocks[key]}
          </div>
        ) : null,
      )}
    </div>
  );
}
export function ResumePreview({
  content = demoResume,
  templateId = "careerpilot_classic",
  design = {},
  demo = false,
  onSelect,
}) {
  const template = getResumeTemplate(templateId);
  const style = {
    "--resume-accent": design.accent || undefined,
    "--resume-scale": design.textSize
      ? String(design.textSize / 100)
      : undefined,
    "--resume-leading": design.lineSpacing || undefined,
    "--resume-section-gap": design.sectionSpacing
      ? `${design.sectionSpacing}px`
      : undefined,
    "--resume-margin": design.pageMargins
      ? `${design.pageMargins}mm`
      : undefined,
  };
  return (
    <div
      className={`resume-document template-${template.id} font-${design.font || "professional"}`}
      style={style}
      data-demo={demo ? "Template demo" : undefined}
    >
      <header>
        <div className="resume-identity">
          <h1>{content.header?.full_name || "Your Name"}</h1>
          <strong>
            {content.header?.professional_title || "Professional title"}
          </strong>
        </div>
        <Contact header={content.header} />
      </header>
      <Sections
        content={content}
        templateId={template.id}
        onSelect={onSelect}
      />
    </div>
  );
}
