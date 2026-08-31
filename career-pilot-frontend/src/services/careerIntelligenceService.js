import { careerRoles } from "../data/careerTaxonomies";

const related = {
  backend: ["Backend Developer","Software Engineer","Cloud Engineer","DevOps Engineer"],
  data: ["Data Analyst","Data Engineer","Data Scientist","Business Intelligence Analyst"],
  design: ["Product Designer","UX Designer","UI Designer","Product Manager"],
  marketing: ["Marketing Manager","Digital Marketing Specialist","Content Strategist"],
  finance: ["Financial Analyst","Accountant","Investment Analyst","Business Analyst"],
};

export const careerGoalSuggestionsService = {
  getSuggestions(profile = {}) {
    const context = `${profile.professional_title || ""} ${profile.professional_summary || ""}`.toLowerCase();
    const match = Object.entries(related).find(([key]) => context.includes(key));
    return [...new Set([...(match?.[1] || []), ...careerRoles])].slice(0, 8);
  },
};
