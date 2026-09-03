import { Check, LockKeyhole } from "lucide-react";
import { resumeTemplates } from "./templates/registry";

export default function TemplateSelector({ value, onChange, disabled }) {
  return <div className="template-selector">{Object.values(resumeTemplates).map((template) => <button type="button" key={template.id} disabled={disabled} className={`template-card ${value === template.id ? "selected" : ""}`} onClick={() => onChange(template.id)}><span className={`template-mini mini-${template.id}`}><i/><i/><i/><i/></span><span><strong>{template.name}</strong><small>{template.tier === "premium" && <LockKeyhole size={10}/>} {template.tier}</small></span>{value === template.id && <Check size={15}/>}</button>)}</div>;
}
