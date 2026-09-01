import {
  ArrowLeft,
  ArrowRight,
  Check,
  Compass,
  LoaderCircle,
  MapPin,
  Rocket,
  Sparkles,
  UserRound,
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

const steps = [
  "Identity",
  "Location",
  "Goals",
  "Preferences",
  "Career level",
  "Launch",
];
const icons = [UserRound, MapPin, Compass, Sparkles, Rocket, Check];
const draftKey = "careerpilot-onboarding-draft";
const emptyDraft = {
  step: 0,
  values: {
    professional_title: "",
    target_roles: [],
    preferred_locations: [],
    preferred_work_modes: [],
    years_of_experience: 0,
  },
  country: null,
  state: null,
  city: null,
  level: "",
};
function readDraft() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(draftKey) || "{}");
    return {
      ...emptyDraft,
      ...saved,
      step: Number.isInteger(saved.step) && saved.step >= 0 && saved.step < steps.length ? saved.step : 0,
      values: { ...emptyDraft.values, ...(saved.values || {}) },
    };
  } catch {
    return emptyDraft;
  }
}

export default function OnboardingPage() {
  const draft = useState(readDraft)[0];
  const user = useAuthStore((s) => s.user);
  const setUser = useAuthStore((s) => s.setUser);
  const [step, setStep] = useState(draft.step);
  const [values, setValues] = useState(draft.values);
  const [country, setCountry] = useState(draft.country);
  const [state, setState] = useState(draft.state);
  const [city, setCity] = useState(draft.city);
  const [prefCountry, setPrefCountry] = useState(null);
  const [prefState, setPrefState] = useState(null);
  const [prefCity, setPrefCity] = useState(null);
  const [level, setLevel] = useState(draft.level);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  useEffect(() => {
    sessionStorage.setItem(
      draftKey,
      JSON.stringify({ step, values, country, state, city, level }),
    );
  }, [step, values, country, state, city, level]);
  if (user?.onboarding_completed)
    return <Navigate to="/app/dashboard" replace />;
  const update = (key, value) => setValues((v) => ({ ...v, [key]: value }));
  const addLocation = () => {
    if (!prefCountry) return;
    const cityName = typeof prefCity === "string" ? prefCity : prefCity?.name;
    const countryName =
      typeof prefCountry === "string" ? prefCountry : prefCountry.name;
    const label = cityName ? `${cityName}, ${countryName}` : countryName;
    if (!values.preferred_locations.includes(label))
      update("preferred_locations", [...values.preferred_locations, label]);
    setPrefCity(null);
  };
  const finish = async () => {
    setSaving(true);
    setError("");
    const payload = {
      ...values,
      country: (typeof country === "string" ? country : country?.name) || null,
      city: (typeof city === "string" ? city : city?.name) || null,
    };
    try {
      try {
        await careerApi.getProfile();
        await careerApi.updateProfile(payload);
      } catch (e) {
        if (e.response?.status === 404) await careerApi.createProfile(payload);
        else throw e;
      }
      const updated = await careerApi.completeOnboarding();
      sessionStorage.removeItem(draftKey);
      setUser(updated);
      navigate("/app/dashboard", { replace: true });
    } catch (e) {
      setError(apiErrorMessage(e));
      setSaving(false);
    }
  };
  const Icon = icons[step];
  return (
    <main className="launchpad">
      <section className="launchpad-shell">
        <aside className="launchpad-side">
          <div className="launch-logo" aria-label="CareerPilot">
            <Compass size={24} />
            <strong>CareerPilot</strong>
          </div>
          <div>
            <span className="section-eyebrow">Career Launchpad</span>
            <h2>Shape the foundation for your next move.</h2>
            <p>
              One connected journey. Every answer strengthens the career
              workspace ahead.
            </p>
          </div>
          <JourneyProgress steps={steps} current={step} />
          <small>Private by design · Editable anytime</small>
        </aside>
        <section className="launchpad-main">
          <header>
            <span>
              {String(step + 1).padStart(2, "0")} /{" "}
              {String(steps.length).padStart(2, "0")}
            </span>
            <i>
              <Icon size={20} />
            </i>
          </header>
          <div className="launch-step" key={step}>
            {step === 0 && (
              <>
                <span className="section-eyebrow">Career identity</span>
                <h1>How do you introduce yourself professionally?</h1>
                <p>
                  This anchors your profile and helps CareerPilot organize
                  relevant next steps.
                </p>
                <label className="hero-input">
                  <span>Professional title</span>
                  <input
                    autoFocus
                    value={values.professional_title}
                    onChange={(e) =>
                      update("professional_title", e.target.value)
                    }
                    placeholder="e.g. Backend Developer"
                  />
                </label>
              </>
            )}
            {step === 1 && (
              <>
                <span className="section-eyebrow">Your location</span>
                <h1>Where are you building your career?</h1>
                <p>
                  Select a country first, then refine your city. You can always
                  adjust this later.
                </p>
                <LocationCombobox
                  country={country}
                  setCountry={setCountry}
                  state={state}
                  setState={setState}
                  city={city}
                  setCity={setCity}
                />
              </>
            )}
            {step === 2 && (
              <>
                <span className="section-eyebrow">Career direction</span>
                <h1>What roles are you moving toward?</h1>
                <p>
                  Choose from a global role taxonomy or add your own direction.
                </p>
                <CareerGoalSelector
                  value={values.target_roles}
                  onChange={(x) => update("target_roles", x)}
                  suggestions={careerGoalSuggestionsService.getSuggestions(
                    values,
                  )}
                />
              </>
            )}
            {step === 3 && (
              <>
                <span className="section-eyebrow">Work preferences</span>
                <h1>Where—and how—do you want to work?</h1>
                <p>
                  Add multiple preferred locations, then choose every work mode
                  that fits.
                </p>
                <div className="preference-location">
                  <LocationCombobox
                    country={prefCountry}
                    setCountry={setPrefCountry}
                    state={prefState}
                    setState={setPrefState}
                    city={prefCity}
                    setCity={setPrefCity}
                  />
                  <button
                    type="button"
                    className="button secondary"
                    onClick={addLocation}
                  >
                    Add location
                  </button>
                </div>
                {values.preferred_locations.length > 0 && (
                  <div className="location-selections">
                    {values.preferred_locations.map((x) => (
                      <span key={x}>
                        <MapPin size={14} />
                        {x}
                        <button
                          type="button"
                          onClick={() =>
                            update(
                              "preferred_locations",
                              values.preferred_locations.filter((v) => v !== x),
                            )
                          }
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
                <span className="mini-label">Work mode</span>
                <WorkModeSelector
                  value={values.preferred_work_modes}
                  onChange={(x) => update("preferred_work_modes", x)}
                />
              </>
            )}
            {step === 4 && (
              <>
                <span className="section-eyebrow">Career level</span>
                <h1>Choose the context that fits you today.</h1>
                <p>Experience ranges are guidance—not rigid labels.</p>
                <CareerLevelSelector
                  value={level}
                  onChange={({ name, years }) => {
                    setLevel(name);
                    update("years_of_experience", years);
                  }}
                />
              </>
            )}
            {step === 5 && (
              <>
                <span className="section-eyebrow">Review & launch</span>
                <h1>Your CareerPilot foundation is ready.</h1>
                <p>
                  Review the direction below. Every detail remains editable in
                  your profile workspace.
                </p>
                <div className="launch-summary">
                  <article>
                    <span>Identity</span>
                    <strong>{values.professional_title || "Add later"}</strong>
                    <small>
                      {[
                        typeof city === "string" ? city : city?.name,
                        typeof country === "string" ? country : country?.name,
                      ]
                        .filter(Boolean)
                        .join(", ") || "Location open"}
                    </small>
                  </article>
                  <article>
                    <span>Target roles</span>
                    <strong>{values.target_roles.length || 0} selected</strong>
                    <small>
                      {values.target_roles.slice(0, 2).join(" · ") ||
                        "Add later"}
                    </small>
                  </article>
                  <article>
                    <span>Work preferences</span>
                    <strong>
                      {values.preferred_work_modes.join(" · ") || "Flexible"}
                    </strong>
                    <small>
                      {values.preferred_locations.length} preferred locations
                    </small>
                  </article>
                  <article>
                    <span>Career level</span>
                    <strong>{level || "Not specified"}</strong>
                    <small>Used as flexible context</small>
                  </article>
                </div>
              </>
            )}
            {error && <p className="form-error">{error}</p>}
          </div>
          <footer>
            <button
              type="button"
              className="button secondary"
              disabled={step === 0 || saving}
              onClick={() => setStep(step - 1)}
            >
              <ArrowLeft size={16} /> Back
            </button>
            <div>
              <button
                className="text-button"
                type="button"
                onClick={() => (step < 5 ? setStep(step + 1) : finish())}
              >
                Skip optional
              </button>
              <button
                type="button"
                className="button primary"
                disabled={saving}
                onClick={() => (step === 5 ? finish() : setStep(step + 1))}
              >
                {saving ? (
                  <LoaderCircle className="spin" size={16} />
                ) : step === 5 ? (
                  <Rocket size={16} />
                ) : null}
                {step === 5 ? "Launch CareerPilot" : "Continue"}
                <ArrowRight size={16} />
              </button>
            </div>
          </footer>
        </section>
      </section>
    </main>
  );
}
