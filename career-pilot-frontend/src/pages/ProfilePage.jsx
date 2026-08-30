import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { BriefcaseBusiness, Check, CircleUserRound, FolderKanban, GraduationCap, LoaderCircle, Mail, MapPin, Pencil, Plus, Save, Trash2, Wrench, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useParams } from "react-router-dom";
import { z } from "zod";
import AsyncState from "../components/common/AsyncState";
import SectionHeading from "../components/common/SectionHeading";
import { useCareerData, useChildMutation, useProfileMutation } from "../hooks/useCareerData";
import { apiErrorMessage, careerApi } from "../services/careerApi";
import useAppStore from "../store/useAppStore";

const onboardingSchema = z.object({ email: z.string().email("Enter a valid email address"), first_name: z.string().min(1, "First name is required"), last_name: z.string().min(1, "Last name is required") });
const profileSchema = z.object({ professional_title: z.string().min(2, "Add a professional title"), professional_summary: z.string().max(1500).optional(), phone: z.string().optional(), city: z.string().optional(), country: z.string().optional(), linkedin_url: z.union([z.literal(""), z.string().url("Enter a complete URL")]).optional(), github_url: z.union([z.literal(""), z.string().url("Enter a complete URL")]).optional(), portfolio_url: z.union([z.literal(""), z.string().url("Enter a complete URL")]).optional(), years_of_experience: z.coerce.number().min(0) });

const resources = {
  education: { title: "Education", singular: "education", icon: GraduationCap, list: "education", api: "education", empty: "Add your academic background to strengthen the context behind your expertise.", fields: [["institution", "Institution", "text", true], ["degree", "Degree"], ["field_of_study", "Field of study"], ["start_date", "Start date", "date"], ["end_date", "End date", "date"], ["grade", "Grade"]] },
  experience: { title: "Experience", singular: "experience", icon: BriefcaseBusiness, list: "experiences", api: "experiences", empty: "Show the work that shaped your professional strengths and measurable impact.", fields: [["company", "Company", "text", true], ["job_title", "Job title", "text", true], ["employment_type", "Employment type"], ["location", "Location"], ["start_date", "Start date", "date"], ["end_date", "End date", "date"], ["description", "Description", "textarea"]] },
  projects: { title: "Projects", singular: "project", icon: FolderKanban, list: "projects", api: "projects", empty: "Add the projects that best demonstrate how you think, build, and deliver.", fields: [["name", "Project name", "text", true], ["role", "Your role"], ["project_url", "Project URL", "url"], ["repository_url", "Repository URL", "url"], ["start_date", "Start date", "date"], ["end_date", "End date", "date"], ["description", "Description", "textarea"]] },
  skills: { title: "Skills", singular: "skill", icon: Wrench, list: "skills", api: "skills", empty: "Add focused skills to improve matching and make your professional signal clearer.", fields: [["name", "Skill name", "text", true], ["category", "Category"], ["proficiency_level", "Proficiency level"], ["years_of_experience", "Years of experience", "number"]] },
};

function Field({ field, register, errors }) {
  const [name, label, type = "text", required] = field;
  return <label className={type === "textarea" ? "span-2" : ""}><span>{label}{required && <em>*</em>}</span>{type === "textarea" ? <textarea rows="4" {...register(name, { required })} /> : <input type={type} {...register(name, { required, valueAsNumber: type === "number" })} />} {errors[name] && <small className="field-error">{errors[name].message || `${label} is required`}</small>}</label>;
}

function Onboarding() {
  const setUserId = useAppStore((state) => state.setUserId);
  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(onboardingSchema) });
  const mutation = useMutation({ mutationFn: careerApi.createUser, onSuccess: (user) => setUserId(user.id) });
  return <main className="page profile-page"><section className="onboarding"><div className="onboarding-copy"><span className="section-eyebrow">Your career foundation</span><h1>Let’s build a profile that works as hard as you do.</h1><p>Start with the essentials. You can refine every detail as your career evolves.</p><div className="onboarding-points"><span><Check size={15}/> One profile across every career tool</span><span><Check size={15}/> Private, structured professional history</span><span><Check size={15}/> Better context for future AI guidance</span></div></div><form className="onboarding-form" onSubmit={handleSubmit((values) => mutation.mutate(values))}><div className="form-mark"><CircleUserRound size={24}/></div><h2>Create your workspace</h2><p>No account password is required in this foundation phase.</p><div className="form-grid"><label><span>First name</span><input autoFocus {...register("first_name")}/>{errors.first_name && <small className="field-error">{errors.first_name.message}</small>}</label><label><span>Last name</span><input {...register("last_name")}/>{errors.last_name && <small className="field-error">{errors.last_name.message}</small>}</label><label className="span-2"><span>Email address</span><input type="email" {...register("email")}/>{errors.email && <small className="field-error">{errors.email.message}</small>}</label></div>{mutation.error && <p className="form-error">{apiErrorMessage(mutation.error)}</p>}<button className="button primary full" disabled={mutation.isPending}>{mutation.isPending ? <LoaderCircle className="spin" size={17}/> : null} Create career workspace</button></form></section></main>;
}

function ProfileForm({ profile }) {
  const mutation = useProfileMutation();
  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm({ resolver: zodResolver(profileSchema), defaultValues: { years_of_experience: 0 } });
  useEffect(() => { if (profile) reset(profile); }, [profile, reset]);
  const submit = (values) => mutation.mutate({ mode: profile ? "update" : "create", id: profile?.id, payload: Object.fromEntries(Object.entries(values).map(([key, value]) => [key, value === "" ? null : value])) });
  return <section className="profile-section surface" id="personal"><SectionHeading eyebrow="Career identity" title="Personal information" copy="The essentials that introduce you clearly and professionally." action={<button className="button primary" type="submit" form="profile-form" disabled={mutation.isPending || (!isDirty && profile)}><Save size={16}/> Save changes</button>} /><form id="profile-form" className="form-grid" onSubmit={handleSubmit(submit)}><label className="span-2"><span>Professional title<em>*</em></span><input placeholder="e.g. Senior Backend Engineer" {...register("professional_title")}/>{errors.professional_title && <small className="field-error">{errors.professional_title.message}</small>}</label><label><span>Years of experience</span><input type="number" step="0.5" {...register("years_of_experience")}/></label><label><span>Phone</span><input {...register("phone")}/></label><label><span>City</span><input {...register("city")}/></label><label><span>Country</span><input {...register("country")}/></label><label className="span-2"><span>Professional summary</span><textarea rows="5" placeholder="Describe your strengths, scope, and the impact you create." {...register("professional_summary")}/></label><label><span>LinkedIn URL</span><input type="url" {...register("linkedin_url")}/>{errors.linkedin_url && <small className="field-error">{errors.linkedin_url.message}</small>}</label><label><span>GitHub URL</span><input type="url" {...register("github_url")}/>{errors.github_url && <small className="field-error">{errors.github_url.message}</small>}</label></form>{mutation.error && <p className="form-error">{apiErrorMessage(mutation.error)}</p>}</section>;
}

function ResourceModal({ config, profileId, item, onClose }) {
  const mutation = useChildMutation();
  const { register, handleSubmit, formState: { errors } } = useForm({ defaultValues: item || {} });
  const submit = (values) => mutation.mutate({ action: item ? "update" : "create", profileId, resource: config.api, id: item?.id, payload: Object.fromEntries(Object.entries(values).filter(([, value]) => value !== "")) }, { onSuccess: onClose });
  return <div className="modal-backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}><section className="modal"><header><div><span className="section-eyebrow">Career profile</span><h2>{item ? "Edit" : "Add"} {config.singular}</h2></div><button className="icon-button" onClick={onClose}><X size={20}/></button></header><form onSubmit={handleSubmit(submit)}><div className="form-grid">{config.fields.map((field) => <Field key={field[0]} field={field} register={register} errors={errors}/>)}</div>{mutation.error && <p className="form-error">{apiErrorMessage(mutation.error)}</p>}<footer><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={mutation.isPending}>{mutation.isPending && <LoaderCircle className="spin" size={16}/>} Save {config.singular}</button></footer></form></section></div>;
}

function ResourceSection({ config, profile }) {
  const [editing, setEditing] = useState(undefined);
  const mutation = useChildMutation();
  const items = profile?.[config.list] || [];
  const Icon = config.icon;
  return <section className="profile-section surface" id={config.list}><SectionHeading eyebrow="Career evidence" title={config.title} copy={`Keep your ${config.title.toLowerCase()} clear, current, and useful.`} action={<button className="button secondary" onClick={() => setEditing(null)} disabled={!profile}><Plus size={16}/> Add {config.singular}</button>} />{items.length ? <div className={`resource-list ${config.list === "skills" ? "skills-list" : ""}`}>{items.map((item) => <article key={item.id}><span className="resource-icon"><Icon size={18}/></span><div><h3>{item.institution || item.company || item.name}</h3><p>{item.degree || item.job_title || item.role || item.category || "Career profile entry"}</p>{item.description && <small>{item.description}</small>}</div><div className="resource-actions"><button className="icon-button quiet" onClick={() => setEditing(item)}><Pencil size={16}/></button><button className="icon-button quiet danger" onClick={() => window.confirm(`Delete this ${config.singular}?`) && mutation.mutate({ action: "delete", resource: config.api, id: item.id })}><Trash2 size={16}/></button></div></article>)}</div> : <div className="empty-state"><span><Icon size={23}/></span><h3>No {config.title.toLowerCase()} added yet</h3><p>{config.empty}</p><button className="button secondary" onClick={() => setEditing(null)} disabled={!profile}><Plus size={16}/> Add {config.singular}</button></div>}{editing !== undefined && <ResourceModal config={config} profileId={profile.id} item={editing} onClose={() => setEditing(undefined)}/>}</section>;
}

export default function ProfilePage() {
  const { section } = useParams();
  const { userId, user, profile } = useCareerData();
  if (!userId) return <Onboarding />;
  const profileMissing = profile.error?.response?.status === 404;
  const visible = section && resources[section] ? [section] : Object.keys(resources);
  return <main className="page profile-page"><section className="profile-hero"><div className="profile-avatar">{user.data ? `${user.data.first_name[0]}${user.data.last_name[0]}` : "CP"}<span/></div><div><span className="hero-kicker">Career profile</span><h1>{user.data ? `${user.data.first_name} ${user.data.last_name}` : "Your professional story"}</h1><p><Mail size={14}/> {user.data?.email || "Loading profile…"}{profile.data?.city && <><i/><MapPin size={14}/>{profile.data.city}</>}</p></div><div className="profile-status"><span>Profile visibility</span><strong><i/> Ready to build</strong></div></section><AsyncState loading={user.isLoading || profile.isLoading} error={user.error}><div className="profile-content"><aside className="profile-index"><span>Profile sections</span><a href="#personal">Personal information</a>{Object.values(resources).map((config) => <a key={config.list} href={`#${config.list}`}>{config.title}</a>)}</aside><div className="profile-sections"><ProfileForm profile={profileMissing ? null : profile.data}/>{visible.map((key) => <ResourceSection key={key} config={resources[key]} profile={profile.data}/>)}</div></div></AsyncState></main>;
}
