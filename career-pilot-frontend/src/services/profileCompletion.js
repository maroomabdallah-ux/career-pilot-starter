export const profileCompletionConfig = {
  personal: 15,
  goals: 10,
  education: 15,
  experience: 25,
  projects: 15,
  skills: 20,
};

const completeEducation = (x) =>
  x?.institution && x?.degree && x?.field_of_study && x?.start_date;
const completeExperience = (x) => x?.company && x?.job_title && x?.start_date;
const completeProject = (x) => x?.name && x?.description;

export function calculateProfileCompletion(profile) {
  const p = profile || {};
  const categories = {
    personal: Boolean(p.professional_title && p.city && p.country),
    goals: Boolean(p.target_roles?.length && p.preferred_work_modes?.length),
    education: Boolean(p.education?.some(completeEducation)),
    experience: Boolean(p.experiences?.some(completeExperience)),
    projects: Boolean(p.projects?.some(completeProject)),
    skills: (p.skills?.length || 0) >= 3,
  };
  const score = Object.entries(categories).reduce(
    (total, [key, done]) => total + (done ? profileCompletionConfig[key] : 0),
    0,
  );
  const actions = [
    [!categories.personal, "Complete your professional basics", "/app/profile"],
    [
      !categories.goals,
      "Add your career goals and work preferences",
      "/app/profile/direction",
    ],
    [
      !categories.education,
      "Complete your education details",
      "/app/profile/education",
    ],
    [
      !categories.experience,
      "Add your latest professional experience",
      "/app/profile/experience",
    ],
    [
      !categories.projects,
      "Showcase your strongest project",
      "/app/profile/projects",
    ],
    [
      !categories.skills,
      `Add ${Math.max(1, 3 - (p.skills?.length || 0))} more core skills`,
      "/app/profile/skills",
    ],
  ];
  const next = actions.find(([needed]) => needed) || [
    false,
    "Let's build your resume",
    "/app/resume",
  ];
  return { score, categories, nextAction: { label: next[1], to: next[2] } };
}
