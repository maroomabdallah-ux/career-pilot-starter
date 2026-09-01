import {
  BriefcaseBusiness,
  Check,
  ExternalLink,
  FolderKanban,
  GraduationCap,
  MapPin,
  Pencil,
  Plus,
  Save,
  Target,
  Trash2,
  UserRound,
  Wrench,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, Navigate, NavLink, useParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import AsyncState from "../components/common/AsyncState";
import {
  DegreeCombobox,
  FieldOfStudyCombobox,
  GradeSystemSelector,
  UniversityCombobox,
} from "../components/selectors/EducationSelectors";
import {
  useCareerData,
  useChildMutation,
  useProfileMutation,
} from "../hooks/useCareerData";
import {
  calculateProfileCompletion,
  profileCompletionConfig,
} from "../services/profileCompletion";
import { apiErrorMessage } from "../services/careerApi";
import {
  CareerGoalSelector,
  WorkModeSelector,
} from "../components/career/CareerSelectors";
import DeleteConfirmationDialog from "../components/common/DeleteConfirmationDialog";

const sections = [
  ["Overview", "", UserRound],
  ["Career Direction", "direction", Target],
  ["Education", "education", GraduationCap],
  ["Experience", "experience", BriefcaseBusiness],
  ["Projects", "projects", FolderKanban],
  ["Skills", "skills", Wrench],
];
const configs = {
  experience: {
    title: "Experience",
    singular: "experience",
    list: "experiences",
    api: "experiences",
    icon: BriefcaseBusiness,
    fields: [
      ["company", "Company", true],
      ["job_title", "Role", true],
      ["employment_type", "Employment type"],
      ["location", "Location"],
      ["start_date", "Start date", false, "date"],
      ["end_date", "End date", false, "date"],
      ["description", "Role scope and impact", false, "textarea"],
    ],
  },
  projects: {
    title: "Projects",
    singular: "project",
    list: "projects",
    api: "projects",
    icon: FolderKanban,
    fields: [
      ["name", "Project title", true],
      ["role", "Your role"],
      ["project_url", "Project link", false, "url"],
      ["repository_url", "Repository", false, "url"],
      ["start_date", "Start date", false, "date"],
      ["end_date", "End date", false, "date"],
      ["description", "What you built and why it mattered", true, "textarea"],
    ],
  },
  skills: {
    title: "Skills",
    singular: "skill",
    list: "skills",
    api: "skills",
    icon: Wrench,
    fields: [
      ["name", "Skill", true],
      ["category", "Skill family"],
      ["proficiency_level", "Proficiency"],
      ["years_of_experience", "Years used", false, "number"],
    ],
  },
};

function Ring({ score }) {
  return (
    <div className="profile-ring" style={{ "--score": score }}>
      <div>
        <strong>{score}%</strong>
        <span>Profile strength</span>
      </div>
    </div>
  );
}
function WorkspaceNav() {
  return (
    <nav className="profile-local-nav">
      {sections.map(([label, path, Icon]) => (
        <NavLink
          end={!path}
          key={label}
          to={`/app/profile${path ? `/${path}` : ""}`}
        >
          <Icon size={16} />
          {label}
        </NavLink>
      ))}
    </nav>
  );
}
function EmptyCategory({ title, onAdd }) {
  return (
    <div className="empty-state">
      <span>
        <Plus size={20} />
      </span>
      <h3>No {title.toLowerCase()} added yet</h3>
      <p>
        Add your {title.toLowerCase()} to strengthen your career profile and
        prepare it for future CareerPilot tools.
      </p>
      <button type="button" className="button secondary" onClick={onAdd}>
        Add {title === "Skills" ? "a skill" : title.toLowerCase()}
      </button>
    </div>
  );
}

function ProfileForm({ profile }) {
  const mutation = useProfileMutation();
  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { isDirty },
  } = useForm({
    defaultValues: {
      professional_title: "",
      city: "",
      country: "",
      professional_summary: "",
      profile_picture: null,
    },
  });
  useEffect(() => {
    reset({
      professional_title: profile?.professional_title || "",
      city: profile?.city || "",
      country: profile?.country || "",
      professional_summary: profile?.professional_summary || "",
      profile_picture: profile?.profile_picture || null,
    });
  }, [profile, reset]);
  const picture = watch("profile_picture");
  const [pictureError, setPictureError] = useState("");
  const choosePicture = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (
      !["image/jpeg", "image/png", "image/webp"].includes(file.type) ||
      file.size > 1_000_000
    ) {
      setPictureError("Choose a JPEG, PNG, or WebP image smaller than 1 MB.");
      event.target.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setValue("profile_picture", reader.result, { shouldDirty: true });
      setPictureError("");
    };
    reader.readAsDataURL(file);
  };
  const submit = (payload) =>
    mutation.mutate({
      mode: profile ? "update" : "create",
      payload: Object.fromEntries(
        Object.entries(payload).map(([k, v]) => [k, v === "" ? null : v]),
      ),
    });
  return (
    <form className="blueprint-editor" onSubmit={handleSubmit(submit)}>
      <header>
        <div>
          <span className="section-eyebrow">Career basics</span>
          <h2>Your professional identity</h2>
        </div>
        <button
          type="submit"
          className="button primary"
          disabled={mutation.isPending || (!isDirty && profile)}
        >
          <Save size={15} /> Save
        </button>
      </header>
      <div className="form-grid">
        <div className="profile-picture-field span-2">
          <span className="profile-picture-preview">
            {picture ? (
              <img src={picture} alt="Profile" />
            ) : (
              <UserRound size={28} />
            )}
          </span>
          <div>
            <strong>
              Profile picture <small>Optional</small>
            </strong>
            <p>
              Shown in your CareerPilot profile and navigation. It is not added
              to your resume.
            </p>
            <div className="profile-picture-actions">
              <label className="button secondary">
                Choose picture
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={choosePicture}
                />
              </label>
              {picture && (
                <button
                  type="button"
                  className="text-button"
                  onClick={() =>
                    setValue("profile_picture", null, { shouldDirty: true })
                  }
                >
                  Remove
                </button>
              )}
            </div>
            {pictureError && (
              <small className="field-error" role="alert">
                {pictureError}
              </small>
            )}
          </div>
        </div>
        <label className="span-2">
          <span>Professional title</span>
          <input
            {...register("professional_title")}
            placeholder="The role that best describes you"
          />
        </label>
        <label>
          <span>City</span>
          <input {...register("city")} />
        </label>
        <label>
          <span>Country</span>
          <input {...register("country")} />
        </label>
        <label className="span-2">
          <span>Professional summary</span>
          <textarea
            rows="5"
            {...register("professional_summary")}
            placeholder="Your strengths, scope, and the value you create"
          />
        </label>
      </div>
      {mutation.isError && (
        <p className="form-error" role="alert">
          {apiErrorMessage(mutation.error)}
        </p>
      )}
    </form>
  );
}

function DirectionForm({ profile }) {
  const mutation = useProfileMutation();
  const [roles, setRoles] = useState(profile?.target_roles || []);
  const [modes, setModes] = useState(profile?.preferred_work_modes || []);
  const [locations, setLocations] = useState(
    (profile?.preferred_locations || []).join(", "),
  );
  useEffect(() => {
    setRoles(profile?.target_roles || []);
    setModes(profile?.preferred_work_modes || []);
    setLocations((profile?.preferred_locations || []).join(", "));
  }, [profile]);
  const save = (event) => {
    event.preventDefault();
    mutation.mutate({
      mode: profile ? "update" : "create",
      payload: {
        target_roles: roles,
        preferred_work_modes: modes,
        preferred_locations: locations
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      },
    });
  };
  return (
    <section className="category-page">
      <header>
        <div>
          <span className="section-eyebrow">
            Career direction · 10% of your profile
          </span>
          <h1>Career Direction</h1>
          <p>
            Align your target roles, preferred work modes, and locations with
            your next move.
          </p>
        </div>
      </header>
      <form className="blueprint-editor direction-editor" onSubmit={save}>
        <CareerGoalSelector
          value={roles}
          onChange={setRoles}
          suggestions={[]}
        />
        <span className="mini-label">Preferred work modes</span>
        <WorkModeSelector value={modes} onChange={setModes} />
        <label className="hero-input direction-locations">
          <span>Preferred locations</span>
          <input
            value={locations}
            onChange={(event) => setLocations(event.target.value)}
            placeholder="Amman, Dubai, Remote"
          />
          <small>Separate multiple locations with commas.</small>
        </label>
        {mutation.isError && (
          <p className="form-error" role="alert">
            {apiErrorMessage(mutation.error)}
          </p>
        )}
        <div className="direction-actions">
          <button
            type="submit"
            className="button primary"
            disabled={mutation.isPending}
          >
            <Save size={15} /> Save career direction
          </button>
        </div>
      </form>
    </section>
  );
}

function Overview({ profile, user }) {
  const completion = calculateProfileCompletion(profile);
  const stages = [
    [
      "Personal profile",
      "personal",
      profile?.professional_title
        ? `${profile.professional_title} · ${profile.city || "Location open"}`
        : "Define your professional identity",
      "/app/profile",
    ],
    [
      "Career direction",
      "goals",
      profile?.target_roles?.length
        ? `${profile.target_roles.length} target roles selected`
        : "Add goals and preferences",
      "/app/profile/direction",
    ],
    [
      "Education",
      "education",
      `${profile?.education?.length || 0} entries`,
      "/app/profile/education",
    ],
    [
      "Experience",
      "experience",
      `${profile?.experiences?.length || 0} roles`,
      "/app/profile/experience",
    ],
    [
      "Projects",
      "projects",
      `${profile?.projects?.length || 0} portfolio projects`,
      "/app/profile/projects",
    ],
    [
      "Skills",
      "skills",
      `${profile?.skills?.length || 0} skills`,
      "/app/profile/skills",
    ],
  ];
  return (
    <>
      <section className="profile-blueprint-hero">
        <div>
          <span className="section-eyebrow">Career Profile Blueprint</span>
          <h1>{user?.first_name}'s professional foundation</h1>
          <p>
            A connected view of the evidence CareerPilot can use across your
            future career tools.
          </p>
          <Link className="button primary" to={completion.nextAction.to}>
            {completion.nextAction.label}
          </Link>
        </div>
        <Ring score={completion.score} />
      </section>
      <div className="blueprint-layout">
        <section className="blueprint-journey">
          {stages.map(([label, key, summary, to], i) => {
            const done = completion.categories[key];
            return (
              <Link to={to} key={label} className={done ? "complete" : ""}>
                <span>
                  {done ? <Check size={15} /> : String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <small>
                    {profileCompletionConfig[key] || 10}% of profile
                  </small>
                  <h3>{label}</h3>
                  <p>{summary}</p>
                </div>
                <strong>{done ? "Complete" : "Needs attention"}</strong>
                {i < stages.length - 1 && <i />}
              </Link>
            );
          })}
        </section>
        <ProfileForm profile={profile} />
      </div>
    </>
  );
}

function EducationDrawer({ item, onClose }) {
  const mutation = useChildMutation();
  const [form, setForm] = useState(item || {});
  const set = (k, v) => setForm((x) => ({ ...x, [k]: v }));
  const submit = (e) => {
    e.preventDefault();
    mutation.mutate(
      {
        action: item ? "update" : "create",
        resource: "education",
        id: item?.id,
        payload: Object.fromEntries(
          Object.entries(form).filter(([, v]) => v !== "" && v != null),
        ),
      },
      { onSuccess: onClose },
    );
  };
  return (
    <div className="modal-backdrop">
      <section className="modal education-drawer">
        <header>
          <div>
            <span className="section-eyebrow">Academic foundation</span>
            <h2>{item ? "Edit" : "Add"} education</h2>
          </div>
          <button type="button" className="icon-button" onClick={onClose}>
            <X />
          </button>
        </header>
        <form onSubmit={submit}>
          <fieldset>
            <legend>Institution & program</legend>
            <UniversityCombobox
              value={form.institution}
              onChange={(x) => set("institution", x)}
              country={form.country}
            />
            <div className="form-grid">
              <DegreeCombobox
                value={form.degree}
                onChange={(x) => set("degree", x)}
              />
              <FieldOfStudyCombobox
                value={form.field_of_study}
                onChange={(x) => set("field_of_study", x)}
              />
            </div>
          </fieldset>
          <fieldset>
            <legend>Study period</legend>
            <div className="form-grid">
              <label>
                <span>Start date</span>
                <input
                  type="date"
                  value={form.start_date || ""}
                  onChange={(e) => set("start_date", e.target.value)}
                />
              </label>
              <label>
                <span>End date</span>
                <input
                  type="date"
                  disabled={form.is_current}
                  value={form.end_date || ""}
                  onChange={(e) => set("end_date", e.target.value)}
                />
              </label>
            </div>
            <label className="check-control">
              <input
                type="checkbox"
                checked={Boolean(form.is_current)}
                onChange={(e) => set("is_current", e.target.checked)}
              />{" "}
              Currently studying here
            </label>
          </fieldset>
          <fieldset>
            <legend>Academic result</legend>
            <GradeSystemSelector
              system={form.grade_system}
              setSystem={(x) => set("grade_system", x)}
              grade={form.grade}
              setGrade={(x) => set("grade", x)}
            />
          </fieldset>
          <footer>
            <button
              type="button"
              className="button secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button type="submit" className="button primary">
              Save education
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

function GenericDrawer({ config, item, onClose }) {
  const mutation = useChildMutation();
  const { register, handleSubmit } = useForm({ defaultValues: item || {} });
  return (
    <div className="modal-backdrop">
      <section className="modal">
        <header>
          <h2>
            {item ? "Edit" : "Add"} {config.singular}
          </h2>
          <button type="button" className="icon-button" onClick={onClose}>
            <X />
          </button>
        </header>
        <form
          onSubmit={handleSubmit((payload) =>
            mutation.mutate(
              {
                action: item ? "update" : "create",
                resource: config.api,
                id: item?.id,
                payload: Object.fromEntries(
                  Object.entries(payload).filter(([, v]) => v !== ""),
                ),
              },
              { onSuccess: onClose },
            ),
          )}
        >
          <div className="form-grid">
            {config.fields.map(([name, label, required, type = "text"]) => (
              <label className={type === "textarea" ? "span-2" : ""} key={name}>
                <span>{label}</span>
                {type === "textarea" ? (
                  <textarea rows="5" {...register(name, { required })} />
                ) : (
                  <input
                    type={type}
                    {...register(name, {
                      required,
                      valueAsNumber: type === "number",
                    })}
                  />
                )}
              </label>
            ))}
          </div>
          <footer>
            <button
              type="button"
              className="button secondary"
              onClick={onClose}
            >
              Cancel
            </button>
            <button type="submit" className="button primary">
              Save {config.singular}
            </button>
          </footer>
        </form>
      </section>
    </div>
  );
}

function EducationPage({ items }) {
  const [edit, setEdit] = useState();
  const [pendingDelete, setPendingDelete] = useState();
  const mutation = useChildMutation();
  return (
    <CategoryShell
      title="Education"
      copy="The academic context behind your expertise."
      action={() => setEdit(null)}
      contribution="15% of your profile"
    >
      {items.length ? (
        <div className="education-timeline">
          {items.map((x) => (
            <article key={x.id}>
              <time>
                {x.start_date?.slice(0, 4) || "—"}
                <i />
                {x.is_current ? "Present" : x.end_date?.slice(0, 4) || "—"}
              </time>
              <span />
              <div>
                <small>{x.grade_system || "Education"}</small>
                <h3>{x.institution}</h3>
                <p>
                  {[x.degree, x.field_of_study].filter(Boolean).join(" · ")}
                </p>
                {x.grade && <strong>{x.grade}</strong>}
              </div>
              <Actions
                onEdit={() => setEdit(x)}
                onDelete={() => setPendingDelete(x)}
              />
            </article>
          ))}
        </div>
      ) : (
        <EmptyCategory title="Education" onAdd={() => setEdit(null)} />
      )}{" "}
      {edit !== undefined && (
        <EducationDrawer item={edit} onClose={() => setEdit(undefined)} />
      )}
      {pendingDelete && <DeleteConfirmationDialog title="Delete education?" description="Remove this education entry from your profile." resourceLabel={[pendingDelete.institution, [pendingDelete.degree, pendingDelete.field_of_study].filter(Boolean).join(" · ")].filter(Boolean).join(" — ")} loading={mutation.isPending} onCancel={() => setPendingDelete(undefined)} onConfirm={() => mutation.mutate({ action: "delete", resource: "education", id: pendingDelete.id }, { onSuccess: () => setPendingDelete(undefined) })} />}
    </CategoryShell>
  );
}
function Actions({ onEdit, onDelete }) {
  return (
    <div className="resource-actions">
      <button
        type="button"
        aria-label="Edit item"
        className="icon-button quiet"
        onClick={onEdit}
      >
        <Pencil size={15} />
      </button>
      <button
        type="button"
        aria-label="Delete item"
        className="icon-button quiet danger"
        onClick={onDelete}
      >
        <Trash2 size={15} />
      </button>
    </div>
  );
}
function CategoryShell({ title, copy, action, contribution, children }) {
  return (
    <section className="category-page">
      <header>
        <div>
          <span className="section-eyebrow">
            Career evidence · {contribution}
          </span>
          <h1>{title}</h1>
          <p>{copy}</p>
        </div>
        <button type="button" className="button primary" onClick={action}>
          <Plus size={16} /> Add{" "}
          {title === "Skills" ? "skill" : title.slice(0, -1).toLowerCase()}
        </button>
      </header>
      {children}
    </section>
  );
}

function GenericPage({ config, items }) {
  const [edit, setEdit] = useState();
  const [pendingDelete, setPendingDelete] = useState();
  const mutation = useChildMutation();
  if (config.list === "skills") {
    const groups = Object.groupBy
      ? Object.groupBy(items, (x) => x.category || "Core skills")
      : items.reduce(
          (a, x) => ((a[x.category || "Core skills"] ||= []).push(x), a),
          {},
        );
    return (
      <CategoryShell
        title="Skills"
        copy="Grouped capabilities that describe how you create value."
        action={() => setEdit(null)}
        contribution="20% of your profile"
      >
        {items.length ? (
          <div className="skill-families">
            {Object.entries(groups).map(([name, skills]) => (
              <section key={name}>
                <span>{name}</span>
                <div>
                  {skills.map((x) => (<div className="skill-chip" key={x.id}><button type="button" onClick={() => setEdit(x)}>{x.name}<small>{x.proficiency_level}</small></button><button type="button" className="icon-button quiet danger" aria-label={`Delete ${x.name}`} onClick={() => setPendingDelete(x)}><Trash2 size={14}/></button></div>))}
                </div>
              </section>
            ))}
          </div>
        ) : (
          <EmptyCategory title="Skills" onAdd={() => setEdit(null)} />
        )}{" "}
        {edit !== undefined && (
          <GenericDrawer
            config={config}
            item={edit}
            onClose={() => setEdit(undefined)}
          />
        )}
        {pendingDelete && <DeleteConfirmationDialog title="Delete skill?" description="Remove this skill from your profile." resourceLabel={pendingDelete.name} loading={mutation.isPending} onCancel={() => setPendingDelete(undefined)} onConfirm={() => mutation.mutate({ action: "delete", resource: config.api, id: pendingDelete.id }, { onSuccess: () => setPendingDelete(undefined) })} />}
      </CategoryShell>
    );
  }
  return (
    <CategoryShell
      title={config.title}
      copy={
        config.list === "projects"
          ? "A portfolio of work that proves what you can deliver."
          : "A professional timeline of your scope, impact, and growth."
      }
      action={() => setEdit(null)}
      contribution={
        config.list === "projects"
          ? "15% of your profile"
          : "25% of your profile"
      }
    >
      {items.length ? (
        <div className={`${config.list}-showcase`}>
          {items.map((x) => (
            <article key={x.id}>
              <span className="entry-mark">
                <config.icon size={18} />
              </span>
              <div>
                <small>
                  {[
                    x.start_date?.slice(0, 4),
                    x.end_date?.slice(0, 4) || "Present",
                  ]
                    .filter(Boolean)
                    .join(" — ")}
                </small>
                <h3>{x.company || x.name}</h3>
                <strong>{x.job_title || x.role}</strong>
                <p>{x.description}</p>
                {x.project_url && (
                  <a href={x.project_url} target="_blank" rel="noreferrer">
                    View project <ExternalLink size={13} />
                  </a>
                )}
              </div>
              <Actions
                onEdit={() => setEdit(x)}
                onDelete={() => setPendingDelete(x)}
              />
            </article>
          ))}
        </div>
      ) : (
        <EmptyCategory title={config.title} onAdd={() => setEdit(null)} />
      )}{" "}
      {edit !== undefined && (
        <GenericDrawer
          config={config}
          item={edit}
          onClose={() => setEdit(undefined)}
        />
      )}
      {pendingDelete && <DeleteConfirmationDialog title={`Delete ${config.singular}?`} description={`Remove this ${config.singular} from your profile.`} resourceLabel={[x => x.job_title, x => x.company || x.name].map((fn) => fn(pendingDelete)).filter(Boolean).join(" — ")} loading={mutation.isPending} onCancel={() => setPendingDelete(undefined)} onConfirm={() => mutation.mutate({ action: "delete", resource: config.api, id: pendingDelete.id }, { onSuccess: () => setPendingDelete(undefined) })} />}
    </CategoryShell>
  );
}

export default function ProfilePage() {
  const { section } = useParams();
  const { user, profile } = useCareerData();
  const p = profile.data;
  if (
    section &&
    !configs[section] &&
    section !== "education" &&
    section !== "direction"
  )
    return <Navigate to="/app/profile" replace />;
  return (
    <main className="page profile-workspace">
      <header className="workspace-heading">
        <div>
          <span className="section-eyebrow">Career profile</span>
          <h1>Build the story behind your next move.</h1>
          <p>
            <MapPin size={14} />
            {p?.city && p?.country
              ? `${p.city}, ${p.country}`
              : "Global career workspace"}
          </p>
        </div>
      </header>
      <WorkspaceNav />
      <AsyncState
        loading={profile.isLoading}
        error={profile.error?.response?.status === 404 ? null : profile.error}
      >
        {!section ? (
          <Overview profile={p} user={user.data} />
        ) : section === "direction" ? (
          <DirectionForm profile={p} />
        ) : section === "education" ? (
          <EducationPage items={p?.education || []} />
        ) : (
          <GenericPage
            config={configs[section]}
            items={p?.[configs[section]?.list] || []}
          />
        )}
      </AsyncState>
    </main>
  );
}
