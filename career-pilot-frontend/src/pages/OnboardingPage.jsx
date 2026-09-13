import {
  ArrowLeft,
  ArrowRight,
  Check,
  Compass,
  GraduationCap,
  LoaderCircle,
  MapPin,
  Pencil,
  Plus,
  Rocket,
  Sparkles,
  Trash2,
  UserRound,
  Wrench,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import {
  CareerGoalSelector,
  CareerLevelSelector,
  WorkModeSelector,
} from "../components/career/CareerSelectors";
import JourneyProgress from "../components/career/JourneyProgress";
import { LocationCombobox } from "../components/selectors/LocationSelectors";
import { useAuthStore } from "../features/auth/auth.store";
import { careerGoalSuggestionsService } from "../services/careerIntelligenceService";
import { apiErrorMessage, careerApi } from "../services/careerApi";

const steps = ["Basics", "Direction", "Education", "Skills", "Experience", "Preferences", "Review"];
const icons = [UserRound, Compass, GraduationCap, Wrench, Pencil, MapPin, Check];
const stepVisuals = [
  ["Your story", "Identity", "Location"],
  ["Your direction", "Profession", "Goals"],
  ["Your learning", "Degree", "Knowledge"],
  ["Your strengths", "Skills", "Expertise"],
  ["Your evidence", "Experience", "Projects"],
  ["Your rhythm", "Work mode", "Places"],
  ["Ready", "Profile", "CareerPilot"],
];
const draftKey = "careerpilot-onboarding-draft-v2";
const blankEducation = { institution: "", degree: "", field_of_study: "", start_date: "", end_date: "", grade: "", grade_system: "" };
const blankExperience = { company: "", job_title: "", start_date: "", end_date: "", description: "" };
const emptyDraft = {
  step: 0,
  values: { professional_title: "", target_roles: [], preferred_locations: [], preferred_work_modes: [], years_of_experience: 0 },
  country: null,
  state: null,
  city: null,
  level: "",
  education: blankEducation,
  educationId: null,
  skills: [],
  experience: blankExperience,
  experienceId: null,
  hasExperience: false,
};

function readDraft() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(draftKey) || "{}");
    return {
      ...emptyDraft,
      ...saved,
      step: Number.isInteger(saved.step) && saved.step >= 0 && saved.step < steps.length ? saved.step : 0,
      values: { ...emptyDraft.values, ...(saved.values || {}) },
      education: { ...blankEducation, ...(saved.education || {}) },
      experience: { ...blankExperience, ...(saved.experience || {}) },
      skills: Array.isArray(saved.skills) ? saved.skills : [],
    };
  } catch {
    return emptyDraft;
  }
}

const clean = (object) => Object.fromEntries(Object.entries(object).map(([key, value]) => [key, value === "" ? null : value]));
const locationName = (value) => (typeof value === "string" ? value : value?.name) || null;

export default function OnboardingPage() {
  const draft = useState(readDraft)[0];
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const [step, setStep] = useState(draft.step);
  const [stepDirection, setStepDirection] = useState("forward");
  const [values, setValues] = useState(draft.values);
  const [country, setCountry] = useState(draft.country);
  const [state, setState] = useState(draft.state);
  const [city, setCity] = useState(draft.city);
  const [prefCountry, setPrefCountry] = useState(null);
  const [prefState, setPrefState] = useState(null);
  const [prefCity, setPrefCity] = useState(null);
  const [level, setLevel] = useState(draft.level);
  const [education, setEducation] = useState(draft.education);
  const [educationId, setEducationId] = useState(draft.educationId);
  const [skills, setSkills] = useState(draft.skills);
  const [skillInput, setSkillInput] = useState("");
  const [experience, setExperience] = useState(draft.experience);
  const [experienceId, setExperienceId] = useState(draft.experienceId);
  const [hasExperience, setHasExperience] = useState(draft.hasExperience);
  const [profileExists, setProfileExists] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    let active = true;
    careerApi.getProfile().then((profile) => {
      if (!active) return;
      if (
        profile.professional_title &&
        profile.target_roles?.length &&
        profile.education?.length &&
        profile.skills?.length
      ) {
        careerApi.completeOnboarding().then((updated) => {
          if (!active) return;
          setUser(updated);
          navigate("/app/dashboard", { replace: true });
        });
        return;
      }
      setProfileExists(true);
      setValues((current) => ({
        ...current,
        professional_title: current.professional_title || profile.professional_title || "",
        target_roles: current.target_roles.length ? current.target_roles : profile.target_roles || [],
        preferred_locations: current.preferred_locations.length ? current.preferred_locations : profile.preferred_locations || [],
        preferred_work_modes: current.preferred_work_modes.length ? current.preferred_work_modes : profile.preferred_work_modes || [],
        years_of_experience: current.years_of_experience || profile.years_of_experience || 0,
      }));
      if (!country && profile.country) setCountry(profile.country);
      if (!city && profile.city) setCity(profile.city);
      const savedEducation = profile.education?.[0];
      if (savedEducation && !educationId) {
        setEducationId(savedEducation.id);
        setEducation(
          Object.fromEntries(
            Object.keys(blankEducation).map((key) => [
              key,
              savedEducation[key] || "",
            ]),
          ),
        );
      }
      if (!skills.length && profile.skills?.length) setSkills(profile.skills.map(({ id, name }) => ({ id, name })));
      const savedExperience = profile.experiences?.[0];
      if (savedExperience && !experienceId) {
        setHasExperience(true);
        setExperienceId(savedExperience.id);
        setExperience(
          Object.fromEntries(
            Object.keys(blankExperience).map((key) => [
              key,
              savedExperience[key] || "",
            ]),
          ),
        );
      }
    }).catch((requestError) => {
      if (requestError.response?.status !== 404 && active) setError(apiErrorMessage(requestError));
    }).finally(() => active && setLoadingProfile(false));
    return () => { active = false; };
  }, []);

  useEffect(() => {
    sessionStorage.setItem(draftKey, JSON.stringify({ step, values, country, state, city, level, education, educationId, skills, experience, experienceId, hasExperience }));
  }, [step, values, country, state, city, level, education, educationId, skills, experience, experienceId, hasExperience]);

  if (user?.onboarding_completed) return <Navigate to="/app/dashboard" replace />;

  const update = (key, value) => setValues((current) => ({ ...current, [key]: value }));
  const updateEducation = (key, value) => setEducation((current) => ({ ...current, [key]: value }));
  const updateExperience = (key, value) => setExperience((current) => ({ ...current, [key]: value }));
  const ensureProfile = async (payload) => {
    if (profileExists) return careerApi.updateProfile(payload);
    const profile = await careerApi.createProfile(payload);
    setProfileExists(true);
    return profile;
  };
  const addSkill = () => {
    const name = skillInput.trim();
    if (name && !skills.some((skill) => skill.name.toLowerCase() === name.toLowerCase())) setSkills((items) => [...items, { id: null, name }]);
    setSkillInput("");
  };
  const removeSkill = async (index) => {
    const skill = skills[index];
    setSkills((items) => items.filter((_, itemIndex) => itemIndex !== index));
    if (skill.id) await careerApi.deleteChild("skills", skill.id);
  };
  const persistStep = async (currentStep) => {
    if (currentStep === 0) {
      await ensureProfile({ country: locationName(country), city: locationName(city) });
    }
    if (currentStep === 1) {
      if (!values.professional_title.trim() || !values.target_roles.length || !level) throw new Error("Add your profession, at least one preferred role, and career level.");
      await ensureProfile({ professional_title: values.professional_title.trim(), target_roles: values.target_roles, years_of_experience: values.years_of_experience });
    }
    if (currentStep === 2) {
      if (!education.institution.trim() || !education.degree.trim() || !education.field_of_study.trim()) throw new Error("Institution, degree, and field of study are required.");
      const payload = clean(education);
      const saved = educationId ? await careerApi.updateChild("education", educationId, payload) : await careerApi.createChild("education", payload);
      setEducationId(saved.id);
    }
    if (currentStep === 3) {
      if (!skills.length) throw new Error("Add at least one skill before continuing.");
      const saved = await Promise.all(skills.map((skill) => skill.id ? careerApi.updateChild("skills", skill.id, { name: skill.name }) : careerApi.createChild("skills", { name: skill.name })));
      setSkills(saved.map(({ id, name }) => ({ id, name })));
    }
    if (currentStep === 4 && hasExperience) {
      if (!experience.company.trim() || !experience.job_title.trim()) throw new Error("Company and job title are required when adding experience.");
      const payload = clean(experience);
      const saved = experienceId ? await careerApi.updateChild("experiences", experienceId, payload) : await careerApi.createChild("experiences", payload);
      setExperienceId(saved.id);
    }
    if (currentStep === 5) await ensureProfile({ preferred_locations: values.preferred_locations, preferred_work_modes: values.preferred_work_modes });
  };
  const moveToStep = async (nextStep) => {
    if (nextStep < step) {
      setStepDirection("backward");
      setStep(nextStep);
      return;
    }
    setSaving(true);
    setError("");
    try {
      await persistStep(step);
      setStepDirection("forward");
      setStep(nextStep);
    } catch (requestError) {
      setError(requestError.response ? apiErrorMessage(requestError) : requestError.message);
    } finally {
      setSaving(false);
    }
  };
  const addLocation = () => {
    if (!prefCountry) return;
    const label = locationName(prefCity) ? `${locationName(prefCity)}, ${locationName(prefCountry)}` : locationName(prefCountry);
    if (!values.preferred_locations.includes(label)) update("preferred_locations", [...values.preferred_locations, label]);
    setPrefCity(null);
  };
  const finish = async () => {
    setSaving(true);
    setError("");
    try {
      await persistStep(5);
      const updated = await careerApi.completeOnboarding();
      sessionStorage.removeItem(draftKey);
      setUser(updated);
      navigate("/app/dashboard", { replace: true });
    } catch (requestError) {
      setError(apiErrorMessage(requestError));
    } finally {
      setSaving(false);
    }
  };

  const Icon = icons[step];
  const visualWords = stepVisuals[step];
  const locationLabel = [locationName(city), locationName(country)].filter(Boolean).join(", ") || "Not provided";

  if (loadingProfile) return <main className="launchpad"><LoaderCircle className="spin" size={28} /></main>;

  return (
    <main className="launchpad" style={{ "--onboarding-progress": step + 1 }}>
      <div className="launch-ambient launch-ambient-one" /><div className="launch-ambient launch-ambient-two" />
      <section className="launchpad-shell">
        <aside className="launchpad-side">
          <div className="launch-logo" aria-label="CareerPilot"><Compass size={24} /><strong>CareerPilot</strong></div>
          <div><span className="section-eyebrow">Career Profile</span><h2>Build the foundation for every next move.</h2><p>Each step saves directly to your Career Profile, so Jobs, Resume, and your agents can use it immediately.</p></div>
          <div className="launch-motion-stage" key={`visual-${step}`} aria-hidden="true">
            <div className="motion-ring motion-ring-outer" /><div className="motion-ring motion-ring-inner" />
            <span className="motion-node motion-node-one">{visualWords[1]}</span><span className="motion-node motion-node-two">{visualWords[2]}</span>
            <div className="motion-core"><Icon size={25} /><strong>{visualWords[0]}</strong></div>
          </div>
          <JourneyProgress steps={steps} current={step} />
          <small>Saved as you continue · Editable anytime</small>
        </aside>

        <section className="launchpad-main">
          <header><span>{String(step + 1).padStart(2, "0")} / {String(steps.length).padStart(2, "0")}</span><i><Icon size={20} /></i></header>
          <div className={`launch-step is-${stepDirection}`} key={step}>
            {step === 0 && <><span className="section-eyebrow">Basic information</span><h1>Let’s start with where you are.</h1><p>Your account already has your name and email. Add your current location to complete the basics.</p><div className="onboarding-account-card"><UserRound size={20} /><div><strong>{user?.first_name} {user?.last_name}</strong><small>{user?.email}</small></div></div><LocationCombobox country={country} setCountry={setCountry} state={state} setState={setState} city={city} setCity={setCity} /></>}
            {step === 1 && <><span className="section-eyebrow">Professional direction</span><h1>What do you do—and where are you heading?</h1><p>Use any profession or industry. This becomes the context for personalized recommendations.</p><label className="hero-input"><span>Current profession or professional title</span><input autoFocus value={values.professional_title} onChange={(event) => update("professional_title", event.target.value)} placeholder="e.g. Nurse, Accountant, Teacher" /></label><CareerGoalSelector value={values.target_roles} onChange={(roles) => update("target_roles", roles)} suggestions={careerGoalSuggestionsService.getSuggestions(values)} /><span className="mini-label">Career level</span><CareerLevelSelector value={level} onChange={({ name, years }) => { setLevel(name); update("years_of_experience", years); }} /></>}
            {step === 2 && <><span className="section-eyebrow">Education</span><h1>Add your education.</h1><p>Include dates and grade only when they are useful to your story.</p><div className="onboarding-form-grid"><label><span>Institution *</span><input value={education.institution} onChange={(event) => updateEducation("institution", event.target.value)} /></label><label><span>Degree *</span><input value={education.degree} onChange={(event) => updateEducation("degree", event.target.value)} placeholder="e.g. Bachelor’s" /></label><label><span>Field of study *</span><input value={education.field_of_study} onChange={(event) => updateEducation("field_of_study", event.target.value)} /></label><label><span>Grade / GPA</span><input value={education.grade} onChange={(event) => updateEducation("grade", event.target.value)} /></label><label><span>Grade system</span><input value={education.grade_system} onChange={(event) => updateEducation("grade_system", event.target.value)} placeholder="e.g. 4.0, 100%" /></label><label><span>Start date</span><input type="date" value={education.start_date} onChange={(event) => updateEducation("start_date", event.target.value)} /></label><label><span>End date</span><input type="date" value={education.end_date} onChange={(event) => updateEducation("end_date", event.target.value)} /></label></div></>}
            {step === 3 && <><span className="section-eyebrow">Skills</span><h1>What strengths do you bring?</h1><p>Search or add any skill. You can edit or remove each one before continuing.</p><form className="onboarding-skill-add" onSubmit={(event) => { event.preventDefault(); addSkill(); }}><input autoFocus value={skillInput} onChange={(event) => setSkillInput(event.target.value)} placeholder="Add a skill" /><button className="button secondary"><Plus size={16} /> Add</button></form><div className="onboarding-skill-list">{skills.map((skill, index) => <label key={skill.id || index}><Wrench size={15} /><input aria-label={`Edit ${skill.name}`} value={skill.name} onChange={(event) => setSkills((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, name: event.target.value } : item))} /><button type="button" aria-label={`Remove ${skill.name}`} onClick={() => removeSkill(index)}><Trash2 size={15} /></button></label>)}</div></>}
            {step === 4 && <><span className="section-eyebrow">Experience & projects</span><h1>Add experience when you have it.</h1><p>Students and career starters can continue without experience and add projects later.</p><label className="experience-toggle"><input type="checkbox" checked={hasExperience} onChange={(event) => setHasExperience(event.target.checked)} /><span>I have professional experience to add</span></label>{hasExperience && <div className="onboarding-form-grid"><label><span>Company *</span><input value={experience.company} onChange={(event) => updateExperience("company", event.target.value)} /></label><label><span>Job title *</span><input value={experience.job_title} onChange={(event) => updateExperience("job_title", event.target.value)} /></label><label><span>Start date</span><input type="date" value={experience.start_date} onChange={(event) => updateExperience("start_date", event.target.value)} /></label><label><span>End date</span><input type="date" value={experience.end_date} onChange={(event) => updateExperience("end_date", event.target.value)} /></label><label className="span-2"><span>What did you do?</span><textarea value={experience.description} onChange={(event) => updateExperience("description", event.target.value)} rows="4" /></label></div>}</>}
            {step === 5 && <><span className="section-eyebrow">Work preferences</span><h1>Where—and how—do you want to work?</h1><p>Add preferred locations and choose every workplace mode that fits.</p><div className="preference-location"><LocationCombobox country={prefCountry} setCountry={setPrefCountry} state={prefState} setState={setPrefState} city={prefCity} setCity={setPrefCity} /><button type="button" className="button secondary" onClick={addLocation}>Add location</button></div>{values.preferred_locations.length > 0 && <div className="location-selections">{values.preferred_locations.map((item) => <span key={item}><MapPin size={14} />{item}<button type="button" onClick={() => update("preferred_locations", values.preferred_locations.filter((value) => value !== item))}>×</button></span>)}</div>}<span className="mini-label">Workplace preference</span><WorkModeSelector value={values.preferred_work_modes} onChange={(modes) => update("preferred_work_modes", modes)} /></>}
            {step === 6 && <><span className="section-eyebrow">Review & continue</span><h1>Your Career Profile is ready.</h1><p>These details are stored in the canonical profile used across CareerPilot.</p><div className="launch-summary"><article><span>Profession</span><strong>{values.professional_title}</strong><small>{level}</small></article><article><span>Direction</span><strong>{values.target_roles.length} preferred role(s)</strong><small>{values.target_roles.slice(0, 2).join(" · ")}</small></article><article><span>Education</span><strong>{education.degree}</strong><small>{education.institution}</small></article><article><span>Skills</span><strong>{skills.length} skill(s)</strong><small>{skills.slice(0, 4).map((skill) => skill.name).join(" · ")}</small></article><article><span>Experience</span><strong>{hasExperience ? experience.job_title : "Add later"}</strong><small>{hasExperience ? experience.company : "Projects and experience remain editable"}</small></article><article><span>Preferences</span><strong>{values.preferred_work_modes.join(" · ") || "Flexible"}</strong><small>{values.preferred_locations.join(" · ") || locationLabel}</small></article></div></>}
            {error && <p className="form-error" role="alert">{error}</p>}
          </div>
          <footer><button type="button" className="button secondary" disabled={step === 0 || saving} onClick={() => moveToStep(step - 1)}><ArrowLeft size={16} /> Back</button><div>{step === 4 && !hasExperience && <span className="optional-note">Experience is optional</span>}<button type="button" className="button primary" disabled={saving} onClick={() => step === steps.length - 1 ? finish() : moveToStep(step + 1)}>{saving ? <LoaderCircle className="spin" size={16} /> : step === steps.length - 1 ? <Rocket size={16} /> : null}{step === steps.length - 1 ? "Continue to CareerPilot" : "Save & continue"}<ArrowRight size={16} /></button></div></footer>
        </section>
      </section>
    </main>
  );
}
