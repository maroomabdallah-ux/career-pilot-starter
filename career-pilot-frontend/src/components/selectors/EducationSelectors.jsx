import { useEffect, useState } from "react";
import apiClient from "../../services/apiClient";
import {
  degrees,
  fieldsOfStudy,
  gradeSystems,
} from "../../data/careerTaxonomies";
import PremiumCombobox from "./PremiumCombobox";

export function UniversityCombobox({ value, onChange, country }) {
  const [query, setQuery] = useState("");
  const [options, setOptions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (query.trim().length < 2) {
      setOptions([]);
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setLoading(true);
      setError("");
      apiClient
        .get("/reference/universities", {
          params: { q: query.trim(), country: country || undefined },
          signal: controller.signal,
        })
        .then((r) => setOptions(r.data))
        .catch((error) => {
          if (error.code !== "ERR_CANCELED")
            setError(
              "We couldn't load universities right now. Enter yours manually.",
            );
        })
        .finally(() => setLoading(false));
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, country]);
  return (
    <div>
      <PremiumCombobox
        label="Institution"
        value={value}
        onChange={(x) => onChange(typeof x === "string" ? x : x.name)}
        onSearchChange={setQuery}
        options={options}
        loading={loading}
        error={error}
        allowCustom
        placeholder="Search universities worldwide"
        getLabel={(x) =>
          typeof x === "string" ? x : `${x.name} — ${x.country}`
        }
        getKey={(x) => (typeof x === "string" ? x : `${x.name}-${x.country}`)}
      />
      <small className="selector-hint">
        Can't find your university? Type its full name and choose the custom
        entry.
      </small>
    </div>
  );
}

export function DegreeCombobox(props) {
  return (
    <PremiumCombobox
      {...props}
      label="Degree"
      options={degrees}
      allowCustom
      placeholder="Search degrees"
    />
  );
}
export function FieldOfStudyCombobox(props) {
  return (
    <PremiumCombobox
      {...props}
      label="Field of study"
      options={fieldsOfStudy}
      allowCustom
      placeholder="Search global fields"
    />
  );
}

export function GradeSystemSelector({ system, setSystem, grade, setGrade }) {
  const letters = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F"];
  const classes = [
    "First Class",
    "Upper Second / 2:1",
    "Lower Second / 2:2",
    "Third Class",
    "Distinction",
    "Merit",
    "Pass",
  ];
  const options =
    system === "Letter Grade"
      ? letters
      : system === "Academic Classification"
        ? classes
        : null;
  const max = system?.includes("4.0")
    ? 4
    : system?.includes("5.0")
      ? 5
      : system?.includes("10.0")
        ? 10
        : system?.includes("100")
          ? 100
          : null;
  const changeSystem = (next) => {
    if (next !== system) setGrade("");
    setSystem(next);
  };
  return (
    <div className="grade-fields">
      <PremiumCombobox
        label="Grade system"
        value={system}
        onChange={changeSystem}
        options={gradeSystems}
        allowCustom
        placeholder="Choose a grading system"
      />
      {options ? (
        <PremiumCombobox
          label="Grade"
          value={grade}
          onChange={setGrade}
          options={options}
          placeholder="Select grade"
        />
      ) : (
        <label className="combo-field">
          <span>Grade value</span>
          <input
            value={grade || ""}
            onChange={(e) => setGrade(e.target.value)}
            type={max ? "number" : "text"}
            min="0"
            max={max || undefined}
            step="0.01"
            placeholder={max ? `0 – ${max}` : "Enter grade"}
          />
        </label>
      )}
    </div>
  );
}
