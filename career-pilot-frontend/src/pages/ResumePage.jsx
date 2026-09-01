import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Download, Plus, Save } from "lucide-react";
import { apiErrorMessage, careerApi } from "../services/careerApi";

export default function ResumePage() {
  const client = useQueryClient();
  const [selectedId, setSelectedId] = useState("");
  const [summary, setSummary] = useState("");
  const resumes = useQuery({
    queryKey: ["resumes"],
    queryFn: careerApi.listResumes,
  });
  const selected =
    resumes.data?.find((item) => item.id === selectedId) || resumes.data?.[0];
  useEffect(() => {
    if (selected) {
      setSelectedId(selected.id);
      setSummary(selected.content.summary || "");
    }
  }, [selected?.id]);
  const refresh = () => client.invalidateQueries({ queryKey: ["resumes"] });
  const generate = useMutation({
    mutationFn: () =>
      careerApi.generateResume({
        title: `Resume V${(resumes.data?.length || 0) + 1}`,
      }),
    onSuccess: async (created) => {
      setSelectedId(created.id);
      await refresh();
    },
  });
  const save = useMutation({
    mutationFn: () =>
      careerApi.updateResume(selected.id, {
        content: { ...selected.content, summary },
      }),
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
  const content = selected?.content;
  return (
    <main className="page resume-studio-page">
      <section className="surface resume-studio-toolbar">
        <div>
          <span className="section-eyebrow">Resume Studio</span>
          <h1>Verified resume workspace</h1>
          <p>
            Every version is built from your saved Career Profile and remains
            independently editable.
          </p>
        </div>
        <div className="button-row">
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {resumes.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.title} · {item.status}
              </option>
            ))}
          </select>
          <button
            className="button primary"
            onClick={() => generate.mutate()}
            disabled={generate.isPending || resumes.isLoading}
          >
            <Plus size={16} />
            {generate.isPending ? "Building resume…" : "New version"}
          </button>
        </div>
      </section>
      {resumes.error && (
        <section className="async-state error">
          <p>{apiErrorMessage(resumes.error)}</p>
        </section>
      )}
      {generate.error && (
        <section className="async-state error">
          <p>{apiErrorMessage(generate.error)}</p>
        </section>
      )}
      {selected && (
        <div className="resume-studio-grid">
          <aside className="surface resume-controls">
            <h2>Content</h2>
            <label>
              Professional summary
              <textarea
                rows="9"
                value={summary}
                onChange={(e) => setSummary(e.target.value)}
              />
            </label>
            <button className="button primary" onClick={() => save.mutate()}>
              <Save size={15} />
              Save wording
            </button>
            {["summary", "experience", "projects", "skills"].map((section) => (
              <button
                key={section}
                className="button secondary"
                disabled={
                  selected.status === "approved" || regenerate.isPending
                }
                onClick={() => regenerate.mutate(section)}
              >
                Regenerate {section}
              </button>
            ))}
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
            <button className="button secondary" onClick={() => window.print()}>
              <Download size={15} />
              Export PDF
            </button>
          </aside>
          <article className="resume-document ats-template" id="resume-print">
            <header>
              <h1>{content.header?.name}</h1>
              <strong>{content.header?.title}</strong>
              <p>
                {[
                  content.header?.email,
                  content.header?.phone,
                  content.header?.city,
                  content.header?.country,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </header>
            {summary && (
              <section>
                <h2>Professional Summary</h2>
                <p>{summary}</p>
              </section>
            )}{" "}
            {!!content.experience?.length && (
              <section>
                <h2>Experience</h2>
                {content.experience.map((item, index) => (
                  <div key={`${item.company}-${index}`}>
                    <h3>
                      {item.job_title} · {item.company}
                    </h3>
                    <small>
                      {[
                        item.start_date,
                        item.end_date || (item.is_current ? "Present" : null),
                        item.location,
                      ]
                        .filter(Boolean)
                        .join(" — ")}
                    </small>
                    {item.bullets?.map((bullet) => (
                      <p key={bullet}>• {bullet}</p>
                    ))}
                  </div>
                ))}
              </section>
            )}{" "}
            {!!content.education?.length && (
              <section>
                <h2>Education</h2>
                {content.education.map((item, index) => (
                  <div key={`${item.institution}-${index}`}>
                    <h3>
                      {item.degree} · {item.institution}
                    </h3>
                    <p>{item.field_of_study}</p>
                  </div>
                ))}
              </section>
            )}{" "}
            {!!content.projects?.length && (
              <section>
                <h2>Projects</h2>
                {content.projects.map((item) => (
                  <div key={item.name}>
                    <h3>{item.name}</h3>
                    <p>{item.description}</p>
                  </div>
                ))}
              </section>
            )}
            <section>
              <h2>Skills</h2>
              <p>{content.skills?.join(" · ")}</p>
            </section>
          </article>
        </div>
      )}
    </main>
  );
}
