import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Copy,
  Download,
  Edit3,
  Eye,
  FilePlus2,
  MoreHorizontal,
  Trash2,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { ResumePreview } from "../features/resume/templates/registry";
import { apiErrorMessage, careerApi } from "../services/careerApi";

export default function ResumeHomePage() {
  const navigate = useNavigate();
  const client = useQueryClient();
  const [menu, setMenu] = useState(null);
  const resumes = useQuery({
    queryKey: ["resumes"],
    queryFn: careerApi.listResumes,
  });
  const refresh = () => client.invalidateQueries({ queryKey: ["resumes"] });
  const remove = useMutation({
    mutationFn: careerApi.deleteResume,
    onSuccess: refresh,
  });
  const duplicate = useMutation({
    mutationFn: careerApi.duplicateResume,
    onSuccess: async (created) => {
      await refresh();
      navigate(`/app/resume/${created.id}/edit`);
    },
  });
  const rename = useMutation({
    mutationFn: ({ id, title }) => careerApi.updateResume(id, { title }),
    onSuccess: refresh,
  });
  const exportPdf = async (item) => {
    try {
      const { data } = await careerApi.exportResume(item.id);
      const url = URL.createObjectURL(data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${item.title}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      window.alert(apiErrorMessage(error));
    }
  };
  if (resumes.isLoading)
    return (
      <main className="page">
        <section className="surface async-state">
          <p>Opening your resume workspace…</p>
        </section>
      </main>
    );
  return (
    <main className="page resume-library-page">
      <section className="resume-library-hero">
        <div>
          <span className="section-eyebrow">Resume workspace</span>
          <h1>Resumes that move your career forward.</h1>
          <p>
            Create tailored, ATS-friendly resumes from your verified Career
            Profile.
          </p>
        </div>
        <Link className="button primary resume-create-button" to="templates">
          <FilePlus2 size={17} />
          Create new resume
        </Link>
      </section>
      {resumes.error && (
        <section className="async-state error">
          <p>{apiErrorMessage(resumes.error)}</p>
        </section>
      )}
      <section className="library-heading">
        <div>
          <h2>My Resumes</h2>
          <p>
            {resumes.data?.length || 0} saved document
            {resumes.data?.length === 1 ? "" : "s"}
          </p>
        </div>
      </section>
      {!resumes.data?.length ? (
        <section className="surface resume-library-empty">
          <div className="empty-document-stack">
            <i />
            <i />
            <FilePlus2 />
          </div>
          <h2>Build your first standout resume</h2>
          <p>
            Start by choosing one of eight original CareerPilot templates. Your
            verified profile will remain the source of truth.
          </p>
          <Link className="button primary" to="templates">
            Explore templates
          </Link>
        </section>
      ) : (
        <div className="resume-library-grid">
          {resumes.data.map((item) => (
            <article className="resume-library-card" key={item.id}>
              <Link
                className="resume-library-thumbnail"
                to={`${item.id}/edit`}
                aria-label={`Edit ${item.title}`}
              >
                <div>
                  <ResumePreview
                    content={item.content}
                    templateId={item.template_id}
                  />
                </div>
              </Link>
              <div className="resume-library-info">
                <div>
                  <span className={`resume-status status-${item.status}`}>
                    {item.status}
                  </span>
                  <h3>{item.title}</h3>
                  <p>
                    {item.template_id.replaceAll("_", " ")} · Version{" "}
                    {item.version}
                  </p>
                  <small>
                    Last edited{" "}
                    {new Date(
                      item.updated_at || Date.now(),
                    ).toLocaleDateString()}
                  </small>
                </div>
                <button
                  className="icon-button"
                  onClick={() => setMenu(menu === item.id ? null : item.id)}
                  aria-label="Resume actions"
                >
                  <MoreHorizontal size={18} />
                </button>
                {menu === item.id && (
                  <div className="resume-card-menu">
                    <Link to={`${item.id}/edit`}>
                      <Edit3 size={14} />
                      Edit
                    </Link>
                    <Link to={`${item.id}/edit?preview=1`}>
                      <Eye size={14} />
                      Preview
                    </Link>
                    <button onClick={() => exportPdf(item)}>
                      <Download size={14} />
                      Download
                    </button>
                    <button onClick={() => duplicate.mutate(item.id)}>
                      <Copy size={14} />
                      Duplicate
                    </button>
                    <button
                      onClick={() => {
                        const title = window.prompt(
                          "Rename resume",
                          item.title,
                        );
                        if (title?.trim())
                          rename.mutate({ id: item.id, title: title.trim() });
                      }}
                    >
                      Rename
                    </button>
                    <button
                      className="danger"
                      onClick={() =>
                        window.confirm(
                          `Delete ${item.title}? This cannot be undone.`,
                        ) && remove.mutate(item.id)
                      }
                    >
                      <Trash2 size={14} />
                      Delete
                    </button>
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </main>
  );
}
